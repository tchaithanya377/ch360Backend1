from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VenueViewSet, EventCategoryViewSet, EventViewSet, EventRegistrationViewSet


router = DefaultRouter()
router.register(r'venues', VenueViewSet, basename='venue')
router.register(r'categories', EventCategoryViewSet, basename='eventcategory')
router.register(r'events', EventViewSet, basename='event')
router.register(r'registrations', EventRegistrationViewSet, basename='eventregistration')


app_name = 'events'
urlpatterns = [
    path('', include(router.urls)),
]


