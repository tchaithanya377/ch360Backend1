"""
Enhanced Integrated Academic System Models
Connects Academic Year, Semester, Timetable, and Attendance systems
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
import uuid

# Import existing models
from students.models import AcademicYear, Semester
from academics.models import CourseSection
from faculty.models import Faculty
from accounts.models import User

# =============================================================================
# INTEGRATED ACADEMIC SYSTEM MODELS
# =============================================================================

class TimeStampedModel(models.Model):
    """Abstract base class with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AcademicPeriod(models.Model):
    """
    Centralized academic period management.
    Links Academic Year and Semester for consistent data across all systems.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='academic_periods'
    )
    semester = models.ForeignKey(
        Semester,
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
        today = date.today()
        return self.period_start <= today <= self.period_end

    def get_duration_days(self):
        """Get duration of academic period in days"""
        return (self.period_end - self.period_start).days + 1


class TimetableSlot(TimeStampedModel):
    """
    Enhanced timetable slots with integrated academic period management.
    Replaces string-based academic year/semester with proper ForeignKey relationships.
    """
    DAYS = [(i, day) for i, day in enumerate([
        "Monday", "Tuesday", "Wednesday", "Thursday", 
        "Friday", "Saturday", "Sunday"
    ])]

    SLOT_TYPES = [
        ('LECTURE', 'Lecture'),
        ('LAB', 'Laboratory'),
        ('TUTORIAL', 'Tutorial'),
        ('SEMINAR', 'Seminar'),
        ('WORKSHOP', 'Workshop'),
        ('PROJECT', 'Project'),
    ]

    # Core relationships
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        help_text="Academic period for this timetable slot"
    )
    course_section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        help_text="Course section for this slot"
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name='teaching_slots',
        help_text="Faculty member teaching this slot"
    )
    
    # Schedule details
    day_of_week = models.IntegerField(
        choices=DAYS,
        db_index=True,
        help_text="Day of the week (0=Monday, 6=Sunday)"
    )
    start_time = models.TimeField(help_text="Slot start time")
    end_time = models.TimeField(help_text="Slot end time")
    room = models.CharField(
        max_length=64,
        blank=True,
        help_text="Room or venue for this slot"
    )
    
    # Slot configuration
    slot_type = models.CharField(
        max_length=20,
        choices=SLOT_TYPES,
        default='LECTURE',
        help_text="Type of slot (lecture, lab, etc.)"
    )
    max_students = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum students for this slot"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this slot is active"
    )
    
    # Additional metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes for this slot"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_timetable_slots'
    )

    class Meta:
        unique_together = [
            ('academic_period', 'course_section', 'day_of_week', 'start_time'),
            ('academic_period', 'faculty', 'day_of_week', 'start_time'),
        ]
        ordering = ['academic_period', 'day_of_week', 'start_time']
        verbose_name = "Timetable Slot"
        verbose_name_plural = "Timetable Slots"
        indexes = [
            models.Index(fields=['academic_period', 'day_of_week', 'start_time']),
            models.Index(fields=['course_section', 'academic_period']),
            models.Index(fields=['faculty', 'academic_period']),
            models.Index(fields=['is_active', 'academic_period']),
        ]

    def __str__(self):
        return f"{self.course_section} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time} ({self.academic_period})"

    def clean(self):
        """Validate timetable slot data"""
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
        
        # Check for overlapping slots for the same faculty
        overlapping = TimetableSlot.objects.filter(
            academic_period=self.academic_period,
            faculty=self.faculty,
            day_of_week=self.day_of_week,
            is_active=True
        ).exclude(id=self.id)
        
        for slot in overlapping:
            if (self.start_time < slot.end_time and self.end_time > slot.start_time):
                raise ValidationError(f"Faculty has overlapping slot: {slot}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration_minutes(self):
        """Calculate slot duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes

    @property
    def academic_year(self):
        """Get academic year from academic period"""
        return self.academic_period.academic_year.year

    @property
    def semester_name(self):
        """Get semester name from academic period"""
        return self.academic_period.semester.name

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
            self.academic_period.is_active and
            self.academic_period.is_ongoing and
            self.get_enrolled_students_count() > 0
        )


