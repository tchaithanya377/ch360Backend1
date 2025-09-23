"""
Enhanced Attendance Models for CampsHub360
Production-ready, timetable-driven attendance system for AP universities
"""

from __future__ import annotations

import uuid
import json
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import Q, F, Count, Sum, Case, When, IntegerField
from django.utils import timezone
from django.utils.functional import cached_property

User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TimeStampedUUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# =============================================================================
# INTEGRATED ACADEMIC SYSTEM MODELS
# =============================================================================

class AcademicPeriod(models.Model):
    """
    Centralized academic period management.
    Links Academic Year and Semester for consistent data across all systems.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(
        'students.AcademicYear',
        on_delete=models.CASCADE,
        related_name='academic_periods'
    )
    semester = models.ForeignKey(
        'students.Semester',
        on_delete=models.CASCADE,
        related_name='academic_periods'
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Whether this is the current active academic period"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this academic period is active"
    )
    
    # Period dates for easy reference
    period_start = models.DateField(
        help_text="Start date of this academic period"
    )
    period_end = models.DateField(
        help_text="End date of this academic period"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Additional description for this academic period"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_academic_periods'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('academic_year', 'semester')
        ordering = ['-academic_year__year', '-semester__semester_type']
        verbose_name = "Academic Period"
        verbose_name_plural = "Academic Periods"
        indexes = [
            models.Index(fields=['is_current', 'is_active']),
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['academic_year', 'semester']),
        ]

    def __str__(self):
        return f"{self.semester.name} {self.academic_year.year}"

    def clean(self):
        """Validate academic period data"""
        if self.period_start >= self.period_end:
            raise ValidationError("Period start date must be before end date")
        
        # Ensure only one current period exists
        if self.is_current:
            existing_current = AcademicPeriod.objects.filter(
                is_current=True
            ).exclude(id=self.id)
            if existing_current.exists():
                raise ValidationError("Only one academic period can be current")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_current_period(cls):
        """Get the current active academic period"""
        return cls.objects.filter(is_current=True, is_active=True).first()

    @classmethod
    def get_period_by_date(cls, date_obj):
        """Get academic period for a specific date"""
        return cls.objects.filter(
            period_start__lte=date_obj,
            period_end__gte=date_obj,
            is_active=True
        ).first()

    @property
    def display_name(self):
        """Human-readable display name"""
        return f"{self.semester.name} {self.academic_year.year}"

    @property
    def is_ongoing(self):
        """Check if this period is currently ongoing"""
        today = timezone.now().date()
        return self.period_start <= today <= self.period_end

    def get_duration_days(self):
        """Get duration of academic period in days"""
        return (self.period_end - self.period_start).days + 1


# =============================================================================
# CONFIGURATION MODELS
# =============================================================================

class AttendanceConfiguration(models.Model):
    """System-wide attendance configuration settings"""
    id = models.BigAutoField(primary_key=True, serialize=False)
    updated_at = models.DateTimeField(auto_now=True)
    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    data_type = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("integer", "Integer"),
            ("float", "Float"),
            ("boolean", "Boolean"),
            ("json", "JSON"),
        ],
        default="string"
    )
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_attendance_configs'
    )

    class Meta:
        db_table = "attendance_configuration"
        verbose_name = "Attendance Configuration"
        verbose_name_plural = "Attendance Configurations"

    def __str__(self):
        return f"{self.key} = {self.value}"

    def get_typed_value(self):
        """Get the value converted to its proper type"""
        try:
            if self.data_type == "integer":
                return int(self.value)
            elif self.data_type == "float":
                return float(self.value)
            elif self.data_type == "boolean":
                return self.value.lower() in ("true", "1", "yes")
            elif self.data_type == "json":
                return json.loads(self.value)
            return self.value
        except (ValueError, TypeError):
            # If conversion fails, return the original value
            return self.value

    @classmethod
    def get_setting(cls, key: str, default=None):
        """Get a configuration setting with fallback to default"""
        try:
            config = cls.objects.get(key=key, is_active=True)
            return config.get_typed_value()
        except cls.DoesNotExist:
            return default


class AcademicCalendarHoliday(TimeStampedModel):
    """Academic calendar holidays and special days"""
    name = models.CharField(max_length=255)
    date = models.DateField(db_index=True)
    is_full_day = models.BooleanField(default=True)
    academic_year = models.CharField(max_length=9, blank=True)
    description = models.TextField(blank=True)
    affects_attendance = models.BooleanField(
        default=True,
        help_text="Whether this holiday affects attendance calculation"
    )

    class Meta:
        unique_together = [("name", "date")]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["academic_year", "date"]),
        ]
        db_table = "attendance_holiday"

    def __str__(self):
        return f"{self.name} - {self.date}"


# =============================================================================
# TIMETABLE MODELS
# =============================================================================

class TimetableSlot(TimeStampedModel):
    """
    Recurring timetable slots for course sections.
    These are used to generate attendance sessions.
    """
    DAYS = [(i, day) for i, day in enumerate([
        "Monday", "Tuesday", "Wednesday", "Thursday", 
        "Friday", "Saturday", "Sunday"
    ])]

    # Core relationships
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        null=True,
        blank=True,
        help_text="Academic period for this timetable slot"
    )
    course_section = models.ForeignKey(
        'academics.CourseSection',
        on_delete=models.CASCADE,
        related_name="timetable_slots"
    )
    faculty = models.ForeignKey(
        'faculty.Faculty',
        on_delete=models.PROTECT,
        related_name="teaching_slots"
    )
    day_of_week = models.IntegerField(choices=DAYS, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Legacy fields for backward compatibility (will be removed in future)
    academic_year = models.CharField(max_length=9, blank=True)
    semester = models.CharField(max_length=20, blank=True)
    
    # Additional metadata
    slot_type = models.CharField(
        max_length=20,
        choices=[
            ('LECTURE', 'Lecture'),
            ('LAB', 'Laboratory'),
            ('TUTORIAL', 'Tutorial'),
            ('SEMINAR', 'Seminar'),
        ],
        default='LECTURE'
    )
    max_students = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum students for this slot"
    )

    class Meta:
        unique_together = [
            ("academic_period", "course_section", "day_of_week", "start_time"),
            ("academic_period", "faculty", "day_of_week", "start_time"),
        ]
        indexes = [
            models.Index(fields=["academic_period", "day_of_week", "start_time"]),
            models.Index(fields=["course_section", "academic_period"]),
            models.Index(fields=["faculty", "academic_period"]),
            models.Index(fields=["is_active", "academic_period"]),
            # Legacy indexes for backward compatibility
            models.Index(fields=["academic_year", "semester", "is_active"]),
        ]
        db_table = "attendance_timetable_slot"

    def __str__(self):
        return f"{self.course_section} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    @property
    def duration_minutes(self):
        """Calculate slot duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes

    @property
    def academic_year_display(self):
        """Get academic year from academic period or legacy field"""
        if self.academic_period:
            return self.academic_period.academic_year.year
        return self.academic_year

    @property
    def semester_display(self):
        """Get semester from academic period or legacy field"""
        if self.academic_period:
            return self.academic_period.semester.name
        return self.semester

    def get_enrolled_students(self):
        """Get students enrolled in this course section"""
        return self.course_section.enrollments.filter(
            status='ENROLLED'
        ).select_related('student')

    def get_enrolled_students_count(self):
        """Get count of enrolled students"""
        return self.get_enrolled_students().count()

    def can_generate_sessions(self):
        """Check if this slot can generate attendance sessions"""
        return (
            self.is_active and
            self.academic_period and
            self.academic_period.is_active and
            self.academic_period.is_ongoing and
            self.get_enrolled_students_count() > 0
        )


