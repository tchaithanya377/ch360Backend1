from django.utils import timezone
from django.db.models import Q
from rest_framework import filters
from core.viewsets import HighPerformanceViewSet
from .models import Venue, EventCategory, Event, EventRegistration
from .serializers import (
    VenueSerializer,
    EventCategorySerializer,
    EventSerializer,
    EventRegistrationSerializer,
)


class VenueViewSet(HighPerformanceViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    filterset_fields = ['city', 'state', 'is_active']
    search_fields = ['name', 'address', 'city']
    ordering_fields = ['name', 'created_at']


class EventCategoryViewSet(HighPerformanceViewSet):
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    filterset_fields = ['is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']


class EventViewSet(HighPerformanceViewSet):
    queryset = Event.objects.select_related('category', 'venue').all()
    serializer_class = EventSerializer
    filterset_fields = ['category', 'venue', 'status', 'is_public']
    search_fields = ['title', 'description']
    ordering_fields = ['start_at', 'end_at', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional date range filtering
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start:
            qs = qs.filter(end_at__gte=start)
        if end:
            qs = qs.filter(start_at__lte=end)
        # Upcoming filter
        upcoming = self.request.query_params.get('upcoming')
        if upcoming == 'true':
            qs = qs.filter(start_at__gte=timezone.now())
        return qs


class EventRegistrationViewSet(HighPerformanceViewSet):
    queryset = EventRegistration.objects.select_related('event', 'user').all()
    serializer_class = EventRegistrationSerializer
    filterset_fields = ['event', 'user', 'attendee_type', 'is_waitlisted']
    search_fields = ['attendee_name', 'attendee_email']
    ordering_fields = ['created_at']


