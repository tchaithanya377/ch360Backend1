"""
URL configuration for campshub360 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import RateLimitedTokenView, RateLimitedRefreshView
from .health_views import health_check, detailed_health_check, readiness_check, liveness_check, app_metrics
# drf-spectacular imports removed

urlpatterns = [
    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('health/detailed/', detailed_health_check, name='detailed_health_check'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/alive/', liveness_check, name='liveness_check'),
    path('metrics/app', app_metrics, name='app_metrics'),
    
    path('admin/', admin.site.urls),
    # Standardized JWT endpoints (rate limited)
    path('api/auth/token/', RateLimitedTokenView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', RateLimitedRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/v1/students/', include('students.api_urls')),
    path('api/v1/faculty/', include('faculty.urls', namespace='faculty')),
    path('api/v1/academics/', include('academics.urls', namespace='academics')),
    path('api/v1/departments/', include('departments.urls', namespace='departments')),
    path('api/v1/attendance/', include('attendance.urls')),
    path('api/v1/placements/', include('placements.urls', namespace='placements')),
    path('api/v1/grads/', include('grads.urls', namespace='grads')),
    path('api/v1/rnd/', include('rnd.urls', namespace='rnd')),
    path('api/v1/facilities/', include('facilities.urls', namespace='facilities')),
    path('api/v1/exams/', include('exams.urls', namespace='exams')),
    path('api/v1/fees/', include('fees.urls', namespace='fees')),
    path('api/v1/transport/', include('transportation.urls', namespace='transportation')),
    path('api/v1/mentoring/', include('mentoring.urls', namespace='mentoring')),
    path('api/v1/feedback/', include('feedback.urls', namespace='feedback')),
    path('api/v1/assignments/', include('assignments.urls', namespace='assignments')),
    # Prometheus metrics (conditionally added below if installed)
    # Docs and API schema routes removed
    path('facilities/', include('facilities.urls', namespace='facilities_dashboard')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('students/', include('students.urls', namespace='students')),
    path('', RedirectView.as_view(pattern_name='dashboard:login', permanent=False)),
]

# Conditionally add Prometheus metrics if app is installed
try:
    import django_prometheus  # noqa: F401
    urlpatterns = [path('', include('django_prometheus.urls'))] + urlpatterns
except Exception:
    pass

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
