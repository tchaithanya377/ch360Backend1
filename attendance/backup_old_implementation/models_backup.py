from __future__ import annotations

import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.utils import timezone

User = get_user_model()


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AcademicCalendarHoliday(TimeStampedModel):
    """Academic calendar holidays and special days"""
    name = models.CharField(max_length=255)
    date = models.DateField(db_index=True)
    is_full_day = models.BooleanField(default=True)
    academic_year = models.CharField(max_length=9, blank=True, help_text="Academic year (e.g., 2024-2025)")
    description = models.TextField(blank=True)

    class Meta:
        unique_together = [("name", "date")]
        indexes = [models.Index(fields=["date"])]
        db_table = "attendance_holiday"

    def __str__(self):
        return f"{self.name} - {self.date}"


class TimetableSlot(TimeStampedModel):
    """
    A recurring slot, e.g., Mon 10:00-10:50 for CourseSection.
    """
    DAYS = [(i, day) for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])]

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
    academic_year = models.CharField(max_length=9, help_text="Academic year (e.g., 2024-2025)")
    semester = models.CharField(max_length=20, help_text="Semester (e.g., Fall, Spring)")

    class Meta:
        indexes = [
            models.Index(fields=["course_section", "day_of_week", "start_time"]),
            models.Index(fields=["faculty", "day_of_week"]),
        ]
        db_table = "attendance_timetable_slot"

    def __str__(self):
        return f"{self.course_section} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class AttendanceSession(TimeStampedModel):
    """Enhanced attendance session with comprehensive status tracking"""
    STATUS = [
        ("scheduled", "Scheduled"),
        ("open", "Open"),
        ("closed", "Closed"),
        ("locked", "Locked"),
        ("cancelled", "Cancelled"),
    ]

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
    scheduled_date = models.DateField(db_index=True)
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    room = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=STATUS, default="scheduled", db_index=True)
    auto_opened = models.BooleanField(default=False)
    auto_closed = models.BooleanField(default=False)
    makeup = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    qr_token = models.CharField(max_length=255, blank=True, db_index=True)
    qr_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("timetable_slot", "scheduled_date")]
        indexes = [
            models.Index(fields=["course_section", "scheduled_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["faculty", "scheduled_date"]),
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

    def generate_qr_token(self):
        """Generate a new QR token for this session"""
        import jwt
        from datetime import timedelta
        
        payload = {
            "session_id": self.id,
            "exp": int((timezone.now() + timedelta(minutes=60)).timestamp())
        }
        self.qr_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        self.qr_expires_at = timezone.now() + timedelta(minutes=60)
        self.save(update_fields=["qr_token", "qr_expires_at"])


class StudentSnapshot(models.Model):
    """
    Denormalize enrollment at session time for stable historical reporting.
    """
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="snapshots")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="attendance_snapshots")
    course_section = models.ForeignKey('academics.CourseSection', on_delete=models.PROTECT)
    student_batch = models.ForeignKey('students.StudentBatch', on_delete=models.PROTECT, null=True, blank=True)
    roll_number = models.CharField(max_length=20, help_text="Student roll number at time of session")
    full_name = models.CharField(max_length=255, help_text="Student full name at time of session")

    class Meta:
        unique_together = [("session", "student")]
        db_table = "attendance_student_snapshot"

    def __str__(self):
        return f"{self.roll_number} - {self.session}"


class AttendanceRecord(TimeStampedModel):
    """Enhanced attendance record with multiple capture sources"""
    MARK = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("excused", "Excused"),
    ]
    SOURCE = [
        ("manual", "Manual"),
        ("qr", "QR"),
        ("biometric", "Biometric"),
        ("rfid", "RFID"),
        ("offline", "Offline"),
        ("import", "Import"),
        ("system", "System"),
    ]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="attendance_records")
    mark = models.CharField(max_length=16, choices=MARK)
    marked_at = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=16, choices=SOURCE, default="manual")
    reason = models.CharField(max_length=255, blank=True)
    vendor_event_id = models.CharField(max_length=128, blank=True, db_index=True)
    client_uuid = models.CharField(max_length=64, blank=True, db_index=True)  # offline dedupe
    marked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="marked_attendance"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        unique_together = [("session", "student")]
        indexes = [
            models.Index(fields=["student", "session"]),
            models.Index(fields=["vendor_event_id"]),
            models.Index(fields=["client_uuid"]),
            models.Index(fields=["marked_at"]),
        ]
        db_table = "attendance_record"

    def __str__(self):
        return f"{self.student.roll_number} - {self.session} - {self.mark}"

    @property
    def is_present(self):
        """Check if student is marked as present (including late)"""
        return self.mark in ["present", "late"]


