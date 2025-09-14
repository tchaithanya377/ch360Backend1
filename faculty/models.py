import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomField(TimeStampedUUIDModel):
    """Model for creating custom fields dynamically"""
    
    FIELD_TYPE_CHOICES = [
        ('CHAR', 'Text'),
        ('TEXT', 'Long Text'),
        ('INTEGER', 'Number'),
        ('DECIMAL', 'Decimal Number'),
        ('DATE', 'Date'),
        ('DATETIME', 'Date & Time'),
        ('BOOLEAN', 'Yes/No'),
        ('EMAIL', 'Email'),
        ('URL', 'URL'),
        ('PHONE', 'Phone Number'),
        ('CHOICE', 'Choice Field'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    required = models.BooleanField(default=False)
    default_value = models.TextField(blank=True, null=True)
    choices = models.TextField(blank=True, null=True, help_text="Comma-separated choices for choice fields")
    help_text = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"


class CustomFieldValue(TimeStampedUUIDModel):
    """Model to store values for custom fields"""
    faculty = models.ForeignKey('Faculty', on_delete=models.CASCADE, related_name='custom_field_values')
    custom_field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('faculty', 'custom_field')


class Faculty(TimeStampedUUIDModel):
    """Faculty model for managing faculty information"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ON_LEAVE', 'On Leave'),
        ('RETIRED', 'Retired'),
        ('TERMINATED', 'Terminated'),
    ]
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('VISITING', 'Visiting'),
        ('ADJUNCT', 'Adjunct'),
    ]
    
    DESIGNATION_CHOICES = [
        ('PROFESSOR', 'Professor'),
        ('ASSOCIATE_PROFESSOR', 'Associate Professor'),
        ('ASSISTANT_PROFESSOR', 'Assistant Professor'),
        ('LECTURER', 'Lecturer'),
        ('INSTRUCTOR', 'Instructor'),
        ('HEAD_OF_DEPARTMENT', 'Head of Department'),
        ('DEAN', 'Dean'),
        ('PRINCIPAL', 'Principal'),
        ('VICE_PRINCIPAL', 'Vice Principal'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('COMPUTER_SCIENCE', 'Computer Science'),
        ('MATHEMATICS', 'Mathematics'),
        ('PHYSICS', 'Physics'),
        ('CHEMISTRY', 'Chemistry'),
        ('BIOLOGY', 'Biology'),
        ('ENGLISH', 'English'),
        ('HISTORY', 'History'),
        ('GEOGRAPHY', 'Geography'),
        ('ECONOMICS', 'Economics'),
        ('COMMERCE', 'Commerce'),
        ('PHYSICAL_EDUCATION', 'Physical Education'),
        ('ARTS', 'Arts'),
        ('MUSIC', 'Music'),
        ('ADMINISTRATION', 'Administration'),
        ('OTHER', 'Other'),
    ]
    
    NATURE_OF_ASSOCIATION_CHOICES = [
        ('REGULAR', 'Regular'),
        ('CONTRACT', 'Contract'),
        ('AD_HOC', 'Ad hoc'),
    ]
    
    CONTRACTUAL_TYPE_CHOICES = [
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
    ]
    
    # Basic Information (from table header)
    name = models.CharField(max_length=200, help_text="Name of the Faculty", default="")
    pan_no = models.CharField(max_length=10, blank=True, null=True, help_text="PAN Number")
    apaar_faculty_id = models.CharField(max_length=50, unique=True, help_text="APAAR Faculty ID", default="")
    
    # Academic Information
    highest_degree = models.CharField(max_length=100, help_text="Highest Degree", default="")
    university = models.CharField(max_length=200, blank=True, null=True, help_text="University")
    area_of_specialization = models.CharField(max_length=200, blank=True, null=True, help_text="Area of Specialization")
    
    # Employment Information
    date_of_joining_institution = models.DateField(help_text="Date of Joining in this Institution", default=timezone.now)
    designation_at_joining = models.CharField(max_length=100, help_text="Designation at Time of Joining in this Institution", default="")
    present_designation = models.CharField(max_length=100, help_text="Present Designation", default="")
    date_designated_as_professor = models.DateField(blank=True, null=True, help_text="Date designated as Professor/Associate Professor")
    
    # Association Details
    nature_of_association = models.CharField(max_length=20, choices=NATURE_OF_ASSOCIATION_CHOICES, help_text="Nature of Association", default="REGULAR")
    contractual_full_time_part_time = models.CharField(max_length=20, choices=CONTRACTUAL_TYPE_CHOICES, blank=True, null=True, help_text="If contractual mention Full time or Part time")
    currently_associated = models.BooleanField(default=True, help_text="Currently Associated (Y/N)")
    date_of_leaving = models.DateField(blank=True, null=True, help_text="Date of Leaving if any")
    experience_in_current_institute = models.DecimalField(max_digits=4, decimal_places=1, default=0.0, help_text="Experience in years in current institute")
    
    # Additional Standard Fields
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile', null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, help_text="Unique employee identifier", default="")
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(default=timezone.now)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    
    # Employment Information (Extended)
    designation = models.CharField(max_length=25, choices=DESIGNATION_CHOICES, default="LECTURER")
    department = models.CharField(max_length=25, choices=DEPARTMENT_CHOICES, default="OTHER")  # Keep for backward compatibility
    department_ref = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='faculty', help_text="Department reference")
    employment_type = models.CharField(max_length=15, choices=EMPLOYMENT_TYPE_CHOICES, default="FULL_TIME")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    date_of_joining = models.DateField(default=timezone.now)
    
    # Contact Information
    email = models.EmailField(unique=True, default="")
    phone_number = models.CharField(
        max_length=15,
        default="",
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    alternate_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    
    # Address Information
    address_line_1 = models.CharField(max_length=255, default="")
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, default="")
    state = models.CharField(max_length=100, default="")
    postal_code = models.CharField(max_length=10, default="")
    country = models.CharField(max_length=100, default='India')
    
    # Academic Information (Extended)
    highest_qualification = models.CharField(max_length=100, default="")
    specialization = models.CharField(max_length=200, blank=True, null=True)
    year_of_completion = models.IntegerField(blank=True, null=True)
    
    # Professional Information
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    previous_institution = models.CharField(max_length=200, blank=True, null=True)
    achievements = models.TextField(blank=True, null=True)
    research_interests = models.TextField(blank=True, null=True)
    
    # Administrative Information
    is_head_of_department = models.BooleanField(default=False)
    is_mentor = models.BooleanField(default=False)
    mentor_for_grades = models.CharField(max_length=50, blank=True, null=True, help_text="Comma-separated grade levels")
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100, default="")
    emergency_contact_phone = models.CharField(max_length=15, default="")
    emergency_contact_relationship = models.CharField(max_length=50, default="")
    
    # Additional Information
    profile_picture = models.ImageField(upload_to='faculty_profiles/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Faculty"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.apaar_faculty_id})"
    
    @property
    def full_name(self):
        """Return the full name of the faculty member"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active_faculty(self):
        """Check if faculty member is currently active"""
        return self.status == 'ACTIVE' and self.currently_associated
    
    def save(self, *args, **kwargs):
        """Override save to automatically generate user account if not exists"""
        if not self.user_id:
            # Generate username from APAAR Faculty ID
            username = f"faculty_{self.apaar_faculty_id}"
            
            # Create user account with default password
            user = User.objects.create_user(
                username=username,
                email=self.email,
                password='Campus@360',  # Default password
                is_active=True,
                is_staff=True,
            )
            self.user = user
        
        super().save(*args, **kwargs)


class FacultySubject(TimeStampedUUIDModel):
    """Model to track subjects taught by faculty members"""
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=10, help_text="e.g., Grade 1-12, College")
    academic_year = models.CharField(max_length=9, help_text="e.g., 2023-2024")
    is_primary_subject = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('faculty', 'subject_name', 'grade_level', 'academic_year')
    
    def __str__(self):
        return f"{self.faculty.name} - {self.subject_name} ({self.grade_level})"


class FacultySchedule(TimeStampedUUIDModel):
    """Model to track faculty schedules and timetables"""
    
    DAY_CHOICES = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
        ('SUNDAY', 'Sunday'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=10)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True, null=True)
    
    class Meta:
        unique_together = ('faculty', 'day_of_week', 'start_time', 'end_time')
    
    def __str__(self):
        return f"{self.faculty.name} - {self.subject} ({self.day_of_week})"


