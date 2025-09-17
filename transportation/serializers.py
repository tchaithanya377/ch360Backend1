from rest_framework import serializers
from django.utils import timezone
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass
from departments.models import Department
from students.models import StudentBatch


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


class BulkStudentPassAssignSerializer(serializers.Serializer):
    # Target cohort
    department_id = serializers.UUIDField()
    academic_year_id = serializers.IntegerField()
    year_of_study = serializers.ChoiceField(choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')])
    section = serializers.CharField(max_length=1)

    # Pass details
    route = serializers.PrimaryKeyRelatedField(queryset=Route.objects.all())
    start_stop = serializers.PrimaryKeyRelatedField(queryset=Stop.objects.all())
    end_stop = serializers.PrimaryKeyRelatedField(queryset=Stop.objects.all())
    valid_from = serializers.DateField(default=timezone.now)
    valid_to = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField(default=True)

    # Options
    skip_if_active_pass_exists = serializers.BooleanField(default=True)

    def validate(self, attrs):
        # Basic sanity checks
        if attrs['valid_to'] < attrs['valid_from']:
            raise serializers.ValidationError({'valid_to': 'valid_to must be on/after valid_from'})

        # Verify Department and StudentBatch existence shape
        try:
            Department.objects.only('id').get(id=attrs['department_id'])
        except Department.DoesNotExist:
            raise serializers.ValidationError({'department_id': 'Invalid department'})

        # Ensure a StudentBatch exists that matches the cohort
        batch_exists = StudentBatch.objects.filter(
            department_id=attrs['department_id'],
            academic_year_id=attrs['academic_year_id'],
            year_of_study=attrs['year_of_study'],
            section=attrs['section']
        ).exists()
        if not batch_exists:
            raise serializers.ValidationError('No StudentBatch found for the given department/year/section/academic_year')

        return attrs


class BulkFacultyPassAssignSerializer(serializers.Serializer):
    # Target cohort
    department_id = serializers.UUIDField()

    # Pass details
    route = serializers.PrimaryKeyRelatedField(queryset=Route.objects.all())
    start_stop = serializers.PrimaryKeyRelatedField(queryset=Stop.objects.all())
    end_stop = serializers.PrimaryKeyRelatedField(queryset=Stop.objects.all())
    valid_from = serializers.DateField(default=timezone.now)
    valid_to = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField(default=True)

    # Options
    skip_if_active_pass_exists = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if attrs['valid_to'] < attrs['valid_from']:
            raise serializers.ValidationError({'valid_to': 'valid_to must be on/after valid_from'})
        try:
            Department.objects.only('id').get(id=attrs['department_id'])
        except Department.DoesNotExist:
            raise serializers.ValidationError({'department_id': 'Invalid department'})
        return attrs