# =============================================================================
# ATTENDANCE SESSION MODELS
# =============================================================================

class AttendanceSession(TimeStampedModel):
    """
    Individual attendance sessions generated from timetable slots.
    Each session represents a specific class instance.
    """
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("open", "Open for Attendance"),
        ("closed", "Closed"),
        ("locked", "Locked"),
        ("cancelled", "Cancelled"),
    ]

    # Core relationships
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        null=True,
        blank=True,
        help_text="Academic period for this session"
    )
    course_section = models.ForeignKey(
        'academics.CourseSection',
        on_delete=models.PROTECT,
        related_name="attendance_sessions"
    )
    faculty = models.ForeignKey(
        'faculty.Faculty',
        on_delete=models.PROTECT,
        related_name="attendance_sessions"
    )
    timetable_slot = models.ForeignKey(
        TimetableSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions"
    )

    # Session timing
    scheduled_date = models.DateField(db_index=True)
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    actual_start_datetime = models.DateTimeField(null=True, blank=True)
    actual_end_datetime = models.DateTimeField(null=True, blank=True)

    # Session details
    room = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="scheduled", db_index=True)
    
    # Automation flags
    auto_opened = models.BooleanField(default=False)
    auto_closed = models.BooleanField(default=False)
    
    # Session metadata
    makeup = models.BooleanField(default=False, help_text="Is this a makeup session?")
    notes = models.TextField(blank=True)
    
    # QR Code functionality
    qr_token = models.CharField(max_length=255, blank=True, db_index=True)
    qr_expires_at = models.DateTimeField(null=True, blank=True)
    qr_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Biometric integration
    biometric_enabled = models.BooleanField(default=False)
    biometric_device_id = models.CharField(max_length=100, blank=True)
    
    # Offline sync support
    offline_sync_token = models.CharField(max_length=255, blank=True, db_index=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("timetable_slot", "scheduled_date")]
        indexes = [
            models.Index(fields=["course_section", "scheduled_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["faculty", "scheduled_date"]),
            models.Index(fields=["qr_token"]),
            models.Index(fields=["offline_sync_token"]),
        ]
        db_table = "attendance_session"

    def __str__(self):
        return f"{self.course_section} - {self.scheduled_date} {self.start_datetime.time()}"

    @property
    def is_qr_valid(self):
        """Check if QR token is still valid"""
        if not self.qr_token or not self.qr_expires_at:
            return False
        return timezone.now() < self.qr_expires_at

    @property
    def is_active(self):
        """Check if session is currently active"""
        now = timezone.now()
        return (
            self.status == "open" and
            self.start_datetime <= now <= self.end_datetime
        )

    @property
    def duration_minutes(self):
        """Get session duration in minutes"""
        if self.actual_start_datetime and self.actual_end_datetime:
            delta = self.actual_end_datetime - self.actual_start_datetime
            return int(delta.total_seconds() / 60)
        elif self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return int(delta.total_seconds() / 60)
        return 0

    def generate_qr_token(self):
        """Generate a new QR token for this session"""
        import jwt
        from datetime import timedelta
        
        settings_dict = AttendanceConfiguration.get_setting('QR_TOKEN_EXPIRY_MINUTES', 60)
        expiry_minutes = int(settings_dict) if isinstance(settings_dict, (int, str)) else 60
        
        payload = {
            "session_id": str(self.id),
            "course_section_id": str(self.course_section_id),
            "faculty_id": str(self.faculty_id),
            "exp": int((timezone.now() + timedelta(minutes=expiry_minutes)).timestamp())
        }
        
        self.qr_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.qr_expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        self.qr_generated_at = timezone.now()
        self.save(update_fields=["qr_token", "qr_expires_at", "qr_generated_at"])

    @property
    def academic_year_display(self):
        """Get academic year from academic period"""
        if self.academic_period:
            return self.academic_period.academic_year.year
        return None

    @property
    def semester_display(self):
        """Get semester from academic period"""
        if self.academic_period:
            return self.academic_period.semester.name
        return None

    def save(self, *args, **kwargs):
        """Override save to auto-populate academic_period from timetable_slot"""
        # Auto-populate academic_period from timetable_slot if not set
        if self.timetable_slot and not self.academic_period:
            self.academic_period = self.timetable_slot.academic_period
        
        # Auto-populate course_section and faculty from timetable_slot if not set
        if self.timetable_slot:
            if not self.course_section:
                self.course_section = self.timetable_slot.course_section
            if not self.faculty:
                self.faculty = self.timetable_slot.faculty
            if not self.room:
                self.room = self.timetable_slot.room
        
        super().save(*args, **kwargs)

    def open_session(self, opened_by=None):
        """Open the session for attendance"""
        if self.status != "scheduled":
            raise ValueError(f"Cannot open session in {self.status} status")
        
        self.status = "open"
        self.actual_start_datetime = timezone.now()
        if opened_by:
            # Log the action
            AttendanceAuditLog.objects.create(
                entity_type="AttendanceSession",
                entity_id=str(self.id),
                action="open",
                performed_by=opened_by,
                after={"status": "open", "actual_start_datetime": self.actual_start_datetime.isoformat()}
            )
        self.save(update_fields=["status", "actual_start_datetime"])

    def close_session(self, closed_by=None):
        """Close the session"""
        if self.status != "open":
            raise ValueError(f"Cannot close session in {self.status} status")
        
        self.status = "closed"
        self.actual_end_datetime = timezone.now()
        if closed_by:
            # Log the action
            AttendanceAuditLog.objects.create(
                entity_type="AttendanceSession",
                entity_id=str(self.id),
                action="close",
                performed_by=closed_by,
                after={"status": "closed", "actual_end_datetime": self.actual_end_datetime.isoformat()}
            )
        self.save(update_fields=["status", "actual_end_datetime"])

    def lock_session(self, locked_by=None):
        """Lock the session"""
        if self.status != "closed":
            raise ValueError(f"Cannot lock session in {self.status} status")
        
        self.status = "locked"
        if locked_by:
            # Log the action
            AttendanceAuditLog.objects.create(
                entity_type="AttendanceSession",
                entity_id=str(self.id),
                action="lock",
                performed_by=locked_by,
                after={"status": "locked"}
            )
        self.save(update_fields=["status"])

    def generate_attendance_records(self):
        """Generate attendance records for all enrolled students"""
        
        # Get all enrolled students for this course section
        enrolled_students = self.course_section.enrollments.filter(
            status='ENROLLED'
        ).select_related('student')
        
        records_created = 0
        for enrollment in enrolled_students:
            # Check if record already exists
            if not AttendanceRecord.objects.filter(
                session=self,
                student=enrollment.student
            ).exists():
                AttendanceRecord.objects.create(
                    session=self,
                    student=enrollment.student,
                    academic_period=self.academic_period,
                    mark='absent',  # Default to absent, can be updated later
                    marked_by=self.faculty.user if hasattr(self.faculty, 'user') else None
                )
                records_created += 1
        
        return records_created

    def get_attendance_summary(self):
        """Get attendance summary for this session"""
        records = self.records.all()
        total_students = records.count()
        present_count = records.filter(mark__in=["present", "late"]).count()
        absent_count = records.filter(mark="absent").count()
        late_count = records.filter(mark="late").count()
        excused_count = records.filter(mark="excused").count()
        
        return {
            "total_students": total_students,
            "present": present_count,
            "absent": absent_count,
            "late": late_count,
            "excused": excused_count,
            "attendance_percentage": (present_count / total_students * 100) if total_students > 0 else 0
        }


class StudentSnapshot(TimeStampedModel):
    """
    Snapshot of student enrollment at the time of attendance session.
    This ensures historical accuracy even if student data changes.
    """
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="snapshots"
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="attendance_snapshots"
    )
    course_section = models.ForeignKey(
        'academics.CourseSection',
        on_delete=models.PROTECT
    )
    student_batch = models.ForeignKey(
        'students.StudentBatch',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    
    # Snapshot data
    roll_number = models.CharField(max_length=20)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    
    # Academic context
    academic_year = models.CharField(max_length=9, blank=True)
    semester = models.CharField(max_length=20, blank=True)
    year_of_study = models.CharField(max_length=1)
    section = models.CharField(max_length=1)

    class Meta:
        unique_together = [("session", "student")]
        db_table = "attendance_student_snapshot"

    def __str__(self):
        return f"{self.roll_number} - {self.session}"

    @classmethod
    def create_snapshot(cls, session, student):
        """Create a snapshot for a student in a session"""
        return cls.objects.create(
            session=session,
            student=student,
            course_section=session.course_section,
            student_batch=student.student_batch,
            roll_number=student.roll_number,
            full_name=student.full_name,
            email=student.email or "",
            phone=student.student_mobile or "",
            academic_year=student.academic_year or "",
            semester=student.semester or "",
            year_of_study=student.year_of_study or "",
            section=student.section or ""
        )


# =============================================================================
# ATTENDANCE RECORD MODELS
# =============================================================================

class AttendanceRecord(TimeStampedModel):
    """
    Individual attendance records for students in sessions.
    Supports multiple capture methods and offline sync.
    """
    MARK_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    ]
    
    SOURCE_CHOICES = [
        ("manual", "Manual Entry"),
        ("qr", "QR Code Scan"),
        ("biometric", "Biometric"),
        ("rfid", "RFID Card"),
        ("offline", "Offline Sync"),
        ("import", "Bulk Import"),
        ("system", "System Generated"),
    ]

    # Core relationships
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        null=True,
        blank=True,
        help_text="Academic period for this record"
    )
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records"
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )
    
    # Attendance data
    mark = models.CharField(max_length=16, choices=MARK_CHOICES)
    marked_at = models.DateTimeField(default=timezone.now, db_index=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default="manual")
    
    # Additional context
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Device and location tracking
    device_id = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Offline sync support
    client_uuid = models.CharField(max_length=64, blank=True, db_index=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending Sync"),
            ("synced", "Synced"),
            ("conflict", "Sync Conflict"),
        ],
        default="synced"
    )
    
    # Vendor integration
    vendor_event_id = models.CharField(max_length=128, blank=True, db_index=True)
    vendor_data = models.JSONField(default=dict, blank=True)
    
    # Audit trail
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendance"
    )
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modified_attendance"
    )

    class Meta:
        unique_together = [("session", "student")]
        indexes = [
            models.Index(fields=["student", "session"]),
            models.Index(fields=["vendor_event_id"]),
            models.Index(fields=["client_uuid"]),
            models.Index(fields=["marked_at"]),
            models.Index(fields=["sync_status"]),
            models.Index(fields=["source", "marked_at"]),
        ]
        db_table = "attendance_record"

    def __str__(self):
        return f"{self.student.roll_number} - {self.session} - {self.mark}"

    @property
    def is_present(self):
        """Check if student is marked as present (including late)"""
        return self.mark in ["present", "late"]

    @property
    def is_late(self):
        """Check if student is marked as late"""
        return self.mark == "late"

    @property
    def is_absent(self):
        """Check if student is marked as absent"""
        return self.mark == "absent"

    @property
    def is_excused(self):
        """Check if student is marked as excused"""
        return self.mark == "excused"

    @property
    def academic_year_display(self):
        """Get academic year from academic period"""
        if self.academic_period:
            return self.academic_period.academic_year.year
        return None

    @property
    def semester_display(self):
        """Get semester from academic period"""
        if self.academic_period:
            return self.academic_period.semester.name
        return None

    def save(self, *args, **kwargs):
        """Override save to auto-populate academic_period from session"""
        # Auto-populate academic_period from session if not set
        if self.session and not self.academic_period:
            self.academic_period = self.session.academic_period
        
        super().save(*args, **kwargs)

    def mark_late_if_appropriate(self):
        """Automatically mark as late if within grace period"""
        if self.mark == "present":
            grace_minutes = AttendanceConfiguration.get_setting('GRACE_PERIOD_MINUTES', 5)
            session_start = self.session.start_datetime
            grace_end = session_start + timedelta(minutes=grace_minutes)
            
            if self.marked_at > grace_end:
                self.mark = "late"
                self.save(update_fields=["mark"])

    @classmethod
    def bulk_mark_attendance(cls, session, attendance_data, marked_by=None):
        """Bulk mark attendance for multiple students"""
        records = []
        for data in attendance_data:
            record = cls(
                session=session,
                student_id=data['student_id'],
                mark=data['mark'],
                source=data.get('source', 'manual'),
                reason=data.get('reason', ''),
                marked_by=marked_by,
                device_id=data.get('device_id', ''),
                ip_address=data.get('ip_address'),
            )
            records.append(record)
        
        return cls.objects.bulk_create(records, ignore_conflicts=True)