class FacultyLeave(TimeStampedUUIDModel):
    """Model to track faculty leave requests and approvals"""
    
    LEAVE_TYPE_CHOICES = [
        ('CASUAL', 'Casual Leave'),
        ('SICK', 'Sick Leave'),
        ('ANNUAL', 'Annual Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('STUDY', 'Study Leave'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.faculty.name} - {self.leave_type} ({self.start_date} to {self.end_date})"
    
    @property
    def leave_days(self):
        """Calculate the number of leave days"""
        # When adding via admin, dates can be empty before save; handle None safely
        if not self.start_date or not self.end_date:
            return 0
        delta_days = (self.end_date - self.start_date).days
        # Prevent negative values if end_date < start_date
        return delta_days + 1 if delta_days >= 0 else 0


class FacultyPerformance(TimeStampedUUIDModel):
    """Model to track faculty performance evaluations"""
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='performances')
    academic_year = models.CharField(max_length=9, help_text="e.g., 2023-2024")
    evaluation_period = models.CharField(max_length=50, help_text="e.g., Q1, Q2, Q3, Q4, Annual")
    
    # Evaluation Criteria
    teaching_effectiveness = models.DecimalField(max_digits=3, decimal_places=1, help_text="Score out of 10")
    student_satisfaction = models.DecimalField(max_digits=3, decimal_places=1, help_text="Score out of 10")
    research_contribution = models.DecimalField(max_digits=3, decimal_places=1, help_text="Score out of 10")
    administrative_work = models.DecimalField(max_digits=3, decimal_places=1, help_text="Score out of 10")
    professional_development = models.DecimalField(max_digits=3, decimal_places=1, help_text="Score out of 10")
    
    # Overall Assessment
    overall_score = models.DecimalField(max_digits=3, decimal_places=1, help_text="Overall performance score")
    strengths = models.TextField(blank=True, null=True)
    areas_for_improvement = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    
    # Evaluation Details
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='faculty_evaluations')
    evaluation_date = models.DateField()
    comments = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('faculty', 'academic_year', 'evaluation_period')
        ordering = ['-evaluation_date']
    
    def __str__(self):
        return f"{self.faculty.name} - {self.academic_year} {self.evaluation_period}"
    
    def save(self, *args, **kwargs):
        """Calculate overall score before saving"""
        if not self.overall_score:
            scores = [
                self.teaching_effectiveness,
                self.student_satisfaction,
                self.research_contribution,
                self.administrative_work,
                self.professional_development
            ]
            self.overall_score = sum(scores) / len(scores)
        super().save(*args, **kwargs)


class FacultyDocument(TimeStampedUUIDModel):
    """Model to store faculty documents and certificates"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('RESUME', 'Resume/CV'),
        ('DEGREE_CERTIFICATE', 'Degree Certificate'),
        ('EXPERIENCE_CERTIFICATE', 'Experience Certificate'),
        ('ID_PROOF', 'ID Proof'),
        ('ADDRESS_PROOF', 'Address Proof'),
        ('PHOTO', 'Photograph'),
        ('PAN_CARD', 'PAN Card'),
        ('AADHAR_CARD', 'Aadhar Card'),
        ('OTHER', 'Other'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=25, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='faculty_documents/')
    description = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.faculty.name} - {self.title}"
