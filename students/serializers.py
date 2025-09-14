from rest_framework import serializers
from .models import (
    Student, StudentEnrollmentHistory, StudentDocument, CustomField, 
    StudentCustomFieldValue, StudentBatch, BulkAssignment
)

# Import API serializers
from .api_serializers import (
    StudentSerializer as APIStudentSerializer,
    StudentDetailSerializer as APIStudentDetailSerializer,
    StudentEnrollmentHistorySerializer as APIStudentEnrollmentHistorySerializer,
    StudentDocumentSerializer as APIStudentDocumentSerializer,
    CustomFieldSerializer as APICustomFieldSerializer,
    StudentCustomFieldValueSerializer as APIStudentCustomFieldValueSerializer,
    StudentImportSerializer as APIStudentImportSerializer,
    StudentStatsSerializer as APIStudentStatsSerializer
)


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='student_batch.department.name', read_only=True)
    department_code = serializers.CharField(source='student_batch.department.code', read_only=True)
    academic_program_name = serializers.CharField(source='student_batch.academic_program.name', read_only=True)
    academic_program_code = serializers.CharField(source='student_batch.academic_program.code', read_only=True)
    academic_year_display = serializers.CharField(source='student_batch.academic_year.year', read_only=True)
    semester_name = serializers.CharField(source='student_batch.semester', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'roll_number', 'first_name', 'last_name', 'middle_name',
            'full_name', 'date_of_birth', 'age', 'gender', 'email', 
            'student_mobile', 'address_line1', 'address_line2', 'city', 
            'state', 'postal_code', 'country', 'full_address',
            'quota', 'rank', 'student_batch',
            'department_name', 'department_code',
            'academic_program_name', 'academic_program_code',
            'academic_year_display', 'semester_name',
            'village', 'aadhar_number', 'religion', 'caste', 'subcaste',
            'father_name', 'mother_name', 'father_mobile', 'mother_mobile',
            'enrollment_date', 'expected_graduation_date', 'status',
            'guardian_name', 'guardian_phone', 'guardian_email', 
            'guardian_relationship', 'emergency_contact_name', 
            'emergency_contact_phone', 'emergency_contact_relationship',
            'medical_conditions', 'medications', 'notes', 'profile_picture',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_roll_number(self, value):
        """Validate that roll_number is unique"""
        if Student.objects.filter(roll_number=value).exists():
            raise serializers.ValidationError("Roll number must be unique.")
        return value
    
    def validate_email(self, value):
        """Validate that email is unique if provided"""
        if value and Student.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email must be unique.")
        return value


class StudentCreateSerializer(StudentSerializer):
    """Serializer for creating new students with required fields"""
    
    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'age', 'full_address']
    
    def validate(self, data):
        """Validate required fields for student creation"""
        required_fields = ['roll_number', 'first_name', 'last_name', 'date_of_birth', 'gender']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required.")
        return data


class StudentUpdateSerializer(StudentSerializer):
    """Serializer for updating existing students"""
    
    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields
        read_only_fields = ['id', 'roll_number', 'created_at', 'updated_at', 'full_name', 'age', 'full_address']
    
    def validate_email(self, value):
        """Validate that email is unique if provided, excluding current instance"""
        if value:
            queryset = Student.objects.filter(email=value)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Email must be unique.")
        return value


class StudentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing students"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'roll_number', 'full_name', 'age', 'gender', 'email',
            'student_batch', 'status', 'enrollment_date', 'created_at'
        ]


class StudentEnrollmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for Student Enrollment History"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    
    class Meta:
        model = StudentEnrollmentHistory
        fields = [
            'id', 'student', 'student_name', 'year_of_study', 'semester', 'academic_year',
            'enrollment_date', 'completion_date', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Student Documents"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.email', read_only=True)
    
    class Meta:
        model = StudentDocument
        fields = [
            'id', 'student', 'student_name', 'document_type', 'title',
            'description', 'document_file', 'uploaded_by', 'uploaded_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'updated_at']


class StudentDetailSerializer(StudentSerializer):
    """Detailed serializer for student with related data"""
    enrollment_history = StudentEnrollmentHistorySerializer(many=True, read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)
    
    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ['enrollment_history', 'documents']


class CustomFieldSerializer(serializers.ModelSerializer):
    """Serializer for Custom Field model"""
    
    class Meta:
        model = CustomField
        fields = [
            'id', 'name', 'label', 'field_type', 'required', 'help_text',
            'default_value', 'choices', 'validation_regex', 'min_value',
            'max_value', 'is_active', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentCustomFieldValueSerializer(serializers.ModelSerializer):
    """Serializer for Student Custom Field Values"""
    custom_field = CustomFieldSerializer(read_only=True)
    custom_field_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = StudentCustomFieldValue
        fields = [
            'id', 'custom_field', 'custom_field_id', 'value', 'file_value',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentWithCustomFieldsSerializer(StudentSerializer):
    """Serializer for Student with custom field values"""
    custom_field_values = StudentCustomFieldValueSerializer(many=True, read_only=True)
    
    class Meta(StudentSerializer.Meta):
        fields = StudentSerializer.Meta.fields + ['custom_field_values']


class StudentDivisionSerializer(serializers.Serializer):
    """Serializer for student division data"""
    department_id = serializers.UUIDField()
    department_name = serializers.CharField()
    department_code = serializers.CharField()
    years = serializers.DictField()


class StudentAssignmentSerializer(serializers.Serializer):
    """Serializer for student assignment requests"""
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of student IDs to assign"
    )
    department_id = serializers.UUIDField(required=False, allow_null=True)
    academic_program_id = serializers.UUIDField(required=False, allow_null=True)
    academic_year_id = serializers.UUIDField(required=False, allow_null=True)
    year_of_study = serializers.CharField(required=False, allow_null=True, max_length=1)
    semester = serializers.CharField(required=False, allow_null=True, max_length=2)
    section = serializers.CharField(required=False, allow_null=True, max_length=1)
    
    def validate_student_ids(self, value):
        """Validate that student IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one student ID is required")
        
        existing_students = Student.objects.filter(id__in=value).count()
        if existing_students != len(value):
            raise serializers.ValidationError("One or more student IDs are invalid")
        
        return value


class BulkAssignmentCriteriaSerializer(serializers.Serializer):
    """Serializer for bulk assignment criteria"""
    current_department = serializers.UUIDField(required=False, allow_null=True)
    current_academic_program = serializers.UUIDField(required=False, allow_null=True)
    current_academic_year = serializers.UUIDField(required=False, allow_null=True)
    current_year_of_study = serializers.CharField(required=False, allow_null=True, max_length=1)
    current_semester = serializers.CharField(required=False, allow_null=True, max_length=2)
    current_section = serializers.CharField(required=False, allow_null=True, max_length=1)
    gender = serializers.CharField(required=False, allow_null=True, max_length=1)
    quota = serializers.CharField(required=False, allow_null=True, max_length=25)


class BulkAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk assignment requests"""
    criteria = BulkAssignmentCriteriaSerializer()
    assignment = StudentAssignmentSerializer()
    
    def validate(self, data):
        """Validate that at least one assignment field is provided"""
        assignment = data.get('assignment', {})
        assignment_fields = ['department_id', 'academic_program_id', 'academic_year_id', 'year_of_study', 'semester', 'section']
        
        if not any(assignment.get(field) for field in assignment_fields):
            raise serializers.ValidationError(
                "At least one assignment field (department_id, academic_program_id, academic_year, year_of_study, semester, section) is required"
            )
        
        return data


class StudentDivisionStatsSerializer(serializers.Serializer):
    """Serializer for student division statistics"""
    department_code = serializers.CharField()
    department_name = serializers.CharField()
    total_students = serializers.IntegerField()
    years = serializers.DictField()
    sections = serializers.DictField()


class StudentBatchSerializer(serializers.ModelSerializer):
    """Serializer for Student Batch model"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    academic_program_name = serializers.CharField(source='academic_program.name', read_only=True)
    academic_program_code = serializers.CharField(source='academic_program.code', read_only=True)
    academic_year_display = serializers.CharField(source='academic_year.year', read_only=True)
    semester_name = serializers.ReadOnlyField()
    semester_type = serializers.ReadOnlyField()
    semester_start_date = serializers.ReadOnlyField()
    semester_end_date = serializers.ReadOnlyField()
    semester_is_current = serializers.ReadOnlyField()
    available_capacity = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    
    class Meta:
        model = StudentBatch
        fields = [
            'id', 'department', 'department_name', 'department_code',
            'academic_program', 'academic_program_name', 'academic_program_code',
            'academic_year', 'academic_year_display', 'semester', 'semester_name',
            'semester_type', 'semester_start_date', 'semester_end_date', 'semester_is_current',
            'year_of_study', 'section', 'batch_name', 'batch_code',
            'max_capacity', 'current_count', 'available_capacity', 'is_full',
            'is_active', 'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_count']


class BulkAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Bulk Assignment operations"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    success_rate = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = BulkAssignment
        fields = [
            'id', 'operation_type', 'title', 'description', 'criteria', 'assignment_data',
            'total_students_found', 'students_updated', 'students_failed', 'errors', 'warnings',
            'status', 'started_at', 'completed_at', 'created_by', 'created_by_name',
            'success_rate', 'duration', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_students_found', 'students_updated', 'students_failed', 
            'errors', 'warnings', 'status', 'started_at', 'completed_at', 
            'created_at', 'updated_at'
        ]


class BulkAssignmentCreateSerializer(serializers.Serializer):
    """Serializer for creating bulk assignment operations"""
    operation_type = serializers.ChoiceField(choices=BulkAssignment.OPERATION_TYPES)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    criteria = serializers.JSONField()
    assignment_data = serializers.JSONField()
    
    def validate_criteria(self, value):
        """Validate criteria data"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Criteria must be a dictionary")
        return value
    
    def validate_assignment_data(self, value):
        """Validate assignment data"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Assignment data must be a dictionary")
        return value


class SmartBulkAssignmentSerializer(serializers.Serializer):
    """Serializer for smart bulk assignment with automatic batch management"""
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="List of student IDs to assign"
    )
    department_id = serializers.UUIDField(required=False, allow_null=True)
    academic_program_id = serializers.UUIDField(required=False, allow_null=True)
    academic_year_id = serializers.UUIDField(required=False, allow_null=True)
    semester_id = serializers.UUIDField(required=False, allow_null=True)
    year_of_study = serializers.CharField(required=False, allow_null=True, max_length=1)
    auto_assign_sections = serializers.BooleanField(default=True, help_text="Automatically assign students to sections")
    max_students_per_section = serializers.IntegerField(default=70, min_value=1, max_value=100)
    section_assignment_strategy = serializers.ChoiceField(
        choices=[
            ('ROUND_ROBIN', 'Round Robin'),
            ('BALANCED', 'Balanced Distribution'),
            ('SEQUENTIAL', 'Sequential Assignment'),
        ],
        default='BALANCED'
    )
    
    def validate_student_ids(self, value):
        """Validate that student IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one student ID is required")
        
        existing_students = Student.objects.filter(id__in=value).count()
        if existing_students != len(value):
            raise serializers.ValidationError("One or more student IDs are invalid")
        
        return value
    
    def validate(self, data):
        """Validate that at least one assignment field is provided"""
        assignment_fields = [
            'department_id', 'academic_program_id', 'academic_year_id', 
            'semester_id', 'year_of_study'
        ]
        
        if not any(data.get(field) for field in assignment_fields):
            raise serializers.ValidationError(
                "At least one assignment field is required"
            )
        
        return data
