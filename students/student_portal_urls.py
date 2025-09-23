from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .student_portal_views import (
    StudentPortalLoginView, StudentPortalDashboardView,
    StudentRepresentativeDashboardView, StudentPortalProfileView,
    StudentFeedbackViewSet, StudentRepresentativeActivityViewSet,
    StudentRepresentativeViewSet, StudentPortalStatsView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'feedback', StudentFeedbackViewSet, basename='student-feedback')
router.register(r'representative-activities', StudentRepresentativeActivityViewSet, basename='representative-activities')
router.register(r'representatives', StudentRepresentativeViewSet, basename='representatives')

app_name = 'student_portal'

urlpatterns = [
    # Authentication
    path('auth/login/', StudentPortalLoginView.as_view(), name='login'),
    
    # Dashboard endpoints
    path('dashboard/', StudentPortalDashboardView.as_view(), name='dashboard'),
    path('representative/dashboard/', StudentRepresentativeDashboardView.as_view(), name='representative-dashboard'),
    
    # Profile management
    path('profile/', StudentPortalProfileView.as_view(), name='profile'),
    
    # Statistics
    path('stats/', StudentPortalStatsView.as_view(), name='stats'),
    
    # Include router URLs
    path('', include(router.urls)),
]
