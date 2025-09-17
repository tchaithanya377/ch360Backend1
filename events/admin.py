from django.contrib import admin
from .models import Venue, EventCategory, Event, EventRegistration


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'capacity', 'is_active', 'created_at')
    list_filter = ('state', 'city', 'is_active')
    search_fields = ('name', 'city', 'address')


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'venue', 'start_at', 'end_at', 'status', 'is_public')
    list_filter = ('status', 'is_public', 'category')
    search_fields = ('title', 'description')
    autocomplete_fields = ('category', 'venue',)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'attendee_name', 'attendee_email', 'attendee_type', 'is_waitlisted', 'created_at')
    list_filter = ('attendee_type', 'is_waitlisted')
    search_fields = ('attendee_name', 'attendee_email')
    autocomplete_fields = ('event', 'user')


