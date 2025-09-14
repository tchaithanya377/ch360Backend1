from __future__ import annotations

from django.utils.deprecation import MiddlewareMixin
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import AuditLog, UserSession
from accounts.utils import extract_client_ip, geolocate_ip


User = get_user_model()


SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}


class AuditLogMiddleware(MiddlewareMixin):
    """Middleware to record audit logs for mutating requests and enrich session geo info.

    - Logs: user, action (method + path), object_type (app_label), ip, ua, meta (status, query params)
    - Enriches latest UserSession (if any) with geolocation on first hit from that IP.
    """

    def process_request(self, request):
        # Assign a request ID for correlation
        request.request_id = str(uuid.uuid4())
        return None

    def process_response(self, request, response):
        try:
            user = getattr(request, 'user', None)
            ip = extract_client_ip(request)
            ua = request.META.get('HTTP_USER_AGENT', '')
            # Add request ID to response for client correlation
            if hasattr(request, 'request_id'):
                response['X-Request-ID'] = request.request_id

            # Mutations only for audit record
            if request.method not in SAFE_METHODS:
                AuditLog.objects.create(
                    user=user if getattr(user, 'is_authenticated', False) else None,
                    action=f"{request.method} {request.path}",
                    object_type=request.resolver_match.app_name if getattr(request, 'resolver_match', None) else '',
                    object_id=None,
                    ip=ip,
                    user_agent=ua,
                    meta={
                        'status_code': response.status_code,
                        'GET': request.GET.dict(),
                        'request_id': getattr(request, 'request_id', ''),
                    },
                )

            # Enrich geo on session once
            if getattr(user, 'is_authenticated', False) and ip:
                try:
                    latest = UserSession.objects.filter(user=user, ip=ip).order_by('-created_at').first()
                    if latest and not getattr(latest, 'country', None):
                        raw, country, region, city, lat, lon = geolocate_ip(ip)
                        if hasattr(latest, 'country'):
                            latest.country = country
                        if hasattr(latest, 'region'):
                            latest.region = region
                        if hasattr(latest, 'city'):
                            latest.city = city
                        if hasattr(latest, 'latitude'):
                            latest.latitude = lat
                        if hasattr(latest, 'longitude'):
                            latest.longitude = lon
                        if raw and hasattr(latest, 'location_raw'):
                            latest.location_raw = raw
                        try:
                            latest.save(update_fields=['country', 'region', 'city', 'latitude', 'longitude', 'location_raw'])
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            # Never block request due to audit errors
            pass
        return response