# =============================================================================
# LEAVE AND CORRECTION MODELS
# =============================================================================

class LeaveApplication(TimeStampedModel):
    """Student leave applications with approval workflow"""
    TYPE_CHOICES = [
        ("medical", "Medical Leave"),
        ("maternity", "Maternity Leave"),
        ("on_duty", "On Duty Leave"),
        ("sport", "Sports/Cultural Leave"),
        ("personal", "Personal Leave"),
        ("emergency", "Emergency Leave"),
        ("other", "Other"),
    ]
    
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    # Core relationships
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="leave_applications"
    )
    
    # Leave details
    leave_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    supporting_document = models.FileField(
        upload_to="leave_documents/",
        null=True,
        blank=True
    )
    
    # Approval workflow
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decided_leaves"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    
    # Attendance impact
    affects_attendance = models.BooleanField(
        default=True,
        help_text="Whether this leave affects attendance calculation"
    )
    auto_apply_to_sessions = models.BooleanField(
        default=True,
        help_text="Automatically apply to relevant attendance sessions"
    )

    class Meta:
        indexes = [
            models.Index(fields=["student", "start_date", "end_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["leave_type", "status"]),
            models.Index(fields=["affects_attendance", "status"]),
        ]
        db_table = "attendance_leave_application"

    def __str__(self):
        return f"{self.student.roll_number} - {self.leave_type} ({self.start_date} to {self.end_date})"

    @property
    def duration_days(self):
        """Calculate leave duration in days"""
        return (self.end_date - self.start_date).days + 1

    def approve(self, approved_by, decision_note=""):
        """Approve the leave application"""
        self.status = "approved"
        self.decided_by = approved_by
        self.decided_at = timezone.now()
        self.decision_note = decision_note
        self.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])
        
        # Auto-apply to relevant sessions if enabled
        if self.auto_apply_to_sessions and self.affects_attendance:
            self._apply_to_sessions()

    def reject(self, rejected_by, decision_note=""):
        """Reject the leave application"""
        self.status = "rejected"
        self.decided_by = rejected_by
        self.decided_at = timezone.now()
        self.decision_note = decision_note
        self.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])

    def _apply_to_sessions(self):
        """Apply approved leave to relevant attendance sessions"""
        # Find sessions that overlap with leave period
        sessions = AttendanceSession.objects.filter(
            course_section__enrollments__student=self.student,
            course_section__enrollments__status='ENROLLED',
            scheduled_date__range=[self.start_date, self.end_date],
            status__in=['open', 'closed']
        ).distinct()
        
        for session in sessions:
            # Create or update attendance record
            record, created = AttendanceRecord.objects.get_or_create(
                session=session,
                student=self.student,
                defaults={
                    'mark': 'excused',
                    'source': 'system',
                    'reason': f'Approved {self.leave_type} leave',
                    'marked_by': self.decided_by,
                }
            )
            if not created and record.mark == 'absent':
                record.mark = 'excused'
                record.reason = f'Approved {self.leave_type} leave'
                record.save(update_fields=['mark', 'reason'])


