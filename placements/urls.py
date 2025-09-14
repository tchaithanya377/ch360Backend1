from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, JobPostingViewSet, ApplicationViewSet, PlacementDriveViewSet, InterviewRoundViewSet, OfferViewSet


router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'jobs', JobPostingViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'drives', PlacementDriveViewSet, basename='drive')
router.register(r'rounds', InterviewRoundViewSet, basename='round')
router.register(r'offers', OfferViewSet, basename='offer')


app_name = 'placements'


urlpatterns = [
    path('api/', include(router.urls)),
]


