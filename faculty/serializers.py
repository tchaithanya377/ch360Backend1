from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Faculty, FacultySubject, FacultySchedule, FacultyLeave, 
    FacultyPerformance, FacultyDocument, CustomField, CustomFieldValue
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CustomFieldSerializer(serializers.ModelSerializer):
    """Serializer for CustomField model"""
    
    class Meta:
        model = CustomField
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomFieldValueSerializer(serializers.ModelSerializer):
    """Serializer for CustomFieldValue model"""
    custom_field = CustomFieldSerializer(read_only=True)
    custom_field_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = CustomFieldValue
        fields = ['id', 'custom_field', 'custom_field_id', 'value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacultyDocumentSerializer(serializers.ModelSerializer):
    """Serializer for FacultyDocument model"""
    verified_by = UserSerializer(read_only=True)
    
    class Meta:
        model = FacultyDocument
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified_by', 'verified_at']


class FacultySubjectSerializer(serializers.ModelSerializer):
    """Serializer for FacultySubject model"""
    
    class Meta:
        model = FacultySubject
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacultyScheduleSerializer(serializers.ModelSerializer):
    """Serializer for FacultySchedule model"""
    
    class Meta:
        model = FacultySchedule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacultyLeaveSerializer(serializers.ModelSerializer):
    """Serializer for FacultyLeave model"""
    approved_by = UserSerializer(read_only=True)
    leave_days = serializers.ReadOnlyField()
    
    class Meta:
        model = FacultyLeave
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_by', 'approved_at', 'leave_days']


class FacultyPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for FacultyPerformance model"""
    evaluated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = FacultyPerformance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'evaluated_by', 'overall_score']


class FacultySerializer(serializers.ModelSerializer):
    """Main serializer for Faculty model"""
    user = UserSerializer(read_only=True)
    documents = FacultyDocumentSerializer(many=True, read_only=True)
    subjects = FacultySubjectSerializer(many=True, read_only=True)
    schedules = FacultyScheduleSerializer(many=True, read_only=True)
    leaves = FacultyLeaveSerializer(many=True, read_only=True)
    performances = FacultyPerformanceSerializer(many=True, read_only=True)
    custom_field_values = CustomFieldValueSerializer(many=True, read_only=True)
    full_name = serializers.ReadOnlyField()
    is_active_faculty = serializers.ReadOnlyField()
    
    class Meta:
        model = Faculty
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class FacultyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new faculty members"""
    custom_fields = serializers.JSONField(required=False, help_text="Custom field values as key-value pairs")
    department_name = serializers.CharField(source='department_ref.name', read_only=True)
    
    class Meta:
        model = Faculty
        fields = [
            'name', 'pan_no', 'apaar_faculty_id', 'highest_degree', 'university', 
            'area_of_specialization', 'date_of_joining_institution', 'designation_at_joining',
            'present_designation', 'date_designated_as_professor', 'nature_of_association',
            'contractual_full_time_part_time', 'currently_associated', 'date_of_leaving',
            'experience_in_current_institute', 'employee_id', 'first_name', 'last_name', 
            'middle_name', 'date_of_birth', 'gender', 'designation', 'department', 
            'department_ref', 'department_name', 'employment_type', 'date_of_joining', 
            'phone_number', 'alternate_phone', 'address_line_1', 'address_line_2', 'city', 
            'state', 'postal_code', 'country', 'highest_qualification', 'specialization', 
            'year_of_completion', 'experience_years', 'previous_institution', 'achievements', 
            'research_interests', 'is_head_of_department', 'is_mentor', 'mentor_for_grades', 
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship', 
            'profile_picture', 'bio', 'notes', 'email', 'custom_fields'
        ]
    
    def validate_apaar_faculty_id(self, value):
        """Validate that apaar_faculty_id is unique"""
        if Faculty.objects.filter(apaar_faculty_id=value).exists():
            raise serializers.ValidationError("APAAR Faculty ID already exists.")
        return value
    
    def validate_email(self, value):
        """Validate that email is unique"""
        if Faculty.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def create(self, validated_data):
        """Create faculty member with custom fields"""
        custom_fields_data = validated_data.pop('custom_fields', {})
        
        # Create faculty member (user will be auto-generated in save method)
        faculty = Faculty.objects.create(**validated_data)
        
        # Create custom field values
        for field_name, value in custom_fields_data.items():
            try:
                custom_field = CustomField.objects.get(name=field_name, is_active=True)
                CustomFieldValue.objects.create(
                    faculty=faculty,
                    custom_field=custom_field,
                    value=str(value)
                )
            except CustomField.DoesNotExist:
                # Skip if custom field doesn't exist
                pass
        
        return faculty


class FacultyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating faculty information"""
    custom_fields = serializers.JSONField(required=False, help_text="Custom field values as key-value pairs")
    department_name = serializers.CharField(source='department_ref.name', read_only=True)
    
    class Meta:
        model = Faculty
        fields = [
            'name', 'pan_no', 'highest_degree', 'university', 'area_of_specialization',
            'date_of_joining_institution', 'designation_at_joining', 'present_designation',
            'date_designated_as_professor', 'nature_of_association', 'contractual_full_time_part_time',
            'currently_associated', 'date_of_leaving', 'experience_in_current_institute',
            'first_name', 'last_name', 'middle_name', 'date_of_birth', 'gender',
            'designation', 'department', 'department_ref', 'department_name', 'employment_type', 
            'status', 'phone_number', 'alternate_phone', 'address_line_1', 'address_line_2', 
            'city', 'state', 'postal_code', 'country', 'highest_qualification', 'specialization',
            'year_of_completion', 'experience_years', 'previous_institution',
            'achievements', 'research_interests', 'is_head_of_department', 'is_mentor',
            'mentor_for_grades', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'profile_picture', 'bio', 'notes', 'custom_fields'
        ]
    
    def update(self, instance, validated_data):
        """Update faculty member with custom fields"""
        custom_fields_data = validated_data.pop('custom_fields', {})
        
        # Update faculty member
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update custom field values
        for field_name, value in custom_fields_data.items():
            try:
                custom_field = CustomField.objects.get(name=field_name, is_active=True)
                custom_field_value, created = CustomFieldValue.objects.get_or_create(
                    faculty=instance,
                    custom_field=custom_field,
                    defaults={'value': str(value)}
                )
                if not created:
                    custom_field_value.value = str(value)
                    custom_field_value.save()
            except CustomField.DoesNotExist:
                # Skip if custom field doesn't exist
                pass
        
        return instance


class FacultyListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing faculty members"""
    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    is_active_faculty = serializers.ReadOnlyField()
    
    class Meta:
        model = Faculty
        fields = [
            'id', 'user', 'name', 'apaar_faculty_id', 'employee_id', 'full_name', 
            'present_designation', 'department', 'employment_type', 'status', 
            'email', 'phone_number', 'date_of_joining_institution', 'currently_associated',
            'is_active_faculty', 'created_at'
        ]


class FacultyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for faculty member view"""
    user = UserSerializer(read_only=True)
    documents = FacultyDocumentSerializer(many=True, read_only=True)
    subjects = FacultySubjectSerializer(many=True, read_only=True)
    schedules = FacultyScheduleSerializer(many=True, read_only=True)
    leaves = FacultyLeaveSerializer(many=True, read_only=True)
    performances = FacultyPerformanceSerializer(many=True, read_only=True)
    custom_field_values = CustomFieldValueSerializer(many=True, read_only=True)
    full_name = serializers.ReadOnlyField()
    is_active_faculty = serializers.ReadOnlyField()
    
    class Meta:
        model = Faculty
        fields = '__all__'


class FacultySubjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating faculty subjects"""
    
    class Meta:
        model = FacultySubject
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacultyScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating faculty schedules"""
    
    class Meta:
        model = FacultySchedule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FacultyLeaveCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating faculty leave requests"""
    
    class Meta:
        model = FacultyLeave
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_by', 'approved_at']


class FacultyPerformanceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating faculty performance evaluations"""
    
    class Meta:
        model = FacultyPerformance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'evaluated_by', 'overall_score']


class FacultyDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating faculty documents"""
    
    class Meta:
        model = FacultyDocument
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified_by', 'verified_at']


class CustomFieldCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating custom fields"""
    
    class Meta:
        model = CustomField
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomFieldValueCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating custom field values"""
    
    class Meta:
        model = CustomFieldValue
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
