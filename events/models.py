from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TimeStampedUUIDModel


class Venue(TimeStampedUUIDModel):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, default='Andhra Pradesh')
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['city', 'state']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class EventCategory(TimeStampedUUIDModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, related_name='events')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, related_name='events')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    timezone_str = models.CharField(max_length=64, default='Asia/Kolkata')
    max_attendees = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='events_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='events_updated')

    class Meta:
        ordering = ['-start_at']
        indexes = [
            models.Index(fields=['start_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_at <= now <= self.end_at

    @property
    def is_future(self):
        return timezone.now() < self.start_at


class EventRegistration(TimeStampedUUIDModel):
    ATTENDEE_TYPE_CHOICES = [
        ('STUDENT', 'Student'),
        ('FACULTY', 'Faculty'),
        ('STAFF', 'Staff'),
        ('GUEST', 'Guest'),
        ('ALUMNI', 'Alumni'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='event_registrations')
    attendee_name = models.CharField(max_length=200)
    attendee_email = models.EmailField(blank=True, null=True)
    attendee_mobile = models.CharField(max_length=20, blank=True, null=True)
    attendee_type = models.CharField(max_length=20, choices=ATTENDEE_TYPE_CHOICES)
    checked_in_at = models.DateTimeField(blank=True, null=True)
    is_waitlisted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'user', 'attendee_email')
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['user']),
            models.Index(fields=['attendee_email']),
        ]

    def __str__(self):
        return f"{self.attendee_name} - {self.event.title}"