class AttendanceCorrectionRequest(TimeStampedModel):
    """Correction requests for attendance records"""
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="correction_requests")
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="correction_requests")
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="attendance_corrections_requested")
    from_mark = models.CharField(max_length=16, choices=AttendanceRecord.MARK)
    to_mark = models.CharField(max_length=16, choices=AttendanceRecord.MARK)
    reason = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS, default="pending", db_index=True)
    decided_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="attendance_corrections_decided"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    supporting_document = models.FileField(upload_to="attendance_corrections/", null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["student", "session"]),
            models.Index(fields=["requested_by", "status"]),
        ]
        db_table = "attendance_correction_request"

    def __str__(self):
        return f"{self.student.roll_number} - {self.from_mark} to {self.to_mark}"


class LeaveApplication(TimeStampedModel):
    """Leave applications for students"""
    TYPE = [
        ("medical", "Medical"),
        ("maternity", "Maternity"),
        ("on_duty", "On Duty"),
        ("sport", "Sport/Cultural"),
        ("personal", "Personal"),
        ("other", "Other"),
    ]
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name="leave_applications")
    leave_type = models.CharField(max_length=32, choices=TYPE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    document = models.FileField(upload_to="leave_docs/", null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS, default="pending", db_index=True)
    decided_by = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="leave_decided"
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True)
    affects_attendance = models.BooleanField(default=True, help_text="Whether this leave affects attendance calculation")

    class Meta:
        indexes = [
            models.Index(fields=["student", "start_date", "end_date"]), 
            models.Index(fields=["status"]),
            models.Index(fields=["leave_type", "status"]),
        ]
        db_table = "attendance_leave_application"

    def __str__(self):
        return f"{self.student.roll_number} - {self.leave_type} ({self.start_date} to {self.end_date})"

    @property
    def duration_days(self):
        """Calculate leave duration in days"""
        return (self.end_date - self.start_date).days + 1


class AttendanceAuditLog(TimeStampedModel):
    """
    Immutable audit trail for attendance changes.
    """
    entity_type = models.CharField(max_length=64)  # e.g., 'AttendanceRecord'
    entity_id = models.CharField(max_length=64)
    action = models.CharField(max_length=32)  # 'create', 'update', 'approve', 'reject'
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="attendance_audit_logs")
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    source = models.CharField(max_length=32, default="system")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["performed_by", "created_at"]),
        ]
        db_table = "attendance_audit_log"

    def __str__(self):
        return f"{self.action} on {self.entity_type} by {self.performed_by}"


class AttendanceConfiguration(models.Model):
    """Configuration settings for attendance system"""
    key = models.CharField(max_length=100, unique=True)
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
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_configuration"

    def __str__(self):
        return f"{self.key} = {self.value}"

    def get_typed_value(self):
        """Get the value converted to its proper type"""
        if self.data_type == "integer":
            return int(self.value)
        elif self.data_type == "float":
            return float(self.value)
        elif self.data_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.data_type == "json":
            import json
            return json.loads(self.value)
        return self.value


# Configuration helper functions
def get_attendance_settings() -> dict:
    """Get attendance configuration settings"""
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
    denominator = total_sessions - excused_count if exclude_excused_from_denominator else total_sessions
    denominator = max(denominator, 1)
    return round(100.0 * (present_count / denominator), 2)


def get_student_attendance_summary(student, course_section=None, start_date=None, end_date=None):
    """Get comprehensive attendance summary for a student"""
    from django.db.models import Count, Q
    
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
    percentage = compute_attendance_percentage(present_count, total_sessions, excused_count)
    
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
    
    return {
        "total_sessions": total_sessions,
        "present": present_count,
        "absent": absent_count,
        "late": late_count,
        "excused": excused_count,
        "percentage": percentage,
        "leave_days": leave_days,
        "is_eligible": percentage >= get_attendance_settings()["THRESHOLD_PERCENT"]
    }

