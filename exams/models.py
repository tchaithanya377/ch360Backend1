import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from academics.models import Course, AcademicProgram
from departments.models import Department
from students.models import Student
from faculty.models import Faculty


class TimeStampedUUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ExamSession(TimeStampedUUIDModel):
    """Model for managing exam sessions/semesters"""
    SESSION_TYPES = [
        ('MID_SEM', 'Mid Semester'),
        ('END_SEM', 'End Semester'),
        ('QUIZ', 'Quiz'),
        ('ASSIGNMENT', 'Assignment'),
        ('PROJECT', 'Project'),
        ('PRACTICAL', 'Practical'),
        ('VIVA', 'Viva Voce'),
        ('THESIS', 'Thesis Defense'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200, help_text="Exam session name (e.g., Fall 2024 Mid Semester)")
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    academic_year = models.CharField(max_length=9, help_text="e.g., 2024-2025")
    semester = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(8)])
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start = models.DateTimeField(help_text="When students can start registering for exams")
    registration_end = models.DateTimeField(help_text="Last date for exam registration")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-academic_year', '-semester', 'start_date']
        verbose_name = "Exam Session"
        verbose_name_plural = "Exam Sessions"
    
    def __str__(self):
        return f"{self.name} - {self.academic_year}"
    
    @property
    def is_registration_open(self):
        now = timezone.now()
        return self.registration_start <= now <= self.registration_end
    
    @property
    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class ExamSchedule(TimeStampedUUIDModel):
    """Model for individual exam schedules"""
    EXAM_TYPES = [
        ('THEORY', 'Theory'),
        ('PRACTICAL', 'Practical'),
        ('VIVA', 'Viva Voce'),
        ('PROJECT', 'Project Presentation'),
        ('ASSIGNMENT', 'Assignment Submission'),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('POSTPONED', 'Postponed'),
    ]
    
    exam_session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='exam_schedules')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_schedules')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    title = models.CharField(max_length=200, help_text="Exam title")
    description = models.TextField(blank=True)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(help_text="Exam duration in minutes")
    total_marks = models.PositiveIntegerField(help_text="Total marks for the exam")
    passing_marks = models.PositiveIntegerField(help_text="Minimum marks required to pass")
    max_students = models.PositiveIntegerField(help_text="Maximum students that can take this exam")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    instructions = models.TextField(blank=True, help_text="Special instructions for students")
    is_online = models.BooleanField(default=False, help_text="Whether this is an online exam")
    online_platform = models.CharField(max_length=100, blank=True, help_text="Platform for online exams")
    
    class Meta:
        ordering = ['exam_date', 'start_time']
        verbose_name = "Exam Schedule"
        verbose_name_plural = "Exam Schedules"
        indexes = [
            models.Index(fields=['exam_session', 'course', 'exam_date'], name='idx_exam_sched_sc_date'),
            models.Index(fields=['exam_date'], name='idx_exam_sched_date'),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.exam_date})"
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        exam_datetime = timezone.make_aware(
            timezone.datetime.combine(self.exam_date, self.start_time)
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(self.exam_date, self.end_time)
        )
        return exam_datetime <= now <= end_datetime


class ExamRoom(TimeStampedUUIDModel):
    """Model for exam rooms/venues"""
    ROOM_TYPES = [
        ('CLASSROOM', 'Classroom'),
        ('LAB', 'Laboratory'),
        ('AUDITORIUM', 'Auditorium'),
        ('HALL', 'Examination Hall'),
        ('ONLINE', 'Online Platform'),
        ('OUTDOOR', 'Outdoor Venue'),
    ]
    
    name = models.CharField(max_length=100, help_text="Room name/number")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    capacity = models.PositiveIntegerField(help_text="Maximum seating capacity")
    building = models.CharField(max_length=100, blank=True)
    floor = models.PositiveIntegerField(blank=True, null=True)
    is_accessible = models.BooleanField(default=True, help_text="Wheelchair accessible")
    has_projector = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['building', 'floor', 'name']
        verbose_name = "Exam Room"
        verbose_name_plural = "Exam Rooms"
    
    def __str__(self):
        return f"{self.building} - {self.name} (Capacity: {self.capacity})"