class AttendanceSession(TimeStampedModel):
    """
    Enhanced attendance session with integrated academic period management.
    Automatically inherits academic period from timetable slot.
    """
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('OPEN', 'Open for Attendance'),
        ('CLOSED', 'Closed'),
        ('LOCKED', 'Locked'),
        ('CANCELLED', 'Cancelled'),
    ]

    # Core relationships
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        help_text="Academic period for this session"
    )
    timetable_slot = models.ForeignKey(
        TimetableSlot,
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        help_text="Timetable slot this session is based on"
    )
    course_section = models.ForeignKey(
        CourseSection,
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        help_text="Course section for this session"
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name='attendance_sessions',
        help_text="Faculty member conducting this session"
    )
    
    # Session details
    scheduled_date = models.DateField(
        db_index=True,
        help_text="Date when this session is scheduled"
    )
    start_datetime = models.DateTimeField(
        help_text="Actual start date and time"
    )
    end_datetime = models.DateTimeField(
        help_text="Actual end date and time"
    )
    room = models.CharField(
        max_length=64,
        blank=True,
        help_text="Room or venue for this session"
    )
    
    # Session status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
        help_text="Current status of the session"
    )
    
    # Automation flags
    auto_opened = models.BooleanField(
        default=False,
        help_text="Whether this session was auto-opened"
    )
    auto_closed = models.BooleanField(
        default=False,
        help_text="Whether this session was auto-closed"
    )
    
    # QR code functionality
    qr_token = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="QR code token for attendance marking"
    )
    qr_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the QR token expires"
    )
    qr_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the QR token was generated"
    )
    
    # Biometric integration
    biometric_enabled = models.BooleanField(
        default=False,
        help_text="Whether biometric attendance is enabled"
    )
    biometric_device_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Biometric device ID for this session"
    )
    
    # Offline sync
    offline_sync_token = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Token for offline attendance sync"
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time offline data was synced"
    )
    
    # Additional metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes for this session"
    )
    makeup = models.BooleanField(
        default=False,
        help_text="Whether this is a makeup session"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_attendance_sessions'
    )

    class Meta:
        ordering = ['-scheduled_date', 'start_datetime']
        verbose_name = "Attendance Session"
        verbose_name_plural = "Attendance Sessions"
        indexes = [
            models.Index(fields=['academic_period', 'scheduled_date']),
            models.Index(fields=['course_section', 'scheduled_date']),
            models.Index(fields=['faculty', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
            models.Index(fields=['qr_token']),
            models.Index(fields=['offline_sync_token']),
        ]

    def __str__(self):
        return f"{self.course_section} - {self.scheduled_date} {self.start_datetime.time()} ({self.status})"

    def clean(self):
        """Validate attendance session data"""
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Start datetime must be before end datetime")
        
        # Ensure academic period matches timetable slot
        if self.timetable_slot and self.academic_period != self.timetable_slot.academic_period:
            raise ValidationError("Academic period must match timetable slot's academic period")

    def save(self, *args, **kwargs):
        # Auto-populate academic period from timetable slot
        if self.timetable_slot and not self.academic_period:
            self.academic_period = self.timetable_slot.academic_period
        
        # Auto-populate course section and faculty from timetable slot
        if self.timetable_slot:
            if not self.course_section:
                self.course_section = self.timetable_slot.course_section
            if not self.faculty:
                self.faculty = self.timetable_slot.faculty
            if not self.room:
                self.room = self.timetable_slot.room
        
        self.clean()
        super().save(*args, **kwargs)

    @property
    def academic_year(self):
        """Get academic year from academic period"""
        return self.academic_period.academic_year.year

    @property
    def semester_name(self):
        """Get semester name from academic period"""
        return self.academic_period.semester.name

    @property
    def duration_minutes(self):
        """Calculate session duration in minutes"""
        duration = self.end_datetime - self.start_datetime
        return int(duration.total_seconds() / 60)

    def get_attendance_records(self):
        """Get all attendance records for this session"""
        return self.attendance_records.all()

    def get_attendance_count(self):
        """Get count of attendance records"""
        return self.attendance_records.count()

    def get_present_count(self):
        """Get count of present students"""
        return self.attendance_records.filter(mark__in=['present', 'late']).count()

    def get_absent_count(self):
        """Get count of absent students"""
        return self.attendance_records.filter(mark='absent').count()

    def get_attendance_percentage(self):
        """Calculate attendance percentage for this session"""
        total_records = self.get_attendance_count()
        if total_records == 0:
            return 0.0
        
        present_count = self.get_present_count()
        return round((present_count / total_records) * 100, 2)

    def can_mark_attendance(self):
        """Check if attendance can be marked for this session"""
        return (
            self.status == 'OPEN' and
            self.academic_period.is_active and
            timezone.now() >= self.start_datetime and
            timezone.now() <= self.end_datetime
        )

    def generate_qr_token(self):
        """Generate QR token for this session"""
        import secrets
        import hashlib
        
        # Create unique token
        token_data = f"{self.id}_{self.scheduled_date}_{secrets.token_hex(16)}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:32]
        
        # Set token and expiry
        self.qr_token = token
        self.qr_expires_at = timezone.now() + timedelta(hours=1)  # 1 hour expiry
        self.qr_generated_at = timezone.now()
        self.save()
        
        return token


class AttendanceRecord(TimeStampedModel):
    """
    Enhanced attendance record with integrated academic period management.
    """
    MARK_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('EXCUSED', 'Excused'),
    ]

    SOURCE_CHOICES = [
        ('QR', 'QR Code Scan'),
        ('BIOMETRIC', 'Biometric Device'),
        ('MANUAL', 'Manual Entry'),
        ('OFFLINE', 'Offline Sync'),
        ('API', 'API Integration'),
    ]

    # Core relationships
    academic_period = models.ForeignKey(
        AcademicPeriod,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Academic period for this record"
    )
    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Attendance session this record belongs to"
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records',
        help_text="Student this record is for"
    )
    
    # Attendance details
    mark = models.CharField(
        max_length=20,
        choices=MARK_CHOICES,
        help_text="Attendance mark for this student"
    )
    marked_at = models.DateTimeField(
        default=timezone.now,
        help_text="When attendance was marked"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='MANUAL',
        help_text="How attendance was marked"
    )
    
    # Device and location information
    device_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Device ID used for marking"
    )
    device_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of device used"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the device"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Latitude of marking location"
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Longitude of marking location"
    )
    
    # Sync and modification tracking
    client_uuid = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Client UUID for offline sync"
    )
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Sync'),
            ('SYNCED', 'Synced'),
            ('CONFLICT', 'Sync Conflict'),
        ],
        default='SYNCED',
        help_text="Sync status for offline records"
    )
    
    # Vendor integration
    vendor_event_id = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="Vendor-specific event ID"
    )
    vendor_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Vendor-specific data"
    )
    
    # User tracking
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendance',
        help_text="User who marked this attendance"
    )
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_attendance',
        help_text="User who last modified this record"
    )
    
    # Additional metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes for this record"
    )

    class Meta:
        unique_together = ('session', 'student')
        ordering = ['-marked_at']
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        indexes = [
            models.Index(fields=['academic_period', 'marked_at']),
            models.Index(fields=['session', 'student']),
            models.Index(fields=['student', 'academic_period']),
            models.Index(fields=['mark', 'marked_at']),
            models.Index(fields=['source', 'marked_at']),
            models.Index(fields=['client_uuid']),
            models.Index(fields=['vendor_event_id']),
        ]

    def __str__(self):
        return f"{self.student} - {self.session} - {self.mark}"

    def save(self, *args, **kwargs):
        # Auto-populate academic period from session
        if self.session and not self.academic_period:
            self.academic_period = self.session.academic_period
        
        super().save(*args, **kwargs)

    @property
    def academic_year(self):
        """Get academic year from academic period"""
        return self.academic_period.academic_year.year

    @property
    def semester_name(self):
        """Get semester name from academic period"""
        return self.academic_period.semester.name

    @property
    def is_present(self):
        """Check if student is marked as present"""
        return self.mark in ['PRESENT', 'LATE']

    @property
    def is_absent(self):
        """Check if student is marked as absent"""
        return self.mark == 'ABSENT'

    @property
    def is_excused(self):
        """Check if student is marked as excused"""
        return self.mark == 'EXCUSED'


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_current_academic_period():
    """Get the current active academic period"""
    return AcademicPeriod.get_current_period()

