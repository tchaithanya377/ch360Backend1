from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Department, DepartmentResource, 
    DepartmentAnnouncement, DepartmentEvent, DepartmentDocument
)

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    
    # Computed fields
    full_address = serializers.ReadOnlyField()
    faculty_utilization_percentage = serializers.ReadOnlyField()
    student_utilization_percentage = serializers.ReadOnlyField()
    
    # Related field representations
    head_of_department_name = serializers.CharField(
        source='head_of_department.name', 
        read_only=True
    )
    deputy_head_name = serializers.CharField(
        source='deputy_head.name', 
        read_only=True
    )
    parent_department_name = serializers.CharField(
        source='parent_department.name', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True
    )
    updated_by_name = serializers.CharField(
        source='updated_by.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'short_name', 'code', 'department_type', 
            'parent_department', 'parent_department_name',
            'head_of_department', 'head_of_department_name',
            'deputy_head', 'deputy_head_name',
            'email', 'phone', 'fax',
            'building', 'floor', 'room_number',
            'address_line1', 'address_line2', 'city', 'state', 
            'postal_code', 'country', 'full_address',
            'established_date', 'accreditation_status', 
            'accreditation_valid_until',
            'description', 'mission', 'vision', 'objectives',
            'max_faculty_capacity', 'max_student_capacity',
            'current_faculty_count', 'current_student_count',
            'faculty_utilization_percentage', 'student_utilization_percentage',
            'annual_budget', 'budget_year',
            'status', 'is_active',
            'website_url', 'social_media_links', 'logo',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'current_faculty_count', 
            'current_student_count', 'faculty_utilization_percentage', 
            'student_utilization_percentage'
        ]
    
    def validate_code(self, value):
        """Validate department code format"""
        if not value.isalnum():
            raise serializers.ValidationError(
                "Department code must contain only alphanumeric characters."
            )
        return value.upper()
    
    def validate_short_name(self, value):
        """Validate short name format"""
        return value.upper()
    
    def validate(self, data):
        """Cross-field validation"""
        # Validate parent department
        if data.get('parent_department') and data.get('parent_department') == self.instance:
            raise serializers.ValidationError(
                "Department cannot be its own parent."
            )
        
        # Validate capacity
        if data.get('current_faculty_count', 0) > data.get('max_faculty_capacity', 0):
            raise serializers.ValidationError(
                "Current faculty count cannot exceed maximum capacity."
            )
        
        if data.get('current_student_count', 0) > data.get('max_student_capacity', 0):
            raise serializers.ValidationError(
                "Current student count cannot exceed maximum capacity."
            )
        
        return data


class DepartmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for department lists"""
    
    head_of_department_name = serializers.CharField(
        source='head_of_department.name', 
        read_only=True
    )
    faculty_utilization_percentage = serializers.ReadOnlyField()
    student_utilization_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'short_name', 'code', 'department_type',
            'head_of_department_name', 'email', 'phone',
            'current_faculty_count', 'current_student_count',
            'faculty_utilization_percentage', 'student_utilization_percentage',
            'status', 'is_active', 'created_at'
        ]


class DepartmentResourceSerializer(serializers.ModelSerializer):
    """Serializer for DepartmentResource model"""
    
    department_name = serializers.CharField(
        source='department.name', 
        read_only=True
    )
    responsible_person_name = serializers.CharField(
        source='responsible_person.name', 
        read_only=True
    )
    
    class Meta:
        model = DepartmentResource
        fields = [
            'id', 'department', 'department_name', 'name', 'resource_type',
            'description', 'location', 'status', 'purchase_date',
            'warranty_expiry', 'maintenance_schedule', 'responsible_person',
            'responsible_person_name', 'cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DepartmentAnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for DepartmentAnnouncement model"""
    
    department_name = serializers.CharField(
        source='department.name', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = DepartmentAnnouncement
        fields = [
            'id', 'department', 'department_name', 'title', 'content',
            'announcement_type', 'priority', 'is_published', 'publish_date',
            'expiry_date', 'target_audience', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'publish_date']


class DepartmentEventSerializer(serializers.ModelSerializer):
    """Serializer for DepartmentEvent model"""
    
    department_name = serializers.CharField(
        source='department.name', 
        read_only=True
    )
    organizer_name = serializers.CharField(
        source='organizer.name', 
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', 
        read_only=True
    )
    duration_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = DepartmentEvent
        fields = [
            'id', 'department', 'department_name', 'title', 'description',
            'event_type', 'start_date', 'end_date', 'location', 'status',
            'is_public', 'max_attendees', 'registration_required',
            'registration_deadline', 'organizer', 'organizer_name',
            'contact_email', 'contact_phone', 'created_by', 'created_by_name',
            'duration_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'duration_hours']
    
    def validate(self, data):
        """Cross-field validation"""
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after start date."
                )
        return data


class DepartmentDocumentSerializer(serializers.ModelSerializer):
    """Serializer for DepartmentDocument model"""
    
    department_name = serializers.CharField(
        source='department.name', 
        read_only=True
    )
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name', 
        read_only=True
    )
    file_size = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DepartmentDocument
        fields = [
            'id', 'department', 'department_name', 'title', 'document_type',
            'description', 'file', 'file_url', 'file_size', 'version',
            'is_public', 'uploaded_by', 'uploaded_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'file_size', 'file_url'
        ]
    
    def get_file_size(self, obj):
        """Get file size in bytes"""
        if obj.file:
            try:
                return obj.file.size
            except (OSError, ValueError):
                return None
        return None
    
    def get_file_url(self, obj):
        """Get file URL"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DepartmentDetailSerializer(DepartmentSerializer):
    """Detailed serializer for Department with related objects"""
    
    resources = DepartmentResourceSerializer(many=True, read_only=True)
    announcements = DepartmentAnnouncementSerializer(many=True, read_only=True)
    events = DepartmentEventSerializer(many=True, read_only=True)
    documents = DepartmentDocumentSerializer(many=True, read_only=True)
    
    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + [
            'resources', 'announcements', 'events', 'documents'
        ]


class DepartmentStatsSerializer(serializers.Serializer):
    """Serializer for department statistics"""
    
    total_departments = serializers.IntegerField()
    active_departments = serializers.IntegerField()
    academic_departments = serializers.IntegerField()
    administrative_departments = serializers.IntegerField()
    research_departments = serializers.IntegerField()
    total_faculty = serializers.IntegerField()
    total_students = serializers.IntegerField()
    total_resources = serializers.IntegerField()
    upcoming_events = serializers.IntegerField()
    active_announcements = serializers.IntegerField()


class DepartmentSearchSerializer(serializers.Serializer):
    """Serializer for department search functionality"""
    
    query = serializers.CharField(max_length=200)
    department_type = serializers.ChoiceField(
        choices=Department.DEPARTMENT_TYPES, 
        required=False
    )
    status = serializers.ChoiceField(
        choices=Department.STATUS_CHOICES, 
        required=False
    )
    is_active = serializers.BooleanField(required=False)
    has_head = serializers.BooleanField(required=False)
    min_faculty_count = serializers.IntegerField(min_value=0, required=False)
    max_faculty_count = serializers.IntegerField(min_value=0, required=False)
    min_student_count = serializers.IntegerField(min_value=0, required=False)
    max_student_count = serializers.IntegerField(min_value=0, required=False)
