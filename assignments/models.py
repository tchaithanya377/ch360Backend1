import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def assignment_file_upload_path(instance, filename):
    """Generate upload path for assignment files"""
    return f'assignments/{instance.assignment.id}/files/{filename}'


def submission_file_upload_path(instance, filename):
    """Generate upload path for submission files"""
    return f'submissions/{instance.submission.id}/files/{filename}'


class AssignmentCategory(TimeStampedUUIDModel):
    """Model for categorizing assignments"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    color_code = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Assignment Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Assignment(TimeStampedUUIDModel):
    """Model for assignments created by faculty"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        AssignmentCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assignments'
    )
    
    # Faculty Information
    faculty = models.ForeignKey(
        'faculty.Faculty', 
        on_delete=models.CASCADE, 
        related_name='assignments'
    )
    
    # Assignment Details
    max_marks = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    due_date = models.DateTimeField()
    late_submission_allowed = models.BooleanField(default=False)
    
    # Assignment Settings
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    is_group_assignment = models.BooleanField(default=False)
    max_group_size = models.PositiveIntegerField(default=1, help_text="Maximum group size for group assignments")
    
    # Target Audience
    assigned_to_programs = models.ManyToManyField(
        'academics.AcademicProgram', 
        blank=True, 
        related_name='assignments',
        help_text="Academic programs this assignment is assigned to"
    )
    assigned_to_departments = models.ManyToManyField(
        'departments.Department', 
        blank=True, 
        related_name='assignments',
        help_text="Departments this assignment is assigned to"
    )
    assigned_to_courses = models.ManyToManyField(
        'academics.Course', 
        blank=True, 
        related_name='course_assignments',
        help_text="Courses this assignment is assigned to"
    )
    assigned_to_course_sections = models.ManyToManyField(
        'academics.CourseSection', 
        blank=True, 
        related_name='assignments',
        help_text="Course sections this assignment is assigned to"
    )
    assigned_to_students = models.ManyToManyField(
        'students.Student', 
        blank=True, 
        related_name='assignments',
        help_text="Specific students this assignment is assigned to"
    )
    
    # Academic Year and Semester
    academic_year = models.ForeignKey(
        'students.AcademicYear', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assignments',
        help_text="Academic year for this assignment"
    )
    semester = models.ForeignKey(
        'students.Semester', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assignments',
        help_text="Semester for this assignment"
    )
    
    # Additional Information
    attachment_files = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of file information for assignment attachments"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['faculty', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['academic_year', 'semester']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.faculty.name}"
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        return timezone.now() > self.due_date and self.status == 'PUBLISHED'
    
    @property
    def submission_count(self):
        """Get total number of submissions"""
        return self.submissions.count()
    
    @property
    def graded_count(self):
        """Get number of graded submissions"""
        return self.submissions.filter(grade__isnull=False).count()
    
    def clean(self):
        """Validate assignment data"""
        if self.is_group_assignment and self.max_group_size < 2:
            raise ValidationError("Group assignments must have a maximum group size of at least 2")
        
        if self.due_date <= timezone.now() and self.status == 'PUBLISHED':
            raise ValidationError("Due date must be in the future for published assignments")