def get_academic_period_by_date(date_obj):
    """Get academic period for a specific date"""
    return AcademicPeriod.get_period_by_date(date_obj)

def create_academic_period(academic_year, semester, period_start, period_end, is_current=False):
    """Create a new academic period"""
    return AcademicPeriod.objects.create(
        academic_year=academic_year,
        semester=semester,
        period_start=period_start,
        period_end=period_end,
        is_current=is_current
    )

def generate_sessions_from_timetable(academic_period, start_date, end_date):
    """Generate attendance sessions from timetable slots for a given period"""
    sessions_created = 0
    
    # Get all active timetable slots for the academic period
    slots = TimetableSlot.objects.filter(
        academic_period=academic_period,
        is_active=True
    )
    
    for slot in slots:
        current_date = start_date
        while current_date <= end_date:
            # Check if current date matches the slot's day of week
            if current_date.weekday() == slot.day_of_week:
                # Check if session already exists
                existing_session = AttendanceSession.objects.filter(
                    timetable_slot=slot,
                    scheduled_date=current_date
                ).first()
                
                if not existing_session:
                    # Create new session
                    start_datetime = timezone.datetime.combine(
                        current_date, slot.start_time
                    )
                    end_datetime = timezone.datetime.combine(
                        current_date, slot.end_time
                    )
                    
                    AttendanceSession.objects.create(
                        academic_period=academic_period,
                        timetable_slot=slot,
                        course_section=slot.course_section,
                        faculty=slot.faculty,
                        scheduled_date=current_date,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        room=slot.room,
                        status='SCHEDULED'
                    )
                    sessions_created += 1
            
            current_date += timedelta(days=1)
    
    return sessions_created