class ExamRoomAllocation(TimeStampedUUIDModel):
    """Model for allocating exam rooms to exam schedules"""
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='room_allocations')
    exam_room = models.ForeignKey(ExamRoom, on_delete=models.CASCADE, related_name='exam_allocations')
    allocated_capacity = models.PositiveIntegerField(help_text="Number of seats allocated for this exam")
    is_primary = models.BooleanField(default=True, help_text="Primary room for the exam")
    notes = models.TextField(blank=True, help_text="Special notes about this allocation")
    
    class Meta:
        unique_together = ['exam_schedule', 'exam_room']
        verbose_name = "Exam Room Allocation"
        verbose_name_plural = "Exam Room Allocations"
    
    def __str__(self):
        return f"{self.exam_schedule} - {self.exam_room}"


class ExamStaffAssignment(TimeStampedUUIDModel):
    """Model for assigning staff to exam duties"""
    ROLE_CHOICES = [
        ('INVIGILATOR', 'Invigilator'),
        ('CHIEF_INVIGILATOR', 'Chief Invigilator'),
        ('DEPUTY_CHIEF', 'Deputy Chief Invigilator'),
        ('OBSERVER', 'Observer'),
        ('TECHNICAL_SUPPORT', 'Technical Support'),
        ('SECURITY', 'Security Staff'),
        ('CLEANING', 'Cleaning Staff'),
    ]
    
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='staff_assignments')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='exam_assignments')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    exam_room = models.ForeignKey(ExamRoom, on_delete=models.CASCADE, related_name='staff_assignments', null=True, blank=True)
    is_available = models.BooleanField(default=True, help_text="Whether staff is available for this duty")
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    
    class Meta:
        unique_together = ['exam_schedule', 'faculty']
        verbose_name = "Exam Staff Assignment"
        verbose_name_plural = "Exam Staff Assignments"
    
    def __str__(self):
        return f"{self.faculty} - {self.role} for {self.exam_schedule}"


class StudentDue(models.Model):
    """Model for tracking student dues and fees"""
    DUE_TYPES = [
        ('TUITION', 'Tuition Fee'),
        ('EXAM', 'Examination Fee'),
        ('LIBRARY', 'Library Fine'),
        ('LAB', 'Laboratory Fee'),
        ('HOSTEL', 'Hostel Fee'),
        ('OTHER', 'Other Dues'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partially Paid'),
        ('WAIVED', 'Waived'),
        ('OVERDUE', 'Overdue'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='dues')
    due_type = models.CharField(max_length=20, choices=DUE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-due_date', 'student']
        verbose_name = "Student Due"
        verbose_name_plural = "Student Dues"
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.due_type} (₹{self.amount})"
    
    @property
    def remaining_amount(self):
        return self.amount - self.paid_amount
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status == 'PENDING'


class ExamRegistration(TimeStampedUUIDModel):
    """Model for student exam registrations"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_registrations')
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    registration_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_registrations')
    approved_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    special_requirements = models.TextField(blank=True, help_text="Any special requirements or accommodations")
    
    class Meta:
        unique_together = ['student', 'exam_schedule']
        verbose_name = "Exam Registration"
        verbose_name_plural = "Exam Registrations"
        indexes = [
            models.Index(fields=['exam_schedule', 'status'], name='idx_examreg_schedule_status'),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.exam_schedule} ({self.status})"


class HallTicket(TimeStampedUUIDModel):
    """Model for generating hall tickets"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('PRINTED', 'Printed'),
        ('ISSUED', 'Issued to Student'),
        ('USED', 'Used in Exam'),
        ('EXPIRED', 'Expired'),
    ]
    
    exam_registration = models.OneToOneField(ExamRegistration, on_delete=models.CASCADE, related_name='hall_ticket')
    ticket_number = models.CharField(max_length=50, unique=True, help_text="Unique hall ticket number")
    exam_room = models.ForeignKey(ExamRoom, on_delete=models.CASCADE, related_name='hall_tickets', null=True, blank=True)
    seat_number = models.CharField(max_length=20, blank=True, help_text="Assigned seat number")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    generated_date = models.DateTimeField(auto_now_add=True)
    printed_date = models.DateTimeField(null=True, blank=True)
    issued_date = models.DateTimeField(null=True, blank=True)
    used_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    
    class Meta:
        ordering = ['-generated_date']
        verbose_name = "Hall Ticket"
        verbose_name_plural = "Hall Tickets"
    
    def __str__(self):
        return f"Hall Ticket {self.ticket_number} - {self.exam_registration.student.roll_number}"
    
    def generate_ticket_number(self):
        """Generate unique ticket number"""
        if not self.ticket_number:
            import random
            import string
            prefix = f"HT{self.exam_registration.exam_schedule.exam_session.academic_year[:4]}"
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.ticket_number = f"{prefix}{suffix}"
        return self.ticket_number


class ExamAttendance(TimeStampedUUIDModel):
    """Model for tracking exam attendance"""
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('DISQUALIFIED', 'Disqualified'),
        ('MEDICAL_LEAVE', 'Medical Leave'),
    ]
    
    exam_registration = models.OneToOneField(ExamRegistration, on_delete=models.CASCADE, related_name='attendance')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    invigilator = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='invigilated_exams')
    remarks = models.TextField(blank=True, help_text="Any remarks or notes")
    
    class Meta:
        verbose_name = "Exam Attendance"
        verbose_name_plural = "Exam Attendances"
    
    def __str__(self):
        return f"{self.exam_registration.student.roll_number} - {self.status}"