class AttendanceCorrectionRequest(TimeStampedModel):
    """Correction requests for attendance records"""
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    # Core relationships
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="correction_requests"
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="correction_requests"
    )
    
    # Correction details
    from_mark = models.CharField(max_length=16, choices=AttendanceRecord.MARK_CHOICES)
    to_mark = models.CharField(max_length=16, choices=AttendanceRecord.MARK_CHOICES)
    reason = models.TextField()
    supporting_document = models.FileField(
        upload_to="attendance_corrections/",
        null=True,
        blank=True
    )
    
    # Request workflow
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="attendance_corrections_requested"
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", db_index=True)
    decided_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance_corrections_decided"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student", "session"]),
            models.Index(fields=["requested_by", "status"]),
        ]
        db_table = "attendance_correction_request"

    def __str__(self):
        return f"{self.student.roll_number} - {self.from_mark} to {self.to_mark}"

    def approve(self, approved_by, decision_note=""):
        """Approve the correction request"""
        with transaction.atomic():
            # Update the attendance record
            try:
                record = AttendanceRecord.objects.get(
                    session=self.session,
                    student=self.student
                )
                old_mark = record.mark
                record.mark = self.to_mark
                record.reason = f"Corrected from {self.from_mark} - {self.reason}"
                record.last_modified_by = approved_by
                record.save(update_fields=["mark", "reason", "last_modified_by"])
                
                # Log the change
                AttendanceAuditLog.objects.create(
                    entity_type="AttendanceRecord",
                    entity_id=str(record.id),
                    action="correction_approved",
                    performed_by=approved_by,
                    before={"mark": old_mark},
                    after={"mark": self.to_mark, "reason": record.reason},
                    reason=f"Correction request approved: {self.reason}"
                )
                
            except AttendanceRecord.DoesNotExist:
                # Create new record if it doesn't exist
                record = AttendanceRecord.objects.create(
                    session=self.session,
                    student=self.student,
                    mark=self.to_mark,
                    source="system",
                    reason=f"Corrected from {self.from_mark} - {self.reason}",
                    marked_by=approved_by,
                    last_modified_by=approved_by
                )
            
            # Update request status
            self.status = "approved"
            self.decided_by = approved_by
            self.decided_at = timezone.now()
            self.decision_note = decision_note
            self.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])

    def reject(self, rejected_by, decision_note=""):
        """Reject the correction request"""
        self.status = "rejected"
        self.decided_by = rejected_by
        self.decided_at = timezone.now()
        self.decision_note = decision_note
        self.save(update_fields=["status", "decided_by", "decided_at", "decision_note"])


