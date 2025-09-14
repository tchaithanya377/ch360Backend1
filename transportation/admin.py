from django.contrib import admin
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("number_plate", "registration_number", "capacity", "is_active")
    search_fields = ("number_plate", "registration_number")
    list_filter = ("is_active",)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "license_number", "is_active")
    search_fields = ("full_name", "phone", "license_number")
    list_filter = ("is_active",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "distance_km", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ("name", "landmark", "latitude", "longitude")
    search_fields = ("name", "landmark")


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ("route", "stop", "order_index", "arrival_offset_min")
    list_filter = ("route",)


@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "driver", "route", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "route")
    autocomplete_fields = ("vehicle", "driver", "route")


@admin.register(TripSchedule)
class TripScheduleAdmin(admin.ModelAdmin):
    list_display = ("assignment", "day_of_week", "departure_time", "return_time")
    list_filter = ("day_of_week",)


@admin.register(TransportPass)
class TransportPassAdmin(admin.ModelAdmin):
    list_display = ("user", "route", "start_stop", "end_stop", "valid_from", "valid_to", "price", "is_active")
    list_filter = ("is_active", "route")
    search_fields = ("user__username", "user__email")