class ExamViolation(TimeStampedUUIDModel):
    """Model for tracking exam violations and misconduct"""
    VIOLATION_TYPES = [
        ('CHEATING', 'Cheating'),
        ('COPYING', 'Copying from others'),
        ('UNAUTHORIZED_MATERIAL', 'Using unauthorized material'),
        ('MOBILE_PHONE', 'Using mobile phone'),
        ('TALKING', 'Talking during exam'),
        ('LEAVING_SEAT', 'Leaving seat without permission'),
        ('LATE_ARRIVAL', 'Late arrival'),
        ('EARLY_DEPARTURE', 'Early departure'),
        ('OTHER', 'Other violation'),
    ]
    
    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('MAJOR', 'Major'),
        ('CRITICAL', 'Critical'),
    ]
    
    exam_registration = models.ForeignKey(ExamRegistration, on_delete=models.CASCADE, related_name='violations')
    violation_type = models.CharField(max_length=30, choices=VIOLATION_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField(help_text="Detailed description of the violation")
    reported_by = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='reported_violations')
    reported_at = models.DateTimeField(auto_now_add=True)
    action_taken = models.TextField(blank=True, help_text="Action taken against the violation")
    penalty = models.TextField(blank=True, help_text="Penalty imposed")
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_violations')
    
    class Meta:
        ordering = ['-reported_at']
        verbose_name = "Exam Violation"
        verbose_name_plural = "Exam Violations"
    
    def __str__(self):
        return f"{self.exam_registration.student.roll_number} - {self.violation_type}"


class ExamResult(TimeStampedUUIDModel):
    """Model for storing exam results"""
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100)'),
        ('A', 'A (80-89)'),
        ('B+', 'B+ (70-79)'),
        ('B', 'B (60-69)'),
        ('C+', 'C+ (50-59)'),
        ('C', 'C (40-49)'),
        ('D', 'D (30-39)'),
        ('F', 'F (Below 30)'),
        ('I', 'Incomplete'),
        ('W', 'Withdrawn'),
    ]
    
    exam_registration = models.OneToOneField(ExamRegistration, on_delete=models.CASCADE, related_name='result')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_pass = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, help_text="Additional remarks or comments")
    evaluated_by = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluated_results')
    evaluated_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False, help_text="Whether result is published to student")
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-evaluated_at']
        verbose_name = "Exam Result"
        verbose_name_plural = "Exam Results"
    
    def __str__(self):
        return f"{self.exam_registration.student.roll_number} - {self.grade} ({self.marks_obtained})"
    
    def calculate_grade_and_percentage(self):
        """Calculate grade and percentage based on marks obtained"""
        if self.marks_obtained is not None:
            total_marks = self.exam_registration.exam_schedule.total_marks
            self.percentage = (self.marks_obtained / total_marks) * 100
            
            # Determine grade based on percentage
            if self.percentage >= 90:
                self.grade = 'A+'
            elif self.percentage >= 80:
                self.grade = 'A'
            elif self.percentage >= 70:
                self.grade = 'B+'
            elif self.percentage >= 60:
                self.grade = 'B'
            elif self.percentage >= 50:
                self.grade = 'C+'
            elif self.percentage >= 40:
                self.grade = 'C'
            elif self.percentage >= 30:
                self.grade = 'D'
            else:
                self.grade = 'F'
            
            # Determine pass/fail
            self.is_pass = self.percentage >= self.exam_registration.exam_schedule.passing_marks
