from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Vehicle(TimeStampedModel):
    number_plate = models.CharField(max_length=32, unique=True)
    registration_number = models.CharField(max_length=64, unique=True)
    make = models.CharField(max_length=64, blank=True)
    model = models.CharField(max_length=64, blank=True)
    capacity = models.PositiveIntegerField(default=40)
    year_of_manufacture = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["number_plate"]

    def __str__(self):
        return f"{self.number_plate} ({self.capacity})"


class Driver(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="driver_profile")
    full_name = models.CharField(max_length=128)
    phone = models.CharField(max_length=20)
    license_number = models.CharField(max_length=64, unique=True)
    license_expiry = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name}"


class Route(TimeStampedModel):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Stop(TimeStampedModel):
    name = models.CharField(max_length=128)
    landmark = models.CharField(max_length=256, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    class Meta:
        unique_together = ("name", "landmark")
        ordering = ["name"]

    def __str__(self):
        return self.name


class RouteStop(TimeStampedModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="route_stops")
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name="stop_routes")
    order_index = models.PositiveIntegerField(default=0)
    arrival_offset_min = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("route", "stop")
        ordering = ["route", "order_index"]

    def __str__(self):
        return f"{self.route} -> {self.stop}"


class VehicleAssignment(TimeStampedModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="assignments")
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="assignments")
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.vehicle} on {self.route}"


class TripSchedule(TimeStampedModel):
    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    assignment = models.ForeignKey(VehicleAssignment, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    departure_time = models.TimeField()
    return_time = models.TimeField(blank=True, null=True)
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ("assignment", "day_of_week", "departure_time")
        ordering = ["assignment", "day_of_week", "departure_time"]


class TransportPass(TimeStampedModel):
    PASS_TYPES = [
        ("STUDENT", "Student"),
        ("STAFF", "Staff"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transport_passes")
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="passes")
    start_stop = models.ForeignKey(Stop, on_delete=models.PROTECT, related_name="pass_start_stops")
    end_stop = models.ForeignKey(Stop, on_delete=models.PROTECT, related_name="pass_end_stops")
    pass_type = models.CharField(max_length=16, choices=PASS_TYPES, default="STUDENT")
    valid_from = models.DateField(default=timezone.now)
    valid_to = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-valid_from"]

    def __str__(self):
        return f"{self.user} - {self.route} ({self.valid_from} -> {self.valid_to})"

