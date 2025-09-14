import uuid
from django.db import models
from django.conf import settings
try:
    from django.contrib.postgres.indexes import GinIndex
except Exception:
    GinIndex = None  # type: ignore
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


class AcademicYear(models.Model):
    """Academic year entity (e.g., 2024-2025)"""
    year = models.CharField(max_length=9, unique=True, help_text="e.g., 2024-2025")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return self.year


class Semester(models.Model):
    """Semester within an academic year"""
    SEMESTER_TYPES = [
        ('ODD', 'Odd Semester (Fall)'),
        ('EVEN', 'Even Semester (Spring)'),
        ('SUMMER', 'Summer Semester'),
    ]

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=50, help_text="e.g., Fall 2024, Spring 2025")
    semester_type = models.CharField(max_length=10, choices=SEMESTER_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('academic_year', 'semester_type')
        ordering = ['academic_year', 'semester_type']

    def __str__(self):
        return f"{self.name} ({self.academic_year.year})"


# Lookup tables for normalization
class Religion(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100, default='', blank=True, null=True, help_text="Display name for the religion")
    display_order = models.IntegerField(default=0, help_text="Order for display purposes")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        # Auto-populate display_name if not provided
        if not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Quota(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_name = models.CharField(max_length=100, help_text="Display name for the quota", default="")
    display_order = models.IntegerField(default=0, help_text="Order for display purposes")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_quotas')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_quotas')

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.display_name or self.name


class Caste(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, blank=True, null=True)  # SC, ST, OBC, etc.
    display_name = models.CharField(max_length=100, default='', help_text="Display name for the caste")
    display_order = models.IntegerField(default=0, help_text="Order for display purposes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_castes')

    class Meta:
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        # Auto-populate display_name if not provided
        if not self.display_name:
            self.display_name = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.name


class Student(TimeStampedUUIDModel):
    """Student model for managing student information"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('GRADUATED', 'Graduated'),
        ('SUSPENDED', 'Suspended'),
        ('DROPPED', 'Dropped Out'),
    ]
    
    YEAR_OF_STUDY_CHOICES = [
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4', '4th Year'),
        ('5', '5th Year'),
    ]
    
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
        ('9', 'Semester 9'),
        ('10', 'Semester 10'),
    ]
    
    SECTION_CHOICES = [
        ('A', 'Section A'),
        ('B', 'Section B'),
        ('C', 'Section C'),
        ('D', 'Section D'),
        ('E', 'Section E'),
        ('F', 'Section F'),
        ('G', 'Section G'),
        ('H', 'Section H'),
        ('I', 'Section I'),
        ('J', 'Section J'),
        ('K', 'Section K'),
        ('L', 'Section L'),
        ('M', 'Section M'),
        ('N', 'Section N'),
        ('O', 'Section O'),
        ('P', 'Section P'),
        ('Q', 'Section Q'),
        ('R', 'Section R'),
        ('S', 'Section S'),
        ('T', 'Section T'),
    ]
    
    # Basic Information (RollNumber equivalent to student_id)
    roll_number = models.CharField(
        max_length=20, 
        unique=True, 
        help_text="Unique roll number/student identifier"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Academic Information - Now managed through StudentBatch
    student_batch = models.ForeignKey(
        'StudentBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        help_text="Student's batch (contains department, program, year, semester, section)"
    )
    quota = models.ForeignKey(Quota, on_delete=models.SET_NULL, null=True, blank=True)
    rank = models.IntegerField(blank=True, null=True, help_text="Academic or admission rank")
    
    # Contact Information
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    student_mobile = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True,
        verbose_name="Student Mobile"
    )
    
    # Address Information (moved to StudentAddress for normalization)
    village = models.CharField(max_length=200, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    
    # Identity Information
    aadhar_number = models.CharField(
        max_length=12, 
        blank=True, 
        null=True,
        help_text="12-digit Aadhar number",
        validators=[
            RegexValidator(
                regex=r'^\d{12}$',
                message="Aadhar number must be exactly 12 digits."
            )
        ]
    )
    
    # Religious and Caste Information (normalized)
    religion = models.ForeignKey(Religion, on_delete=models.SET_NULL, null=True, blank=True)
    caste = models.ForeignKey(Caste, on_delete=models.SET_NULL, null=True, blank=True)
    subcaste = models.CharField(max_length=100, blank=True, null=True)
    
    # Parent Information (normalized via StudentContact)
    father_name = models.CharField(max_length=200, blank=True, null=True)
    mother_name = models.CharField(max_length=200, blank=True, null=True)
    father_mobile = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True,
        verbose_name="Father Mobile"
    )
    mother_mobile = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True,
        verbose_name="Mother Mobile"
    )
    
    # Academic Status
    enrollment_date = models.DateField(default=timezone.now)
    expected_graduation_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Guardian/Parent Information (Legacy fields for compatibility)
    guardian_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True
    )
    guardian_email = models.EmailField(blank=True, null=True)
    guardian_relationship = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="e.g., Father, Mother, Guardian, etc."
    )
    
    # Emergency Contact (normalized via StudentContact)
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True
    )
    emergency_contact_relationship = models.CharField(
        max_length=50, 
        blank=True, 
        null=True
    )
    
    # Medical Information
    medical_conditions = models.TextField(
        blank=True, 
        null=True,
        help_text="Any medical conditions or allergies"
    )
    medications = models.TextField(
        blank=True, 
        null=True,
        help_text="Current medications"
    )
    
    # Additional Information
    notes = models.TextField(blank=True, null=True, help_text="Additional notes about the student")
    profile_picture = models.ImageField(
        upload_to='student_profiles/', 
        blank=True, 
        null=True
    )
    
    # Linked auth user (created automatically)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile'
    )
    
    # System fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_students'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_students'
    )
    
    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        indexes = [
            models.Index(fields=['student_batch'], name='idx_student_batch'),
            models.Index(fields=['status'], name='idx_student_status_active', condition=models.Q(status='ACTIVE')),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        
    def __str__(self):
        return f"{self.roll_number} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Return the student's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate and return the student's age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def department(self):
        """Get department from student batch"""
        return self.student_batch.department if self.student_batch else None
    
    @property
    def academic_program(self):
        """Get academic program from student batch"""
        return self.student_batch.academic_program if self.student_batch else None
    
    @property
    def academic_year(self):
        """Get academic year from student batch"""
        return self.student_batch.academic_year.year if self.student_batch and self.student_batch.academic_year else None
    
    @property
    def semester(self):
        """Get semester from student batch"""
        return self.student_batch.semester if self.student_batch else None
    
    @property
    def year_of_study(self):
        """Get year of study from student batch"""
        return self.student_batch.year_of_study if self.student_batch else None
    
    @property
    def section(self):
        """Get section from student batch"""
        return self.student_batch.section if self.student_batch else None
    
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


class StudentBatch(models.Model):
    """Enhanced grouping of students by department, academic year, year of study and section"""
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        related_name='student_batches'
    )
    academic_program = models.ForeignKey(
        'academics.AcademicProgram',
        on_delete=models.CASCADE,
        related_name='student_batches',
        null=True,
        blank=True
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='student_batches'
    )
    # TODO: Re-enable this ForeignKey field after proper migration
    # semester = models.ForeignKey(
    #     Semester,
    #     on_delete=models.CASCADE,
    #     related_name='student_batches',
    #     null=True,
    #     blank=True
    # )
    semester = models.CharField(max_length=2, choices=Student.SEMESTER_CHOICES, default='1')
    year_of_study = models.CharField(max_length=1, choices=Student.YEAR_OF_STUDY_CHOICES)
    section = models.CharField(max_length=1, choices=Student.SECTION_CHOICES)
    batch_name = models.CharField(max_length=100, help_text="e.g., CS-2024-1-A")
    batch_code = models.CharField(max_length=50, unique=True, help_text="Unique batch code")
    max_capacity = models.PositiveIntegerField(default=70, help_text="Maximum students per batch")
    current_count = models.PositiveIntegerField(default=0, help_text="Current student count")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_batches'
    )

    class Meta:
        unique_together = ('department', 'academic_year', 'year_of_study', 'section')
        ordering = ['department', 'academic_year__year', 'year_of_study', 'section']
        verbose_name = 'Student Batch'
        verbose_name_plural = 'Student Batches'

    def __str__(self):
        return self.batch_name
    
    def get_available_capacity(self):
        """Get available capacity in this batch"""
        return self.max_capacity - self.current_count
    
    def is_full(self):
        """Check if batch is at capacity"""
        return self.current_count >= self.max_capacity
    
    def can_add_students(self, count=1):
        """Check if batch can accommodate additional students"""
        return (self.current_count + count) <= self.max_capacity
    
    def get_semester_object(self):
        """Get the Semester object based on the semester string and academic year"""
        if not self.semester or not self.academic_year:
            return None
        
        # Map semester string to semester type
        semester_mapping = {
            '1': 'ODD',
            '2': 'EVEN',
            '3': 'SUMMER',
        }
        
        semester_type = semester_mapping.get(self.semester)
        if not semester_type:
            return None
            
        try:
            return Semester.objects.get(
                academic_year=self.academic_year,
                semester_type=semester_type,
                is_active=True
            )
        except Semester.DoesNotExist:
            return None
    
    def set_semester_from_object(self, semester_obj):
        """Set the semester string based on a Semester object"""
        if not semester_obj:
            return
            
        # Map semester type to semester string
        type_mapping = {
            'ODD': '1',
            'EVEN': '2', 
            'SUMMER': '3',
        }
        
        self.semester = type_mapping.get(semester_obj.semester_type, '1')
    
    @property
    def semester_name(self):
        """Get the semester name from the linked Semester object"""
        semester_obj = self.get_semester_object()
        return semester_obj.name if semester_obj else f"Semester {self.semester}"
    
    @property
    def semester_type(self):
        """Get the semester type from the linked Semester object"""
        semester_obj = self.get_semester_object()
        return semester_obj.semester_type if semester_obj else None
    
    @property
    def semester_start_date(self):
        """Get the semester start date from the linked Semester object"""
        semester_obj = self.get_semester_object()
        return semester_obj.start_date if semester_obj else None
    
    @property
    def semester_end_date(self):
        """Get the semester end date from the linked Semester object"""
        semester_obj = self.get_semester_object()
        return semester_obj.end_date if semester_obj else None
    
    @property
    def semester_is_current(self):
        """Get whether the semester is current from the linked Semester object"""
        semester_obj = self.get_semester_object()
        return semester_obj.is_current if semester_obj else False

    def update_student_count(self):
        """Update current student count from actual students"""
        from django.db.models import Count
        count = Student.objects.filter(
            student_batch=self,
            status='ACTIVE'
        ).count()
        self.current_count = count
        self.save(update_fields=['current_count'])


class StudentContact(TimeStampedUUIDModel):
    """Normalized contacts for a student (parent/guardian/emergency/self)."""
    CONTACT_TYPE_CHOICES = [
        ('SELF', 'Self'),
        ('FATHER', 'Father'),
        ('MOTHER', 'Mother'),
        ('GUARDIAN', 'Guardian'),
        ('EMERGENCY', 'Emergency'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")], max_length=17, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    relationship = models.CharField(max_length=50, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'contact_type', 'is_primary')
        indexes = [
            models.Index(fields=['student', 'contact_type']),
        ]


class StudentAddress(TimeStampedUUIDModel):
    """Normalized addresses for a student with address type."""
    ADDRESS_TYPE_CHOICES = [
        ('CURRENT', 'Current'),
        ('PERMANENT', 'Permanent'),
        ('MAILING', 'Mailing'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    is_primary = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'address_type', 'is_primary')
        indexes = [
            models.Index(fields=['student', 'address_type']),
        ]


class StudentIdentifierType(models.TextChoices):
    AADHAR = 'AADHAR', 'Aadhar'
    OTHER = 'OTHER', 'Other'


class StudentIdentifier(TimeStampedUUIDModel):
    """Normalized identifiers for students (e.g., Aadhar)."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='identifiers')
    id_type = models.CharField(max_length=20, choices=StudentIdentifierType.choices)
    identifier = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('id_type', 'identifier')
        indexes = [
            models.Index(fields=['student', 'id_type', 'is_primary']),
        ]


class StudentEnrollmentHistory(TimeStampedUUIDModel):
    """Track student enrollment history"""
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='enrollment_history'
    )
    year_of_study = models.CharField(max_length=1, choices=Student.YEAR_OF_STUDY_CHOICES, default='1')
    semester = models.CharField(max_length=2, choices=Student.SEMESTER_CHOICES, default='1')
    academic_year = models.CharField(max_length=9, help_text="e.g., 2023-2024")
    enrollment_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Student.STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-enrollment_date']
        verbose_name = 'Student Enrollment History'
        verbose_name_plural = 'Student Enrollment Histories'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.year_of_study} Year, Sem {self.semester} ({self.academic_year})"


