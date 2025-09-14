from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Building(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Room(models.Model):
    CLASSROOM = 'classroom'
    LAB = 'lab'
    LECTURE_HALL = 'lecture_hall'
    MEETING_ROOM = 'meeting_room'

    ROOM_TYPE_CHOICES = [
        (CLASSROOM, 'Classroom'),
        (LAB, 'Lab'),
        (LECTURE_HALL, 'Lecture Hall'),
        (MEETING_ROOM, 'Meeting Room'),
    ]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=50)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default=CLASSROOM)
    capacity = models.PositiveIntegerField(default=20)
    floor = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('building', 'code')

    def __str__(self) -> str:
        return f"{self.building.code}-{self.code}"


class Equipment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class RoomEquipment(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_equipments')
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='equipment_rooms')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('room', 'equipment')


class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    title = models.CharField(max_length=255)
    purpose = models.CharField(max_length=255, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['room', 'starts_at', 'ends_at']),
        ]
        ordering = ['starts_at']

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError("Booking end time must be after start time.")
        if self.starts_at < timezone.now() and not self.pk:
            # do not allow creating past bookings
            raise ValidationError("Cannot create bookings in the past.")

        # check overlapping bookings
        overlapping = (
            Booking.objects.filter(room=self.room)
            .exclude(pk=self.pk)
            .filter(starts_at__lt=self.ends_at, ends_at__gt=self.starts_at)
            .exists()
        )
        if overlapping:
            raise ValidationError("Booking overlaps with an existing booking.")

    def __str__(self) -> str:
        return f"{self.title} @ {self.room} ({self.starts_at} - {self.ends_at})"


class Maintenance(models.Model):
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

    STATUS_CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='maintenances')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SCHEDULED)
    scheduled_for = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.room} - {self.title} ({self.status})"


# Create your models here.