# =============================================================================
# AUDIT AND ANALYTICS MODELS
# =============================================================================

class AttendanceAuditLog(TimeStampedModel):
    """
    Immutable audit trail for all attendance-related changes.
    Critical for compliance and debugging.
    """
    entity_type = models.CharField(max_length=64)  # e.g., 'AttendanceRecord', 'AttendanceSession'
    entity_id = models.CharField(max_length=64)
    action = models.CharField(max_length=32)  # 'create', 'update', 'approve', 'reject', etc.
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="attendance_audit_logs"
    )
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    source = models.CharField(max_length=32, default="system")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional context
    session_id = models.CharField(max_length=64, blank=True)
    student_id = models.CharField(max_length=64, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["performed_by", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["session_id", "created_at"]),
        ]
        db_table = "attendance_audit_log"

    def __str__(self):
        return f"{self.action} on {self.entity_type} by {self.performed_by}"


class AttendanceStatistics(TimeStampedModel):
    """
    Pre-calculated attendance statistics for performance optimization.
    Updated via Celery tasks.
    """
    # Context
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="attendance_statistics"
    )
    course_section = models.ForeignKey(
        'academics.CourseSection',
        on_delete=models.CASCADE,
        related_name="attendance_statistics"
    )
    academic_year = models.CharField(max_length=9)
    semester = models.CharField(max_length=20)
    
    # Statistics
    total_sessions = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)
    excused_count = models.PositiveIntegerField(default=0)
    
    # Calculated fields
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0
    )
    is_eligible_for_exam = models.BooleanField(default=True)
    
    # Date range
    period_start = models.DateField()
    period_end = models.DateField()
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ("student", "course_section", "academic_year", "semester", "period_start", "period_end")
        ]
        indexes = [
            models.Index(fields=["student", "course_section"]),
            models.Index(fields=["academic_year", "semester"]),
            models.Index(fields=["is_eligible_for_exam"]),
            models.Index(fields=["attendance_percentage"]),
        ]
        db_table = "attendance_statistics"

    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section} ({self.attendance_percentage}%)"

    def calculate_percentage(self):
        """Calculate attendance percentage"""
        if self.total_sessions == 0:
            self.attendance_percentage = 0.0
        else:
            # Exclude excused absences from denominator
            effective_sessions = self.total_sessions - self.excused_count
            if effective_sessions > 0:
                self.attendance_percentage = (self.present_count / effective_sessions) * 100
            else:
                self.attendance_percentage = 100.0
        
        # Check exam eligibility
        threshold = AttendanceConfiguration.get_setting('THRESHOLD_PERCENT', 75)
        self.is_eligible_for_exam = self.attendance_percentage >= threshold
        
        self.save(update_fields=["attendance_percentage", "is_eligible_for_exam"])


