from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass
from .serializers import (
    VehicleSerializer,
    DriverSerializer,
    RouteSerializer,
    StopSerializer,
    RouteStopSerializer,
    VehicleAssignmentSerializer,
    TripScheduleSerializer,
    TransportPassSerializer,
)
from .permissions import IsStaffOrReadOnly


class DefaultPermission(IsStaffOrReadOnly):
    pass


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["number_plate", "registration_number", "make", "model"]
    ordering_fields = ["number_plate", "capacity", "created_at"]


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "phone", "license_number"]
    ordering_fields = ["full_name", "license_expiry", "created_at"]


class StopViewSet(viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "landmark"]
    ordering_fields = ["name", "created_at"]


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class RouteStopViewSet(viewsets.ModelViewSet):
    queryset = RouteStop.objects.select_related("route", "stop").all()
    serializer_class = RouteStopSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["route", "stop"]
    ordering_fields = ["order_index"]


class VehicleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = VehicleAssignment.objects.select_related("vehicle", "driver", "route").all()
    serializer_class = VehicleAssignmentSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["vehicle", "driver", "route", "is_active"]
    ordering_fields = ["start_date", "end_date"]


class TripScheduleViewSet(viewsets.ModelViewSet):
    queryset = TripSchedule.objects.select_related("assignment").all()
    serializer_class = TripScheduleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["assignment", "day_of_week"]
    ordering_fields = ["day_of_week", "departure_time"]


class TransportPassViewSet(viewsets.ModelViewSet):
    queryset = TransportPass.objects.select_related("user", "route", "start_stop", "end_stop").all()
    serializer_class = TransportPassSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "route", "pass_type", "is_active"]
    ordering_fields = ["valid_from", "valid_to", "price"]

