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
    
    ASSIGNMENT_TYPES = [
        ('HOMEWORK', 'Homework'),
        ('PROJECT', 'Project'),
        ('LAB_ASSIGNMENT', 'Lab Assignment'),
        ('RESEARCH_PAPER', 'Research Paper'),
        ('PRESENTATION', 'Presentation'),
        ('QUIZ', 'Quiz'),
        ('EXAM', 'Exam'),
        ('PEER_REVIEW', 'Peer Review'),
        ('PORTFOLIO', 'Portfolio'),
        ('FIELD_WORK', 'Field Work'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
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
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='HOMEWORK')
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_LEVELS, default='INTERMEDIATE')
    max_marks = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    due_date = models.DateTimeField()
    late_submission_allowed = models.BooleanField(default=False)
    late_penalty_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage penalty for late submissions (0-100)"
    )
    
    # Assignment Settings
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    is_group_assignment = models.BooleanField(default=False)
    max_group_size = models.PositiveIntegerField(default=1, help_text="Maximum group size for group assignments")
    
    # AP-Specific Features
    is_apaar_compliant = models.BooleanField(
        default=True, 
        help_text="Compliant with AP Academic Assessment and Accreditation Requirements"
    )
    requires_plagiarism_check = models.BooleanField(
        default=True, 
        help_text="Requires plagiarism detection check"
    )
    plagiarism_threshold = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=15.0,
        help_text="Maximum allowed similarity percentage (0-100)"
    )
    
    # Grading Integration
    rubric = models.ForeignKey(
        'AssignmentRubric', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assignments',
        help_text="Grading rubric for this assignment"
    )
    enable_peer_review = models.BooleanField(
        default=False, 
        help_text="Enable peer review for this assignment"
    )
    peer_review_weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Weight of peer review in final grade (0-100)"
    )
    
    # Learning Outcomes
    learning_objectives = models.TextField(
        blank=True, 
        null=True,
        help_text="Learning objectives for this assignment"
    )
    
    # Time Management
    estimated_time_hours = models.PositiveIntegerField(
        default=2, 
        help_text="Estimated time to complete in hours"
    )
    submission_reminder_days = models.PositiveIntegerField(
        default=1, 
        help_text="Days before due date to send reminder"
    )
    # Availability window (research-backed: explicit open/close improves student UX)
    available_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the assignment becomes visible and open for submissions"
    )
    available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional hard close; after this, no submissions are allowed"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when status first became PUBLISHED"
    )
    
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

    # Canonical links (simple assignment target)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_assignments',
        help_text="Primary department for this assignment"
    )
    course = models.ForeignKey(
        'academics.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_assignments',
        help_text="Primary course for this assignment"
    )
    course_section = models.ForeignKey(
        'academics.CourseSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_assignments',
        help_text="Primary course section for this assignment"
    )
    is_active = models.BooleanField(default=True)
    
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
            models.Index(fields=['department']),
            models.Index(fields=['course']),
            models.Index(fields=['course_section']),
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

        if self.available_until and self.due_date and self.available_until < self.due_date:
            raise ValidationError("available_until cannot be earlier than due_date")

        if self.course_section and self.course and self.course_section.course_id != self.course.id:
            raise ValidationError("course_section must belong to the selected course")

        if self.course and self.department and self.course.department_id and self.course.department_id != self.department.id:
            # Not fatal, but helps maintain canonical link integrity
            raise ValidationError("Selected course does not belong to the selected department")

        # If a course_section is selected, enforce integrity:
        if self.course_section:
            # Section must belong to selected course when course is set
            if self.course and self.course_section.course_id != self.course.id:
                raise ValidationError("Selected course_section does not belong to the chosen course")
            # Faculty teaching the section should match assignment faculty
            section_faculty_id = getattr(self.course_section, 'faculty_id', None)
            if section_faculty_id and self.faculty_id and section_faculty_id != self.faculty_id:
                raise ValidationError("Assignment faculty must match the course section faculty")
            # AP university rule: Max two assignments per section per semester
            try:
                from django.db.models import Q
                existing_count = Assignment.objects.filter(
                    course_section=self.course_section,
                    academic_year=self.academic_year,
                    semester=self.semester,
                    status__in=['DRAFT', 'PUBLISHED', 'CLOSED']
                ).exclude(id=self.id).count()
                if existing_count >= 2:
                    raise ValidationError("Only two assignments are allowed per course section in a semester")
            except Exception:
                # If validation query fails during migrations, ignore silently
                pass


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
        # Validate student belongs to the course section batch if applicable
        try:
            if self.assignment and self.assignment.course_section and hasattr(self.student, 'student_batch'):
                section_batch = getattr(self.assignment.course_section, 'student_batch_id', None)
                if section_batch and self.student.student_batch_id != section_batch:
                    raise ValidationError("Student is not part of the assignment's course section batch")
        except ValidationError:
            raise
        except Exception:
            # Avoid hard failures on legacy data paths
            pass
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


