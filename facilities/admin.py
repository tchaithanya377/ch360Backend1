from django.contrib import admin
from .models import Building, Room, Equipment, RoomEquipment, Booking, Maintenance


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "building", "room_type", "capacity", "is_active")
    list_filter = ("room_type", "building", "is_active")
    search_fields = ("code", "name")


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(RoomEquipment)
class RoomEquipmentAdmin(admin.ModelAdmin):
    list_display = ("room", "equipment", "quantity")
    list_filter = ("equipment", "room__building")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("title", "room", "starts_at", "ends_at", "is_approved")
    list_filter = ("is_approved", "room__building")
    search_fields = ("title", "purpose")


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ("room", "title", "status", "scheduled_for", "resolved_at")
    list_filter = ("status", "room__building")

# Register your models here.
