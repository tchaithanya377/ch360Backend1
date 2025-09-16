from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, JobPostingViewSet, ApplicationViewSet, PlacementDriveViewSet,
    InterviewRoundViewSet, OfferViewSet, PlacementStatisticsViewSet,
    CompanyFeedbackViewSet, PlacementDocumentViewSet, AlumniPlacementViewSet,
    PlacementAnalyticsViewSet
)


router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'jobs', JobPostingViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'drives', PlacementDriveViewSet, basename='drive')
router.register(r'rounds', InterviewRoundViewSet, basename='round')
router.register(r'offers', OfferViewSet, basename='offer')
router.register(r'statistics', PlacementStatisticsViewSet, basename='statistics')
router.register(r'feedbacks', CompanyFeedbackViewSet, basename='feedback')
router.register(r'documents', PlacementDocumentViewSet, basename='document')
router.register(r'alumni', AlumniPlacementViewSet, basename='alumni')
router.register(r'analytics', PlacementAnalyticsViewSet, basename='analytics')


app_name = 'placements'


urlpatterns = [
    path('api/', include(router.urls)),
]