# =============================================================================
# BIOMETRIC INTEGRATION MODELS
# =============================================================================

class BiometricDevice(TimeStampedModel):
    """Biometric device registration and management"""
    DEVICE_TYPES = [
        ("fingerprint", "Fingerprint Scanner"),
        ("face", "Face Recognition"),
        ("iris", "Iris Scanner"),
        ("palm", "Palm Scanner"),
    ]
    
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("maintenance", "Under Maintenance"),
        ("error", "Error"),
    ]

    device_id = models.CharField(max_length=100, unique=True)
    device_name = models.CharField(max_length=200)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    location = models.CharField(max_length=200)
    room = models.CharField(max_length=64, blank=True)
    
    # Device status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    last_seen = models.DateTimeField(null=True, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    
    # Configuration
    is_enabled = models.BooleanField(default=True)
    auto_sync = models.BooleanField(default=True)
    sync_interval_minutes = models.PositiveIntegerField(default=5)
    
    # Network details
    ip_address = models.GenericIPAddressField()
    port = models.PositiveIntegerField(default=80)
    api_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "attendance_biometric_device"

    def __str__(self):
        return f"{self.device_name} ({self.device_id})"


class BiometricTemplate(TimeStampedModel):
    """Biometric templates for students (encrypted)"""
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name="biometric_templates"
    )
    device = models.ForeignKey(
        BiometricDevice,
        on_delete=models.CASCADE,
        related_name="templates"
    )
    
    # Encrypted template data
    template_data = models.TextField(help_text="Encrypted biometric template")
    template_hash = models.CharField(max_length=64, db_index=True)
    
    # Template metadata
    quality_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("student", "device")]
        indexes = [
            models.Index(fields=["template_hash"]),
            models.Index(fields=["is_active"]),
        ]
        db_table = "attendance_biometric_template"

    def __str__(self):
        return f"{self.student.roll_number} - {self.device.device_name}"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_attendance_settings() -> dict:
    """Get all attendance configuration settings with defaults"""
    configs = AttendanceConfiguration.objects.filter(is_active=True)
    settings_dict = {}
    
    for config in configs:
        settings_dict[config.key] = config.get_typed_value()
    
    # Set defaults if not configured
    defaults = {
        "GRACE_PERIOD_MINUTES": 5,
        "MIN_DURATION_FOR_PRESENT_MINUTES": 10,
        "THRESHOLD_PERCENT": 75,
        "ALLOW_QR_SELF_MARK": True,
        "OFFLINE_SYNC_MAX_DELTA_MINUTES": 120,
        "DEFAULT_TIMEZONE": "Asia/Kolkata",
        "DATA_RETENTION_YEARS": 7,
        "AUTO_OPEN_SESSIONS": True,
        "AUTO_CLOSE_SESSIONS": True,
        "QR_TOKEN_EXPIRY_MINUTES": 60,
        "MAX_CORRECTION_DAYS": 7,
        "BIOMETRIC_ENABLED": False,
        "RFID_ENABLED": False,
        "GPS_VERIFICATION": False,
        "AUTO_MARK_ABSENT": True,
        "SEND_ATTENDANCE_NOTIFICATIONS": True,
    }
    
    for key, default_value in defaults.items():
        if key not in settings_dict:
            settings_dict[key] = default_value
    
    return settings_dict