class AssignmentRubric(TimeStampedUUIDModel):
    """Model for assignment grading rubrics"""
    
    RUBRIC_TYPES = [
        ('ANALYTIC', 'Analytic Rubric'),
        ('HOLISTIC', 'Holistic Rubric'),
        ('CHECKLIST', 'Checklist Rubric'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    rubric_type = models.CharField(max_length=15, choices=RUBRIC_TYPES, default='ANALYTIC')
    criteria = models.JSONField(
        default=list,
        help_text="List of rubric criteria with descriptions and point values"
    )
    total_points = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignment_rubrics'
    )
    is_public = models.BooleanField(default=False, help_text="Available to all faculty")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AssignmentRubricGrade(TimeStampedUUIDModel):
    """Model for rubric-based grading"""
    
    submission = models.OneToOneField(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        related_name='rubric_grade'
    )
    rubric = models.ForeignKey(
        AssignmentRubric, 
        on_delete=models.CASCADE, 
        related_name='grades'
    )
    criteria_scores = models.JSONField(
        default=dict,
        help_text="Scores for each rubric criterion"
    )
    total_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='rubric_grades'
    )
    graded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-graded_at']
    
    def __str__(self):
        return f"{self.submission.student} - {self.rubric.name}: {self.total_score}"


class AssignmentPeerReview(TimeStampedUUIDModel):
    """Model for peer review assignments"""
    
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='peer_reviews'
    )
    reviewer = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='peer_reviews_given'
    )
    reviewee = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='peer_reviews_received'
    )
    submission = models.ForeignKey(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        related_name='peer_reviews'
    )
    
    # Peer Review Content
    content_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating for content quality (1-5)"
    )
    clarity_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating for clarity (1-5)"
    )
    creativity_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating for creativity (1-5)"
    )
    overall_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Overall rating (1-5)"
    )
    
    # Feedback
    strengths = models.TextField(help_text="What the student did well")
    improvements = models.TextField(help_text="Areas for improvement")
    additional_comments = models.TextField(blank=True, null=True)
    
    # Status
    is_completed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('assignment', 'reviewer', 'reviewee')
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.reviewer} reviews {self.reviewee} - {self.assignment.title}"


class AssignmentPlagiarismCheck(TimeStampedUUIDModel):
    """Model for plagiarism detection results"""
    
    PLAGIARISM_STATUS = [
        ('PENDING', 'Pending'),
        ('CLEAN', 'No Plagiarism Detected'),
        ('SUSPICIOUS', 'Suspicious Content'),
        ('PLAGIARIZED', 'Plagiarism Detected'),
    ]
    
    submission = models.OneToOneField(
        AssignmentSubmission, 
        on_delete=models.CASCADE, 
        related_name='plagiarism_check'
    )
    status = models.CharField(max_length=15, choices=PLAGIARISM_STATUS, default='PENDING')
    similarity_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Percentage of similarity detected"
    )
    sources = models.JSONField(
        default=list,
        help_text="List of potential sources with similarity percentages"
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='plagiarism_checks'
    )
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"{self.submission.student} - {self.status} ({self.similarity_percentage}%)"