class StudentDocument(TimeStampedUUIDModel):
    """Store student-related documents"""
    
    DOCUMENT_TYPES = [
        ('BIRTH_CERT', 'Birth Certificate'),
        ('TRANSCRIPT', 'Academic Transcript'),
        ('MEDICAL', 'Medical Record'),
        ('IMMUNIZATION', 'Immunization Record'),
        ('PHOTO_ID', 'Photo ID'),
        ('OTHER', 'Other'),
    ]
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    document_file = models.FileField(upload_to='student_documents/')
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Document'
        verbose_name_plural = 'Student Documents'
        indexes = [
            models.Index(fields=['document_type', 'student']),
        ]
    
    def __str__(self):
        return f"{self.student.full_name} - {self.title}"


class CustomFieldType(models.TextChoices):
    """Types of custom fields that can be created"""
    TEXT = 'text', 'Text'
    NUMBER = 'number', 'Number'
    DATE = 'date', 'Date'
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    SELECT = 'select', 'Select (Dropdown)'
    MULTISELECT = 'multiselect', 'Multi-Select'
    BOOLEAN = 'boolean', 'Yes/No'
    TEXTAREA = 'textarea', 'Long Text'
    FILE = 'file', 'File Upload'
    URL = 'url', 'URL'


class CustomField(TimeStampedUUIDModel):
    """Model for creating custom fields for students"""
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=CustomFieldType.choices)
    required = models.BooleanField(default=False)
    help_text = models.TextField(blank=True, null=True)
    default_value = models.TextField(blank=True, null=True)
    choices = models.JSONField(blank=True, null=True, help_text="For select/multiselect fields, provide options as JSON array")
    validation_regex = models.CharField(max_length=200, blank=True, null=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Custom Field'
        verbose_name_plural = 'Custom Fields'
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"


class StudentCustomFieldValue(TimeStampedUUIDModel):
    """Model for storing custom field values for each student"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='custom_field_values')
    custom_field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='student_values')
    value = models.TextField(blank=True, null=True)
    file_value = models.FileField(upload_to='student_custom_files/', blank=True, null=True)
    
    class Meta:
        unique_together = ('student', 'custom_field')
        verbose_name = 'Student Custom Field Value'
        verbose_name_plural = 'Student Custom Field Values'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.custom_field.label}: {self.value}"


class StudentImport(TimeStampedUUIDModel):
    """Model to track student import history"""
    
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    total_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    
    # Import options
    skip_errors = models.BooleanField(default=False)
    create_login = models.BooleanField(default=True)
    update_existing = models.BooleanField(default=False)
    
    # Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Error details (stored as JSON)
    errors = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    
    # User who performed the import
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='student_imports'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Import'
        verbose_name_plural = 'Student Imports'
    
    def __str__(self):
        return f"{self.filename} - {self.status} ({self.success_count} imported)"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_rows == 0:
            return 0
        return round((self.success_count / self.total_rows) * 100, 2)


class BulkAssignment(TimeStampedUUIDModel):
    """Model to track bulk assignment operations"""
    
    OPERATION_TYPES = [
        ('ASSIGN_DEPARTMENT', 'Assign Department'),
        ('ASSIGN_PROGRAM', 'Assign Academic Program'),
        ('ASSIGN_YEAR', 'Assign Academic Year'),
        ('ASSIGN_SEMESTER', 'Assign Semester'),
        ('ASSIGN_SECTION', 'Assign Section'),
        ('PROMOTE_YEAR', 'Promote to Next Year'),
        ('TRANSFER_BATCH', 'Transfer to Different Batch'),
        ('CUSTOM', 'Custom Assignment'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partially Completed'),
    ]
    
    # Operation details
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    title = models.CharField(max_length=200, help_text="Operation title")
    description = models.TextField(blank=True, null=True, help_text="Operation description")
    
    # Criteria for selecting students
    criteria = models.JSONField(default=dict, help_text="Selection criteria")
    
    # Assignment details
    assignment_data = models.JSONField(default=dict, help_text="Assignment data")
    
    # Results
    total_students_found = models.PositiveIntegerField(default=0)
    students_updated = models.PositiveIntegerField(default=0)
    students_failed = models.PositiveIntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User who performed the operation
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bulk_assignments'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bulk Assignment'
        verbose_name_plural = 'Bulk Assignments'
    
    def __str__(self):
        return f"{self.title} - {self.status} ({self.students_updated} updated)"
    
    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        if self.total_students_found == 0:
            return 0
        return round((self.students_updated / self.total_students_found) * 100, 2)
    
    @property
    def duration(self):
        """Calculate operation duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