def compute_attendance_percentage(
    present_count: int,
    total_sessions: int,
    excused_count: int = 0,
    exclude_excused_from_denominator: bool = True
) -> float:
    """Compute attendance percentage with proper handling of excused absences"""
    if total_sessions <= 0:
        return 0.0
    
    if exclude_excused_from_denominator:
        denominator = total_sessions - excused_count
    else:
        denominator = total_sessions
    
    denominator = max(denominator, 1)
    return round(100.0 * (present_count / denominator), 2)


def get_student_attendance_summary(
    student,
    course_section=None,
    start_date=None,
    end_date=None,
    include_excused=True
):
    """Get comprehensive attendance summary for a student"""
    # Base query for attendance records
    records_query = AttendanceRecord.objects.filter(student=student)
    
    if course_section:
        records_query = records_query.filter(session__course_section=course_section)
    
    if start_date:
        records_query = records_query.filter(session__scheduled_date__gte=start_date)
    
    if end_date:
        records_query = records_query.filter(session__scheduled_date__lte=end_date)
    
    # Get counts
    total_sessions = records_query.count()
    present_count = records_query.filter(mark__in=["present", "late"]).count()
    absent_count = records_query.filter(mark="absent").count()
    late_count = records_query.filter(mark="late").count()
    excused_count = records_query.filter(mark="excused").count()
    
    # Calculate percentage
    percentage = compute_attendance_percentage(
        present_count, total_sessions, excused_count, include_excused
    )
    
    # Get leave applications that might affect attendance
    leave_query = LeaveApplication.objects.filter(
        student=student,
        status="approved",
        affects_attendance=True
    )
    
    if start_date:
        leave_query = leave_query.filter(start_date__lte=end_date or timezone.now().date())
    if end_date:
        leave_query = leave_query.filter(end_date__gte=start_date or timezone.now().date())
    
    leave_days = sum(leave.duration_days for leave in leave_query)
    
    # Check exam eligibility
    threshold = AttendanceConfiguration.get_setting('THRESHOLD_PERCENT', 75)
    is_eligible = percentage >= threshold
    
    return {
        "total_sessions": total_sessions,
        "present": present_count,
        "absent": absent_count,
        "late": late_count,
        "excused": excused_count,
        "percentage": percentage,
        "leave_days": leave_days,
        "is_eligible_for_exam": is_eligible,
        "threshold_percent": threshold
    }