class AssignmentLearningOutcome(TimeStampedUUIDModel):
    """Model for assignment learning outcomes"""
    
    BLOOM_TAXONOMY_LEVELS = [
        ('REMEMBER', 'Remember'),
        ('UNDERSTAND', 'Understand'),
        ('APPLY', 'Apply'),
        ('ANALYZE', 'Analyze'),
        ('EVALUATE', 'Evaluate'),
        ('CREATE', 'Create'),
    ]
    
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='learning_outcomes'
    )
    outcome_code = models.CharField(max_length=20, help_text="Learning outcome code (e.g., LO1, LO2)")
    description = models.TextField(help_text="Description of the learning outcome")
    bloom_level = models.CharField(max_length=15, choices=BLOOM_TAXONOMY_LEVELS)
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Weight of this outcome in the assignment (0-100)"
    )
    
    class Meta:
        ordering = ['outcome_code']
        unique_together = ('assignment', 'outcome_code')
    
    def __str__(self):
        return f"{self.assignment.title} - {self.outcome_code}"


class AssignmentAnalytics(TimeStampedUUIDModel):
    """Model for assignment analytics and insights"""
    
    assignment = models.OneToOneField(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='analytics'
    )
    
    # Submission Analytics
    total_expected_submissions = models.PositiveIntegerField(default=0)
    actual_submissions = models.PositiveIntegerField(default=0)
    submission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Submission rate percentage"
    )
    
    # Grade Analytics
    average_grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    median_grade = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    grade_distribution = models.JSONField(
        default=dict,
        help_text="Distribution of grades across different ranges"
    )
    
    # Time Analytics
    average_submission_time = models.DurationField(
        null=True, 
        blank=True,
        help_text="Average time taken to submit after assignment creation"
    )
    late_submission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage of late submissions"
    )
    
    # Learning Outcome Analytics
    outcome_achievement = models.JSONField(
        default=dict,
        help_text="Achievement rates for each learning outcome"
    )
    
    # Plagiarism Analytics
    plagiarism_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage of submissions flagged for plagiarism"
    )
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Analytics for {self.assignment.title}"


class AssignmentNotification(TimeStampedUUIDModel):
    """Model for assignment-related notifications"""
    
    NOTIFICATION_TYPES = [
        ('ASSIGNMENT_CREATED', 'Assignment Created'),
        ('ASSIGNMENT_DUE_SOON', 'Assignment Due Soon'),
        ('ASSIGNMENT_OVERDUE', 'Assignment Overdue'),
        ('SUBMISSION_RECEIVED', 'Submission Received'),
        ('GRADE_POSTED', 'Grade Posted'),
        ('FEEDBACK_POSTED', 'Feedback Posted'),
        ('PEER_REVIEW_ASSIGNED', 'Peer Review Assigned'),
        ('PLAGIARISM_DETECTED', 'Plagiarism Detected'),
    ]
    
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignment_notifications'
    )
    notification_type = models.CharField(max_length=25, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Additional context
    context_data = models.JSONField(
        default=dict,
        help_text="Additional context data for the notification"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} - {self.title}"


class AssignmentSchedule(TimeStampedUUIDModel):
    """Model for automated assignment scheduling"""
    
    SCHEDULE_TYPES = [
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('SEMESTER', 'Per Semester'),
        ('CUSTOM', 'Custom Interval'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    template = models.ForeignKey(
        AssignmentTemplate, 
        on_delete=models.CASCADE, 
        related_name='schedules'
    )
    schedule_type = models.CharField(max_length=15, choices=SCHEDULE_TYPES)
    interval_days = models.PositiveIntegerField(
        default=7, 
        help_text="Interval in days for custom schedules"
    )
    
    # Target Settings
    target_programs = models.ManyToManyField(
        'academics.AcademicProgram', 
        blank=True, 
        related_name='assignment_schedules'
    )
    target_departments = models.ManyToManyField(
        'departments.Department', 
        blank=True, 
        related_name='assignment_schedules'
    )
    target_courses = models.ManyToManyField(
        'academics.Course', 
        blank=True, 
        related_name='assignment_schedules'
    )
    
    # Schedule Settings
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignment_schedules'
    )
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