class AssignmentSubmission(TimeStampedUUIDModel):
    """Model for student submissions"""
    
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('DRAFT', 'Draft'),
        ('LATE', 'Late Submission'),
        ('RESUBMITTED', 'Resubmitted'),
    ]
    
    # Submission Details
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='submissions'
    )
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='assignment_submissions'
    )
    
    # Submission Content
    content = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Additional notes from student")
    
    # Submission Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SUBMITTED')
    submission_date = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    
    # Files
    attachment_files = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of file information for submission attachments"
    )
    
    # Grading Information
    grade = models.OneToOneField(
        'AssignmentGrade', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='submission'
    )
    feedback = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='graded_submissions'
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submission_date']
        indexes = [
            models.Index(fields=['assignment', 'student']),
            models.Index(fields=['submission_date']),
            models.Index(fields=['status']),
            models.Index(fields=['assignment', 'status', 'submission_date']),
        ]
    
    def __str__(self):
        # Student model does not expose `name`; use full_name or fallback
        student_display = getattr(self.student, 'full_name', None)
        if callable(student_display):
            student_display = self.student.full_name
        if not student_display:
            student_display = getattr(self.student, 'roll_number', 'Student')
        return f"{student_display} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        """Override save to check for late submission"""
        if not self.pk:  # New submission
            if timezone.now() > self.assignment.due_date:
                self.is_late = True
                if self.status == 'SUBMITTED':
                    self.status = 'LATE'
        super().save(*args, **kwargs)


class AssignmentFile(TimeStampedUUIDModel):
    """Model for assignment and submission files"""
    
    FILE_TYPE_CHOICES = [
        ('ASSIGNMENT', 'Assignment File'),
        ('SUBMISSION', 'Submission File'),
    ]
    
    # File Information
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='files'
    )
    submission = models.ForeignKey(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='files'
    )
    
    # File Details
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(
        upload_to=assignment_file_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'rar']
            )
        ]
    )
    file_type = models.CharField(max_length=15, choices=FILE_TYPE_CHOICES)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Upload Information
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='uploaded_files'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['assignment', 'file_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.file_name} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate file size"""
        if self.file_path:
            self.file_size = self.file_path.size
        super().save(*args, **kwargs)


class AssignmentGrade(TimeStampedUUIDModel):
    """Model for assignment grades"""
    
    GRADE_LETTER_CHOICES = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('B-', 'B-'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('C-', 'C-'),
        ('D+', 'D+'),
        ('D', 'D'),
        ('F', 'F'),
        ('P', 'Pass'),
        ('NP', 'No Pass'),
    ]
    
    # Grade Information
    marks_obtained = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    grade_letter = models.CharField(
        max_length=2, 
        choices=GRADE_LETTER_CHOICES,
        blank=True, 
        null=True
    )
    feedback = models.TextField(blank=True, null=True)
    
    # Grading Information
    graded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_grades'
    )
    graded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-graded_at']
        indexes = [
            models.Index(fields=['graded_at']),
            models.Index(fields=['grade_letter']),
        ]
    
    def __str__(self):
        return f"{self.marks_obtained} - {self.grade_letter or 'No Grade'}"
    
    def clean(self):
        """Validate grade data"""
        if self.marks_obtained < 0:
            raise ValidationError("Marks obtained cannot be negative")


class AssignmentComment(TimeStampedUUIDModel):
    """Model for comments on assignments"""
    
    COMMENT_TYPE_CHOICES = [
        ('GENERAL', 'General Comment'),
        ('CLARIFICATION', 'Clarification'),
        ('FEEDBACK', 'Feedback'),
        ('QUESTION', 'Question'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    
    # Comment Information
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignment_comments'
    )
    content = models.TextField()
    comment_type = models.CharField(max_length=15, choices=COMMENT_TYPE_CHOICES, default='GENERAL')
    
    # Reply Information
    parent_comment = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='replies'
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['assignment', 'created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"{self.author.email} - {self.assignment.title}"


class AssignmentGroup(TimeStampedUUIDModel):
    """Model for group assignments"""
    
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='groups'
    )
    group_name = models.CharField(max_length=100)
    members = models.ManyToManyField(
        'students.Student', 
        related_name='assignment_groups'
    )
    leader = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='led_groups'
    )
    
    class Meta:
        unique_together = ('assignment', 'group_name')
        ordering = ['group_name']
    
    def __str__(self):
        return f"{self.group_name} - {self.assignment.title}"
    
    def clean(self):
        """Validate group data"""
        if self.assignment and not self.assignment.is_group_assignment:
            raise ValidationError("Cannot create groups for non-group assignments")
        
        if self.assignment and len(self.members.all()) > self.assignment.max_group_size:
            raise ValidationError(f"Group size cannot exceed {self.assignment.max_group_size} members")


class AssignmentTemplate(TimeStampedUUIDModel):
    """Model for assignment templates"""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        AssignmentCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    max_marks = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    is_group_assignment = models.BooleanField(default=False)
    max_group_size = models.PositiveIntegerField(default=1)
    template_data = models.JSONField(
        default=dict,
        help_text="Additional template configuration data"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignment_templates'
    )
    is_public = models.BooleanField(default=False, help_text="Available to all faculty")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
