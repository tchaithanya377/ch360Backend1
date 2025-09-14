from rest_framework import generics, permissions, status, exceptions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import AuthIdentifier, IdentifierType
from .models import UserSession
from django.contrib.auth.models import Group
from django.core.cache import cache
try:
    from ratelimit.decorators import ratelimit
except Exception:  # Fallback if ratelimit isn't installed in the running env
    def ratelimit(*args, **kwargs):
        def _decorator(view):
            return view
        return _decorator
from django.utils.decorators import method_decorator
from django.conf import settings
from students.signals import record_session
from accounts.utils import extract_client_ip, geolocate_ip

from .serializers import RegisterSerializer, UserSerializer
from .permissions import HasRole, HasAnyPermission


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class RollOrEmailTokenSerializer(TokenObtainPairSerializer):
    """Custom token serializer accepting roll number or email as username field."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the username field to accept both username and email
        self.fields['username'] = serializers.CharField(required=False)
        self.fields['email'] = serializers.EmailField(required=False)

    def validate(self, attrs):
        # Accept either username or email field
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None
        # Try by username first, then by email
        if username:
            user = self._get_user_by_identifier(username)
        elif email:
            user = self._get_user_by_identifier(email)

        if user is None:
            raise exceptions.AuthenticationFailed('Invalid credentials', code='authorization')

        if not user.check_password(password):
            raise exceptions.AuthenticationFailed('Invalid credentials', code='authorization')

        # Create a new attrs dict with email field for parent validation
        parent_attrs = {'email': user.email, 'password': password}
        data = super().validate(parent_attrs)

        request = self.context.get('request')
        if request:
            # record base session
            usession = record_session(user, request)
            # enrich with geo info immediately when available (ignore if DB not migrated yet)
            try:
                ip = extract_client_ip(request)
                raw, country, region, city, lat, lon = geolocate_ip(ip)
                if usession and (country or raw):
                    usession.country = country
                    usession.region = region
                    usession.city = city
                    usession.latitude = lat
                    usession.longitude = lon
                    if raw:
                        usession.location_raw = raw
                    usession.save(update_fields=['country','region','city','latitude','longitude','location_raw'])
            except Exception:
                # DB might not have new columns yet; skip enrichment
                pass

            # Attach session/location metadata into token response (non-breaking extra fields)
            try:
                session_payload = {
                    'ip': extract_client_ip(request),
                    'login_at': getattr(usession, 'login_at', None),
                    'country': getattr(usession, 'country', None),
                    'region': getattr(usession, 'region', None),
                    'city': getattr(usession, 'city', None),
                    'latitude': getattr(usession, 'latitude', None),
                    'longitude': getattr(usession, 'longitude', None),
                }
                data['session'] = session_payload
            except Exception:
                pass

        # Also include minimal user info for clients
        try:
            data['user'] = {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
            }
        except Exception:
            pass

        return data

    def _get_user_by_identifier(self, identifier: str):
        # Match by email
        try:
            return User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            pass
        # Match by roll number via AuthIdentifier (stored as USERNAME)
        auth_ids = AuthIdentifier.objects.filter(
            Q(identifier__iexact=identifier),
            Q(id_type=IdentifierType.USERNAME) | Q(id_type=IdentifierType.EMAIL)
        ).select_related('user')
        if auth_ids.exists():
            return auth_ids.first().user
        # As fallback, match username field directly
        try:
            return User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            return None


class RollOrEmailTokenView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = RollOrEmailTokenSerializer


@method_decorator(ratelimit(key='ip', rate=getattr(settings, 'AUTH_RATE_LIMIT_TOKEN', '5/m'), method='POST', block=True), name='post')
class RateLimitedTokenView(RollOrEmailTokenView):
    pass


@method_decorator(ratelimit(key='ip', rate=getattr(settings, 'AUTH_RATE_LIMIT_REFRESH', '10/m'), method='POST', block=True), name='post')
class RateLimitedRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class RolesPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.core.cache import cache
        cache_key = f"rolesperms:v2:{request.user.id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        # Django Groups as roles
        roles = list(request.user.groups.values_list('name', flat=True))
        # Django permissions including group + user perms as app_label.codename
        perms = sorted(list(request.user.get_all_permissions()))
        payload = {'roles': sorted(roles), 'permissions': sorted(perms)}
        # Cache for 1 hour (3600 seconds) for better performance
        cache.set(cache_key, payload, timeout=3600)
        return Response(payload)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = ['Admin']

    def get_queryset(self):
        qs = User.objects.all().order_by('-date_joined')
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(username__icontains=search))
        return qs

    def list(self, request, *args, **kwargs):
        try:
            # Lightweight, serializer-free listing for speed and resiliency
            qs = self.get_queryset().only('id', 'email', 'username', 'is_active', 'is_verified', 'date_joined')
            try:
                limit = int(request.query_params.get('limit', '50'))
                offset = int(request.query_params.get('offset', '0'))
            except ValueError:
                limit, offset = 50, 0
            total = qs.count()
            rows = list(
                qs.values('id', 'email', 'username', 'is_active', 'is_verified', 'date_joined')[offset:offset+limit]
            )
            return Response({'count': total, 'results': rows})
        except Exception as exc:
            return Response({'detail': 'Internal error', 'error': str(exc)}, status=500)


class AssignRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = ['Admin']

    def post(self, request):
        user_id = request.data.get('user_id')
        role_name = request.data.get('role')
        if not user_id or not role_name:
            return Response({'detail': 'user_id and role are required.'}, status=400)
        try:
            target_user = User.objects.get(id=user_id)
            group, _ = Group.objects.get_or_create(name=role_name)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        target_user.groups.add(group)
        # Invalidate cached roles/permissions for the target user
        cache.delete(f"rolesperms:v2:{target_user.id}")
        return Response({'detail': 'Role assigned.'})


class RevokeRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = ['Admin']

    def post(self, request):
        user_id = request.data.get('user_id')
        role_name = request.data.get('role')
        if not user_id or not role_name:
            return Response({'detail': 'user_id and role are required.'}, status=400)
        try:
            target_user = User.objects.get(id=user_id)
            group = Group.objects.get(name=role_name)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)
        except Group.DoesNotExist:
            return Response({'detail': 'Role not found.'}, status=404)
        target_user.groups.remove(group)
        cache.delete(f"rolesperms:v2:{target_user.id}")
        return Response({'detail': 'Role revoked.'})


class RolesCatalogView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasRole]
    required_roles = ['Admin']

    def get(self, request):
        # Expose Django Groups and their assigned permissions (codenames with app label)
        groups = []
        role_perms = {}
        for g in Group.objects.all().order_by('name'):
            groups.append({'id': g.id, 'name': g.name})
            perms = g.permissions.select_related('content_type').all()
            role_perms[g.name] = [f"{p.content_type.app_label}.{p.codename}" for p in perms]
        return Response({'roles': groups, 'role_permissions': role_perms})


class MySessionsView(generics.ListAPIView):
    """Return recent login sessions for the current user, including IP, location, and timestamps."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user).order_by('-login_at')

    def list(self, request, *args, **kwargs):
        # Cache user sessions for 5 minutes
        cache_key = f'user_sessions:v1:{request.user.id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        
        sessions = self.get_queryset()
        data = []
        for s in sessions[:50]:  # cap to reasonable size
            data.append({
                'id': str(s.id),
                'ip': s.ip,
                'device_info': s.device_info,
                'login_at': s.login_at,
                'expires_at': s.expires_at,
                'revoked': s.revoked,
                'revoked_at': s.revoked_at,
                'country': getattr(s, 'country', None),
                'region': getattr(s, 'region', None),
                'city': getattr(s, 'city', None),
                'latitude': getattr(s, 'latitude', None),
                'longitude': getattr(s, 'longitude', None),
            })
        
        response_data = {'count': sessions.count(), 'results': data}
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, response_data, timeout=300)
        return Response(response_data)


class MyActiveSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Cache active session for 2 minutes
        cache_key = f'active_session:v1:{request.user.id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        
        s = UserSession.objects.filter(user=request.user, revoked=False).order_by('-login_at').first()
        if not s:
            return Response({'detail': 'No active session'}, status=404)
        payload = {
            'id': str(s.id),
            'ip': s.ip,
            'device_info': s.device_info,
            'login_at': s.login_at,
            'expires_at': s.expires_at,
            'revoked': s.revoked,
            'country': getattr(s, 'country', None),
            'region': getattr(s, 'region', None),
            'city': getattr(s, 'city', None),
            'latitude': getattr(s, 'latitude', None),
            'longitude': getattr(s, 'longitude', None),
        }
        # Cache for 2 minutes (120 seconds)
        cache.set(cache_key, payload, timeout=120)
        return Response(payload)
