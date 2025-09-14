"""
Core serializers for CampusHub360
Shared base serializers and utilities across all apps
"""

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import TimeStampedUUIDModel, CustomField, CustomFieldValue, BaseEntity, Document, Contact


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer with common functionality
    All serializers should inherit from this
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        abstract = True


class BaseListSerializer(BaseModelSerializer):
    """
    Lightweight serializer for list views
    Only includes essential fields for performance
    """
    class Meta:
        abstract = True
        fields = ['id', 'created_at', 'updated_at']


class BaseDetailSerializer(BaseModelSerializer):
    """
    Full serializer for detail views
    Includes all fields and related data
    """
    class Meta:
        abstract = True


class CustomFieldSerializer(BaseModelSerializer):
    """Serializer for Custom Field model"""
    
    class Meta:
        model = CustomField
        fields = [
            'id', 'name', 'label', 'field_type', 'required', 'help_text',
            'default_value', 'choices', 'validation_regex', 'min_value',
            'max_value', 'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomFieldValueSerializer(BaseModelSerializer):
    """Serializer for Custom Field Values"""
    custom_field = CustomFieldSerializer(read_only=True)
    custom_field_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = CustomFieldValue
        fields = [
            'id', 'custom_field', 'custom_field_id', 'value', 'file_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentSerializer(BaseModelSerializer):
    """Serializer for Document model"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.email', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.email', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'title', 'description', 'document_file',
            'is_verified', 'verified_by', 'verified_by_name', 'verified_at',
            'uploaded_by', 'uploaded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'verified_by', 'verified_at', 'created_at', 'updated_at']


class ContactSerializer(BaseModelSerializer):
    """Serializer for Contact model"""
    
    class Meta:
        model = Contact
        fields = [
            'id', 'contact_type', 'name', 'phone', 'email', 'relationship',
            'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BaseEntitySerializer(BaseModelSerializer):
    """
    Base serializer for entities (Student, Faculty, etc.)
    """
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        abstract = True
        fields = [
            'id', 'first_name', 'last_name', 'middle_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'email', 'mobile',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'full_address', 'status', 'user', 'created_by',
            'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'age', 'full_address']


class BaseEntityListSerializer(BaseListSerializer):
    """
    Lightweight serializer for entity list views
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        abstract = True
        fields = [
            'id', 'full_name', 'email', 'mobile', 'status', 'created_at'
        ]


class BaseEntityDetailSerializer(BaseDetailSerializer):
    """
    Detailed serializer for entity detail views
    """
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    documents = DocumentSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    custom_field_values = CustomFieldValueSerializer(many=True, read_only=True)
    
    class Meta:
        abstract = True
        fields = [
            'id', 'first_name', 'last_name', 'middle_name', 'full_name',
            'date_of_birth', 'age', 'gender', 'email', 'mobile',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code',
            'country', 'full_address', 'status', 'user', 'created_by',
            'updated_by', 'documents', 'contacts', 'custom_field_values',
            'created_at', 'updated_at'
        ]


class BulkOperationSerializer(serializers.Serializer):
    """
    Base serializer for bulk operations
    """
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of entity IDs for bulk operation"
    )
    
    def validate_ids(self, value):
        """Validate that IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one ID is required")
        return value


class SearchSerializer(serializers.Serializer):
    """
    Base serializer for search operations
    """
    query = serializers.CharField(max_length=255, help_text="Search query")
    filters = serializers.JSONField(required=False, help_text="Additional filters")
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20)
    
    def validate_query(self, value):
        """Validate search query"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Query must be at least 2 characters long")
        return value.strip()


class StatisticsSerializer(serializers.Serializer):
    """
    Base serializer for statistics responses
    """
    total_count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    inactive_count = serializers.IntegerField()
    created_today = serializers.IntegerField()
    created_this_week = serializers.IntegerField()
    created_this_month = serializers.IntegerField()
    distribution = serializers.JSONField(help_text="Distribution data (e.g., by department, status)")


class ExportSerializer(serializers.Serializer):
    """
    Base serializer for export operations
    """
    format = serializers.ChoiceField(choices=['csv', 'xlsx', 'json'], default='csv')
    filters = serializers.JSONField(required=False, help_text="Filters to apply")
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Specific fields to export"
    )
    include_related = serializers.BooleanField(default=False, help_text="Include related data")


class ImportSerializer(serializers.Serializer):
    """
    Base serializer for import operations
    """
    file = serializers.FileField(help_text="File to import")
    format = serializers.ChoiceField(choices=['csv', 'xlsx'], default='csv')
    skip_errors = serializers.BooleanField(default=False, help_text="Skip rows with errors")
    update_existing = serializers.BooleanField(default=False, help_text="Update existing records")
    create_users = serializers.BooleanField(default=True, help_text="Create user accounts")
    
    def validate_file(self, value):
        """Validate uploaded file"""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("File size cannot exceed 10MB")
        return value
