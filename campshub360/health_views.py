"""
Health check views for the CampsHub360 application.
These views provide endpoints for monitoring application health, readiness, and liveness.
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import logging
from .metrics import collect_app_metrics

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    """
    return JsonResponse({
        'status': 'healthy',
        'message': 'CampsHub360 is running',
        'version': '1.0.0'
    })


def detailed_health_check(request):
    """
    Detailed health check endpoint.
    Checks database connectivity, cache, and other critical services.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': None,
        'services': {}
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['services']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        health_status['status'] = 'unhealthy'
    
    # Check cache connectivity
    try:
        cache.set('health_check', 'test', 10)
        cache.get('health_check')
        health_status['services']['cache'] = {
            'status': 'healthy',
            'message': 'Cache connection successful'
        }
    except Exception as e:
        health_status['services']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache connection failed: {str(e)}'
        }
        health_status['status'] = 'unhealthy'
    
    # Check static files
    try:
        import os
        static_root = settings.STATIC_ROOT
        if os.path.exists(static_root):
            health_status['services']['static_files'] = {
                'status': 'healthy',
                'message': 'Static files directory accessible'
            }
        else:
            health_status['services']['static_files'] = {
                'status': 'warning',
                'message': 'Static files directory not found'
            }
    except Exception as e:
        health_status['services']['static_files'] = {
            'status': 'unhealthy',
            'message': f'Static files check failed: {str(e)}'
        }
    
    # Check media files
    try:
        import os
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            health_status['services']['media_files'] = {
                'status': 'healthy',
                'message': 'Media files directory accessible'
            }
        else:
            health_status['services']['media_files'] = {
                'status': 'warning',
                'message': 'Media files directory not found'
            }
    except Exception as e:
        health_status['services']['media_files'] = {
            'status': 'unhealthy',
            'message': f'Media files check failed: {str(e)}'
        }
    
    # Add timestamp
    from django.utils import timezone
    health_status['timestamp'] = timezone.now().isoformat()
    
    # Return appropriate HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def readiness_check(request):
    """
    Readiness check endpoint.
    Indicates if the application is ready to receive traffic.
    """
    try:
        # Check if database is accessible
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check if cache is accessible
        cache.set('readiness_check', 'test', 10)
        cache.get('readiness_check')
        
        return JsonResponse({
            'status': 'ready',
            'message': 'Application is ready to receive traffic'
        })
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JsonResponse({
            'status': 'not_ready',
            'message': f'Application is not ready: {str(e)}'
        }, status=503)


def liveness_check(request):
    """
    Liveness check endpoint.
    Indicates if the application is alive and running.
    """
    return JsonResponse({
        'status': 'alive',
        'message': 'Application is alive and running'
    })


def app_metrics(request):
    """Lightweight JSON metrics for RPS and latency percentiles."""
    data = collect_app_metrics()
    return JsonResponse(data)
