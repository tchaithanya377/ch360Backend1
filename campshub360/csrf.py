from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.utils.cache import add_never_cache_headers
import logging

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=None):
    """Custom CSRF failure handler that logs details and avoids generic 500s."""
    logger.warning(
        "CSRF failure",
        extra={
            'path': request.path,
            'method': request.method,
            'reason': reason,
            'origin': request.headers.get('Origin'),
            'referer': request.headers.get('Referer'),
            'host': request.get_host(),
            'cookies': list(request.COOKIES.keys()),
            'user_agent': request.headers.get('User-Agent', '')[:100],
        }
    )

    # Return JSON for API/AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('Accept', '').find('application/json') != -1:
        return JsonResponse({
            'success': False,
            'error': 'CSRF Failed',
            'reason': reason or 'Invalid or missing CSRF token',
            'csrf_token': get_token(request),  # Provide new token
        }, status=403)

    # For admin forms, provide a more helpful response
    if '/admin/' in request.path:
        response = HttpResponseBadRequest(
            "CSRF verification failed. Please refresh the page and try again. "
            "If the problem persists, try clearing your browser cookies and logging in again."
        )
        add_never_cache_headers(response)
        return response

    # Fallback simple 400/403 response for browser form posts
    return HttpResponseBadRequest("CSRF verification failed. Please refresh the page and try again.")


class CSRFEnsureTokenMiddleware(MiddlewareMixin):
    """
    Middleware to ensure CSRF token is available for admin forms.
    This helps prevent CSRF failures in Django admin.
    """
    
    def process_request(self, request):
        # Ensure CSRF token is set for admin pages
        if '/admin/' in request.path and request.method in ['GET', 'POST']:
            # Force token generation if not present
            if 'csrftoken' not in request.COOKIES:
                get_token(request)
        return None


