import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
    """Abstract base model with UUID primary key and timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Department(TimeStampedUUIDModel):
    """Enhanced Department model for comprehensive university department management"""
    
    DEPARTMENT_TYPES = [
        ('ACADEMIC', 'Academic Department'),
        ('ADMINISTRATIVE', 'Administrative Department'),
        ('RESEARCH', 'Research Department'),
        ('SERVICE', 'Service Department'),
        ('SUPPORT', 'Support Department'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('MERGED', 'Merged'),
        ('DISSOLVED', 'Dissolved'),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200, 
        unique=True, 
        help_text="Full department name"
    )
    short_name = models.CharField(
        max_length=50, 
        unique=True, 
        help_text="Short name or abbreviation (e.g., CS, ME, EE)"
    )
    code = models.CharField(
        max_length=10, 
        unique=True, 
        help_text="Department code for system use (e.g., CS001, ME002)"
    )
    
    # Department Classification
    department_type = models.CharField(
        max_length=20, 
        choices=DEPARTMENT_TYPES, 
        default='ACADEMIC',
        help_text="Type of department"
    )
    parent_department = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='sub_departments',
        help_text="Parent department if this is a sub-department"
    )
    
    # Leadership and Management
    head_of_department = models.ForeignKey(
        'faculty.Faculty', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='headed_departments_new',
        help_text="Current head of department"
    )
    deputy_head = models.ForeignKey(
        'faculty.Faculty', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='deputy_headed_departments_new',
        help_text="Deputy head of department"
    )
    
    # Contact Information
    email = models.EmailField(
        help_text="Department email address"
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        help_text="Department phone number"
    )
    fax = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True,
        help_text="Department fax number"
    )
    
    # Location Information
    building = models.CharField(
        max_length=100, 
        help_text="Building name or number"
    )
    floor = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Floor number or name"
    )
    room_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Room number"
    )
    address_line1 = models.CharField(
        max_length=255, 
        blank=True,
        null=True,
        help_text="Address line 1"
    )
    address_line2 = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Address line 2"
    )
    city = models.CharField(
        max_length=100, 
        blank=True,
        null=True
    )
    state = models.CharField(
        max_length=100, 
        blank=True,
        null=True
    )
    postal_code = models.CharField(
        max_length=20, 
        blank=True,
        null=True
    )
    country = models.CharField(
        max_length=100, 
        blank=True,
        null=True
    )
    
    # Academic Information
    established_date = models.DateField(
        help_text="Date when department was established"
    )
    accreditation_status = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Accreditation status (e.g., NAAC, NBA)"
    )
    accreditation_valid_until = models.DateField(
        blank=True, 
        null=True,
        help_text="Accreditation valid until date"
    )
    
    # Department Details
    description = models.TextField(
        help_text="Department description and overview"
    )
    mission = models.TextField(
        blank=True, 
        null=True,
        help_text="Department mission statement"
    )
    vision = models.TextField(
        blank=True, 
        null=True,
        help_text="Department vision statement"
    )
    objectives = models.TextField(
        blank=True, 
        null=True,
        help_text="Department objectives"
    )
    
    # Capacity and Resources
    max_faculty_capacity = models.PositiveIntegerField(
        default=50, 
        help_text="Maximum faculty capacity"
    )
    max_student_capacity = models.PositiveIntegerField(
        default=500, 
        help_text="Maximum student capacity"
    )
    current_faculty_count = models.PositiveIntegerField(
        default=0, 
        help_text="Current faculty count"
    )
    current_student_count = models.PositiveIntegerField(
        default=0, 
        help_text="Current student count"
    )
    
    # Financial Information
    annual_budget = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Annual budget in local currency"
    )
    budget_year = models.CharField(
        max_length=9, 
        blank=True, 
        null=True,
        help_text="Budget year (e.g., 2024-2025)"
    )
    
    # Status and Metadata
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE'
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether department is currently active"
    )
    
    # Additional Information
    website_url = models.URLField(
        blank=True, 
        null=True,
        help_text="Department website URL"
    )
    social_media_links = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Social media links (JSON format)"
    )
    logo = models.ImageField(
        upload_to='department_logos/', 
        blank=True, 
        null=True,
        help_text="Department logo"
    )
    
    # System fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_departments'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_departments'
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['short_name']),
            models.Index(fields=['department_type']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Validate department data"""
        super().clean()
        
        # Validate parent department
        if self.parent_department and self.parent_department == self:
            raise ValidationError("Department cannot be its own parent")
        
        # Validate capacity
        if self.current_faculty_count > self.max_faculty_capacity:
            raise ValidationError("Current faculty count cannot exceed maximum capacity")
        
        if self.current_student_count > self.max_student_capacity:
            raise ValidationError("Current student count cannot exceed maximum capacity")
    
    def save(self, *args, **kwargs):
        """Override save to perform validation and auto-update counts"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        """Return the full address as a string"""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    @property
    def faculty_utilization_percentage(self):
        """Calculate faculty utilization percentage"""
        if self.max_faculty_capacity == 0:
            return 0
        return round((self.current_faculty_count / self.max_faculty_capacity) * 100, 2)
    
    @property
    def student_utilization_percentage(self):
        """Calculate student utilization percentage"""
        if self.max_student_capacity == 0:
            return 0
        return round((self.current_student_count / self.max_student_capacity) * 100, 2)
    
    def get_faculty_count(self):
        """Get actual faculty count from related faculty"""
        return self.faculty.filter(status='ACTIVE').count()
    
    def get_student_count(self):
        """Get actual student count from related students through student batches"""
        from students.models import Student
        return Student.objects.filter(
            student_batch__department=self,
            status='ACTIVE'
        ).count()
    
    def update_counts(self):
        """Update current counts from related objects"""
        self.current_faculty_count = self.get_faculty_count()
        self.current_student_count = self.get_student_count()
        self.save(update_fields=['current_faculty_count', 'current_student_count'])


"""DepartmentProgram removed. Consolidated into academics.AcademicProgram."""


class DepartmentResource(TimeStampedUUIDModel):
    """Model for department resources and facilities"""
    
    RESOURCE_TYPES = [
        ('LABORATORY', 'Laboratory'),
        ('LIBRARY', 'Library'),
        ('EQUIPMENT', 'Equipment'),
        ('SOFTWARE', 'Software'),
        ('FACILITY', 'Facility'),
        ('VEHICLE', 'Vehicle'),
        ('OTHER', 'Other'),
    ]
    
    RESOURCE_STATUS = [
        ('AVAILABLE', 'Available'),
        ('IN_USE', 'In Use'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('OUT_OF_ORDER', 'Out of Order'),
        ('RETIRED', 'Retired'),
    ]
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='resources'
    )
    name = models.CharField(
        max_length=200, 
        help_text="Resource name"
    )
    resource_type = models.CharField(
        max_length=20, 
        choices=RESOURCE_TYPES
    )
    description = models.TextField(
        help_text="Resource description"
    )
    location = models.CharField(
        max_length=200, 
        help_text="Resource location"
    )
    status = models.CharField(
        max_length=20, 
        choices=RESOURCE_STATUS, 
        default='AVAILABLE'
    )
    purchase_date = models.DateField(
        blank=True, 
        null=True,
        help_text="Date when resource was purchased"
    )
    warranty_expiry = models.DateField(
        blank=True, 
        null=True,
        help_text="Warranty expiry date"
    )
    maintenance_schedule = models.TextField(
        blank=True, 
        null=True,
        help_text="Maintenance schedule"
    )
    responsible_person = models.ForeignKey(
        'faculty.Faculty', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Person responsible for this resource"
    )
    cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Resource cost"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Department Resource"
        verbose_name_plural = "Department Resources"
    
    def __str__(self):
        return f"{self.department.short_name} - {self.name}"


class DepartmentAnnouncement(TimeStampedUUIDModel):
    """Model for department announcements and notices"""
    
    ANNOUNCEMENT_TYPES = [
        ('GENERAL', 'General'),
        ('ACADEMIC', 'Academic'),
        ('EVENT', 'Event'),
        ('DEADLINE', 'Deadline'),
        ('EMERGENCY', 'Emergency'),
        ('MAINTENANCE', 'Maintenance'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='announcements'
    )
    title = models.CharField(
        max_length=200, 
        help_text="Announcement title"
    )
    content = models.TextField(
        help_text="Announcement content"
    )
    announcement_type = models.CharField(
        max_length=20, 
        choices=ANNOUNCEMENT_TYPES, 
        default='GENERAL'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_LEVELS, 
        default='MEDIUM'
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether announcement is published"
    )
    publish_date = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Date when announcement was published"
    )
    expiry_date = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Date when announcement expires"
    )
    target_audience = models.CharField(
        max_length=100, 
        default='ALL',
        help_text="Target audience (ALL, FACULTY, STUDENTS, etc.)"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_announcements'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Department Announcement"
        verbose_name_plural = "Department Announcements"
    
    def __str__(self):
        return f"{self.department.short_name} - {self.title}"
    
    def save(self, *args, **kwargs):
        """Override save to set publish_date when published"""
        if self.is_published and not self.publish_date:
            self.publish_date = timezone.now()
        super().save(*args, **kwargs)


class DepartmentEvent(TimeStampedUUIDModel):
    """Model for department events and activities"""
    
    EVENT_TYPES = [
        ('SEMINAR', 'Seminar'),
        ('WORKSHOP', 'Workshop'),
        ('CONFERENCE', 'Conference'),
        ('MEETING', 'Meeting'),
        ('CELEBRATION', 'Celebration'),
        ('COMPETITION', 'Competition'),
        ('EXHIBITION', 'Exhibition'),
        ('OTHER', 'Other'),
    ]
    
    EVENT_STATUS = [
        ('PLANNED', 'Planned'),
        ('CONFIRMED', 'Confirmed'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('POSTPONED', 'Postponed'),
    ]
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='events'
    )
    title = models.CharField(
        max_length=200, 
        help_text="Event title"
    )
    description = models.TextField(
        help_text="Event description"
    )
    event_type = models.CharField(
        max_length=20, 
        choices=EVENT_TYPES
    )
    start_date = models.DateTimeField(
        help_text="Event start date and time"
    )
    end_date = models.DateTimeField(
        help_text="Event end date and time"
    )
    location = models.CharField(
        max_length=200, 
        help_text="Event location"
    )
    status = models.CharField(
        max_length=20, 
        choices=EVENT_STATUS, 
        default='PLANNED'
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether event is public"
    )
    max_attendees = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Maximum number of attendees"
    )
    registration_required = models.BooleanField(
        default=False,
        help_text="Whether registration is required"
    )
    registration_deadline = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Registration deadline"
    )
    organizer = models.ForeignKey(
        'faculty.Faculty', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Event organizer"
    )
    contact_email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Contact email for event"
    )
    contact_phone = models.CharField(
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$', 
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )], 
        max_length=17, 
        blank=True, 
        null=True,
        help_text="Contact phone for event"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_events'
    )
    
    class Meta:
        ordering = ['start_date']
        verbose_name = "Department Event"
        verbose_name_plural = "Department Events"
    
    def __str__(self):
        return f"{self.department.short_name} - {self.title}"
    
    def clean(self):
        """Validate event data"""
        super().clean()
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")
    
    @property
    def duration_hours(self):
        """Calculate event duration in hours"""
        if not self.start_date or not self.end_date:
            return 0
        duration = self.end_date - self.start_date
        return duration.total_seconds() / 3600


class DepartmentDocument(TimeStampedUUIDModel):
    """Model for department documents and files"""
    
    DOCUMENT_TYPES = [
        ('POLICY', 'Policy Document'),
        ('PROCEDURE', 'Procedure Document'),
        ('FORM', 'Form'),
        ('REPORT', 'Report'),
        ('MANUAL', 'Manual'),
        ('GUIDELINE', 'Guideline'),
        ('CERTIFICATE', 'Certificate'),
        ('OTHER', 'Other'),
    ]
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    title = models.CharField(
        max_length=200, 
        help_text="Document title"
    )
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPES
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Document description"
    )
    file = models.FileField(
        upload_to='department_documents/',
        help_text="Document file"
    )
    version = models.CharField(
        max_length=20, 
        default='1.0',
        help_text="Document version"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Whether document is public"
    )
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='uploaded_documents'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Department Document"
        verbose_name_plural = "Department Documents"
    
    def __str__(self):
        return f"{self.department.short_name} - {self.title}"