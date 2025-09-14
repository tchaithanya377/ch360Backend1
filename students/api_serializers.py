from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import UserSession

from .models import (
    Student, StudentEnrollmentHistory, StudentDocument, 
    CustomField, StudentCustomFieldValue, StudentImport
)

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """Basic student serializer for list views"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    has_login = serializers.ReadOnlyField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'roll_number', 'first_name', 'last_name', 'middle_name', 
            'full_name', 'date_of_birth', 'age', 'gender', 'student_batch', 
            'email', 'student_mobile', 'quota', 'rank', 'status', 'has_login', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentDetailSerializer(StudentSerializer):
    """Detailed student serializer for single student views"""
    user_info = serializers.SerializerMethodField()
    recent_sessions = serializers.SerializerMethodField()
    
    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + [
            'father_name', 'mother_name', 'father_mobile', 'mother_mobile',
            'full_address', 'village', 'aadhar_number', 'religion', 'caste', 
            'subcaste', 'user_info', 'recent_sessions'
        ]
    
    def get_user_info(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'is_active': obj.user.is_active,
                'date_joined': obj.user.date_joined
            }
        return None
    
    def get_recent_sessions(self, obj):
        if obj.user:
            sessions = UserSession.objects.filter(user=obj.user).order_by('-created_at')[:5]
            return [{
                'id': session.id,
                'ip': session.ip,
                'device_info': session.device_info,
                'created_at': session.created_at,
                'expires_at': session.expires_at,
                'is_active': session.is_active
            } for session in sessions]
        return []


class StudentEnrollmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for student enrollment history"""
    student_name = serializers.ReadOnlyField(source='student.full_name')
    student_roll_number = serializers.ReadOnlyField(source='student.roll_number')
    
    class Meta:
        model = StudentEnrollmentHistory
        fields = [
            'id', 'student', 'student_name', 'student_roll_number',
            'academic_year', 'year_of_study', 'semester', 'enrollment_date',
            'status', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentDocumentSerializer(serializers.ModelSerializer):
    """Serializer for student documents"""
    student_name = serializers.ReadOnlyField(source='student.full_name')
    student_roll_number = serializers.ReadOnlyField(source='student.roll_number')
    uploaded_by_name = serializers.ReadOnlyField(source='uploaded_by.get_full_name')
    file_size = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentDocument
        fields = [
            'id', 'student', 'student_name', 'student_roll_number',
            'document_type', 'title', 'description', 'document_file',
            'file_size', 'file_url', 'uploaded_by', 'uploaded_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'updated_at']
    
    def get_file_size(self, obj):
        if obj.document_file:
            try:
                return obj.document_file.size
            except:
                return None
        return None
    
    def get_file_url(self, obj):
        if obj.document_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document_file.url)
        return None


class CustomFieldSerializer(serializers.ModelSerializer):
    """Serializer for custom fields"""
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomField
        fields = [
            'id', 'name', 'label', 'field_type', 'required', 'help_text',
            'default_value', 'choices', 'validation_regex', 'min_value',
            'max_value', 'is_active', 'order', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_usage_count(self, obj):
        return StudentCustomFieldValue.objects.filter(custom_field=obj).count()


class StudentCustomFieldValueSerializer(serializers.ModelSerializer):
    """Serializer for student custom field values"""
    student_name = serializers.ReadOnlyField(source='student.full_name')
    student_roll_number = serializers.ReadOnlyField(source='student.roll_number')
    custom_field_label = serializers.ReadOnlyField(source='custom_field.label')
    custom_field_type = serializers.ReadOnlyField(source='custom_field.field_type')
    
    class Meta:
        model = StudentCustomFieldValue
        fields = [
            'id', 'student', 'student_name', 'student_roll_number',
            'custom_field', 'custom_field_label', 'custom_field_type',
            'value', 'file_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentImportSerializer(serializers.ModelSerializer):
    """Serializer for student import records"""
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = StudentImport
        fields = [
            'id', 'filename', 'file_size', 'total_rows', 'success_count',
            'error_count', 'warning_count', 'skip_errors', 'create_login',
            'update_existing', 'status', 'errors', 'warnings', 'created_by',
            'created_by_name', 'success_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentStatsSerializer(serializers.Serializer):
    """Serializer for student statistics"""
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    students_with_login = serializers.IntegerField()
    recent_enrollments = serializers.IntegerField()
    grade_distribution = serializers.ListField()
    status_distribution = serializers.ListField()
    gender_distribution = serializers.ListField()


class StudentBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk student creation"""
    students = StudentSerializer(many=True)


class StudentBulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk student updates"""
    updates = serializers.ListField(
        child=serializers.DictField()
    )


class StudentBulkDeleteSerializer(serializers.Serializer):
    """Serializer for bulk student deletion"""
    roll_numbers = serializers.ListField(
        child=serializers.CharField()
    )


class StudentSearchSerializer(serializers.Serializer):
    """Serializer for student search"""
    q = serializers.CharField(help_text="Search query")


class StudentLoginSerializer(serializers.Serializer):
    """Serializer for creating student login"""
    password = serializers.CharField(required=False, help_text="Custom password (optional)")


# Nested serializers for related data
class StudentUserSerializer(serializers.ModelSerializer):
    """Serializer for student user information"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined']


class StudentSessionSerializer(serializers.ModelSerializer):
    """Serializer for student login sessions"""
    class Meta:
        model = UserSession
        fields = ['id', 'ip', 'device_info', 'created_at', 'expires_at', 'is_active']


# API Response serializers
class StudentListResponseSerializer(serializers.Serializer):
    """Serializer for student list API response"""
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = StudentSerializer(many=True)


class StudentDetailResponseSerializer(serializers.Serializer):
    """Serializer for student detail API response"""
    student = StudentDetailSerializer()
    documents = StudentDocumentSerializer(many=True)
    enrollment_history = StudentEnrollmentHistorySerializer(many=True)
    custom_fields = StudentCustomFieldValueSerializer(many=True)


class BulkOperationResponseSerializer(serializers.Serializer):
    """Serializer for bulk operation responses"""
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    errors = serializers.ListField(allow_empty=True)
    results = serializers.ListField(allow_empty=True, required=False)

