"""
Core models for CampusHub360
Shared base models and utilities across all apps
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.validators import RegexValidator

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps
    Used across all apps to maintain consistency
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomFieldType(models.TextChoices):
    """Unified custom field types for all apps"""
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
    """
    Unified custom field model for all apps
    Replaces duplicate CustomField models across students, faculty, etc.
    """
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
        indexes = [
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['field_type']),
        ]
    
    def __str__(self):
        return f"{self.label} ({self.get_field_type_display()})"


class CustomFieldValue(TimeStampedUUIDModel):
    """
    Generic custom field value model
    Uses content_type to link to any model (Student, Faculty, etc.)
    """
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    custom_field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='values')
    value = models.TextField(blank=True, null=True)
    file_value = models.FileField(upload_to='custom_field_files/', blank=True, null=True)
    
    class Meta:
        unique_together = ('content_type', 'object_id', 'custom_field')
        verbose_name = 'Custom Field Value'
        verbose_name_plural = 'Custom Field Values'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['custom_field']),
        ]
    
    def __str__(self):
        return f"{self.content_object} - {self.custom_field.label}: {self.value}"


class BaseEntity(TimeStampedUUIDModel):
    """
    Base entity model with common fields for Student, Faculty, etc.
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Contact Information
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$', 
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    mobile = models.CharField(
        validators=[phone_regex], 
        max_length=17, 
        blank=True, 
        null=True
    )
    
    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='India')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Linked auth user
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_profile'
    )
    
    # System fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_%(class)ss'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_%(class)ss'
    )
    
    class Meta:
        abstract = True
    
    @property
    def full_name(self):
        """Return the full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate and return the age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
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


class Document(TimeStampedUUIDModel):
    """
    Generic document model for all entities
    """
    DOCUMENT_TYPES = [
        ('BIRTH_CERT', 'Birth Certificate'),
        ('TRANSCRIPT', 'Academic Transcript'),
        ('MEDICAL', 'Medical Record'),
        ('IMMUNIZATION', 'Immunization Record'),
        ('PHOTO_ID', 'Photo ID'),
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
    
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    document_type = models.CharField(max_length=25, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    document_file = models.FileField(upload_to='documents/')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='core_verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='core_uploaded_documents'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['document_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.content_object} - {self.title}"


class Contact(TimeStampedUUIDModel):
    """
    Generic contact model for all entities
    """
    CONTACT_TYPE_CHOICES = [
        ('SELF', 'Self'),
        ('FATHER', 'Father'),
        ('MOTHER', 'Mother'),
        ('GUARDIAN', 'Guardian'),
        ('EMERGENCY', 'Emergency'),
        ('SPOUSE', 'Spouse'),
        ('SIBLING', 'Sibling'),
        ('OTHER', 'Other'),
    ]
    
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$', 
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )], 
        max_length=17, 
        blank=True, 
        null=True
    )
    email = models.EmailField(blank=True, null=True)
    relationship = models.CharField(max_length=50, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('content_type', 'object_id', 'contact_type', 'is_primary')
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['contact_type']),
        ]
    
    def __str__(self):
        return f"{self.content_object} - {self.get_contact_type_display()}: {self.name or self.phone}"
