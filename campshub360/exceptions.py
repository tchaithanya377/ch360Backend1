import logging
from typing import Optional

from django.http import HttpRequest
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from accounts.utils import RateLimitExceeded


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context) -> Optional[Response]:
    """Wrap DRF's default handler to add structured logging and a safe fallback.

    Ensures 500s are logged with request context and returns a stable JSON shape.
    """
    # Custom: rate-limit to 429
    if isinstance(exc, RateLimitExceeded):
        return Response({'detail': 'Too Many Requests'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    response = drf_exception_handler(exc, context)

    request: Optional[HttpRequest] = context.get('request')
    path = getattr(request, 'path', None)
    method = getattr(request, 'method', None)
    user = getattr(getattr(request, 'user', None), 'id', None)

    if response is not None:
        # Log 4xx/5xx handled by DRF
        if response.status_code >= 400:
            logger.warning(
                'DRF error %s at %s %s',
                response.status_code,
                method,
                path,
                extra={
                    'status_code': response.status_code,
                    'path': path,
                    'method': method,
                    'user_id': user,
                    'detail': getattr(response, 'data', None),
                },
            )
        return response

    # Unhandled exception: log and return generic JSON 500
    logger.exception(
        'Unhandled exception at %s %s',
        method,
        path,
        extra={
            'path': path,
            'method': method,
            'user_id': user,
        },
    )

    return Response(
        {
            'success': False,
            'error': 'Internal Server Error',
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


