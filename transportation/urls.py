from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet,
    DriverViewSet,
    StopViewSet,
    RouteViewSet,
    RouteStopViewSet,
    VehicleAssignmentViewSet,
    TripScheduleViewSet,
    TransportPassViewSet,
)

app_name = 'transportation'

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'stops', StopViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'route-stops', RouteStopViewSet)
router.register(r'assignments', VehicleAssignmentViewSet)
router.register(r'schedules', TripScheduleViewSet)
router.register(r'passes', TransportPassViewSet)

urlpatterns = [
    path('', include(router.urls)),
]