def generate_sessions_from_timetable(
    start_date,
    end_date,
    course_sections=None,
    academic_year=None,
    semester=None
):
    """Generate attendance sessions from timetable slots for a date range"""
    from datetime import datetime, timedelta
    
    # Get timetable slots
    slots_query = TimetableSlot.objects.filter(is_active=True)
    
    if course_sections:
        slots_query = slots_query.filter(course_section__in=course_sections)
    if academic_year:
        slots_query = slots_query.filter(academic_year=academic_year)
    if semester:
        slots_query = slots_query.filter(semester=semester)
    
    sessions_created = 0
    
    for slot in slots_query:
        # Calculate session date based on day of week
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() == slot.day_of_week:
                # Check if session already exists
                existing_session = AttendanceSession.objects.filter(
                    timetable_slot=slot,
                    scheduled_date=current_date
                ).first()
                
                if not existing_session:
                    # Create session
                    session_start = datetime.combine(current_date, slot.start_time)
                    session_end = datetime.combine(current_date, slot.end_time)
                    
                    session = AttendanceSession.objects.create(
                        course_section=slot.course_section,
                        faculty=slot.faculty,
                        timetable_slot=slot,
                        scheduled_date=current_date,
                        start_datetime=session_start,
                        end_datetime=session_end,
                        room=slot.room,
                        status="scheduled"
                    )
                    
                    # Create student snapshots
                    enrolled_students = slot.course_section.enrollments.filter(
                        status='ENROLLED'
                    ).select_related('student')
                    
                    for enrollment in enrolled_students:
                        StudentSnapshot.create_snapshot(session, enrollment.student)
                    
                    sessions_created += 1
                
                break
            
            current_date += timedelta(days=1)
    
    return sessions_created
