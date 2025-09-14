from rest_framework import serializers
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"


class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = "__all__"


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = "__all__"


class RouteStopSerializer(serializers.ModelSerializer):
    stop = StopSerializer(read_only=True)
    stop_id = serializers.PrimaryKeyRelatedField(queryset=Stop.objects.all(), source="stop", write_only=True)

    class Meta:
        model = RouteStop
        fields = ("id", "route", "stop", "stop_id", "order_index", "arrival_offset_min", "created_at", "updated_at")


class RouteSerializer(serializers.ModelSerializer):
    route_stops = RouteStopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ("id", "name", "description", "distance_km", "is_active", "route_stops", "created_at", "updated_at")


class VehicleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleAssignment
        fields = "__all__"


class TripScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TripSchedule
        fields = "__all__"


class TransportPassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportPass
        fields = "__all__"


