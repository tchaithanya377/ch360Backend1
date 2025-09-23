from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Student, StudentRepresentative, StudentRepresentativeActivity, 
    StudentFeedback, StudentRepresentativeType
)

User = get_user_model()


class StudentPortalLoginSerializer(serializers.Serializer):
    """Serializer for student portal login with roll number or email"""
    username = serializers.CharField(required=False, help_text="Roll number or email")
    email = serializers.EmailField(required=False, help_text="Email address")
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not (username or email):
            raise serializers.ValidationError("Either username or email is required")
        
        # Use existing identifier lookup logic
        user = self._get_user_by_identifier(username or email)
        
        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")
        
        # Check if user has Student role
        if not self._user_is_student(user):
            raise serializers.ValidationError("Access denied. Student role required.")
        
        attrs['user'] = user
        return attrs
    
    def _get_user_by_identifier(self, identifier: str):
        """Get user by roll number or email"""
        from accounts.models import AuthIdentifier, IdentifierType
        from django.db.models import Q
        
        # Match by email
        try:
            return User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            pass
        
        # Match by roll number via AuthIdentifier
        auth_ids = AuthIdentifier.objects.filter(
            Q(identifier__iexact=identifier),
            Q(id_type=IdentifierType.USERNAME) | Q(id_type=IdentifierType.EMAIL)
        ).select_related('user')
        if auth_ids.exists():
            return auth_ids.first().user
        
        # As fallback, match username field directly
        try:
            return User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            return None
    
    def _user_is_student(self, user):
        """Check if user has Student role"""
        return user.groups.filter(name='Student').exists()


class StudentRepresentativeSerializer(serializers.ModelSerializer):
    """Serializer for student representative information"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    scope_description = serializers.ReadOnlyField()
    is_current = serializers.ReadOnlyField()
    represented_students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentRepresentative
        fields = [
            'id', 'student', 'student_name', 'student_roll_number',
            'representative_type', 'academic_year', 'semester',
            'department', 'academic_program', 'year_of_study', 'section',
            'scope_description', 'is_active', 'is_current',
            'start_date', 'end_date', 'responsibilities', 'achievements',
            'contact_email', 'contact_phone', 'represented_students_count',
            'nominated_by', 'approved_by', 'nomination_date', 'approval_date',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_represented_students_count(self, obj):
        """Get count of students represented by this representative"""
        return obj.get_represented_students().count()


class StudentRepresentativeActivitySerializer(serializers.ModelSerializer):
    """Serializer for representative activities"""
    representative_name = serializers.CharField(source='representative.student.full_name', read_only=True)
    representative_type = serializers.CharField(source='representative.representative_type', read_only=True)
    
    class Meta:
        model = StudentRepresentativeActivity
        fields = [
            'id', 'representative', 'representative_name', 'representative_type',
            'activity_type', 'title', 'description', 'activity_date', 'location',
            'participants_count', 'target_audience', 'outcomes', 'feedback_received',
            'follow_up_required', 'follow_up_notes', 'status', 'reviewed_by',
            'review_notes', 'attachments', 'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for student feedback"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    representative_name = serializers.CharField(source='representative.student.full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = StudentFeedback
        fields = [
            'id', 'student', 'student_name', 'student_roll_number',
            'representative', 'representative_name', 'feedback_type',
            'title', 'description', 'priority', 'status', 'resolution_notes',
            'resolved_by', 'resolved_date', 'follow_up_required', 'follow_up_date',
            'attachments', 'is_anonymous', 'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentPortalProfileSerializer(serializers.ModelSerializer):
    """Comprehensive student profile serializer for portal"""
    full_name = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    academic_info = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()
    representative_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'roll_number', 'full_name', 'first_name', 'last_name', 'middle_name',
            'date_of_birth', 'age', 'gender', 'email', 'student_mobile', 'status',
            'enrollment_date', 'expected_graduation_date', 'academic_info', 'contact_info',
            'representative_role', 'profile_picture'
        ]
    
    def get_academic_info(self, obj):
        """Get academic information from student batch"""
        if not obj.student_batch:
            return None
        
        batch = obj.student_batch
        return {
            'department': {
                'id': str(batch.department.id),
                'name': batch.department.name,
                'code': batch.department.code
            } if batch.department else None,
            'academic_program': {
                'id': str(batch.academic_program.id),
                'name': batch.academic_program.name,
                'code': batch.academic_program.code
            } if batch.academic_program else None,
            'academic_year': batch.academic_year.year if batch.academic_year else None,
            'year_of_study': batch.year_of_study,
            'semester': batch.semester,
            'section': batch.section,
            'batch_name': batch.batch_name
        }
    
    def get_contact_info(self, obj):
        """Get contact information"""
        return {
            'address_line1': obj.address_line1,
            'address_line2': obj.address_line2,
            'city': obj.city,
            'state': obj.state,
            'postal_code': obj.postal_code,
            'country': obj.country,
            'father_name': obj.father_name,
            'father_mobile': obj.father_mobile,
            'mother_name': obj.mother_name,
            'mother_mobile': obj.mother_mobile,
            'emergency_contact_name': obj.emergency_contact_name,
            'emergency_contact_phone': obj.emergency_contact_phone
        }
    
    def get_representative_role(self, obj):
        """Get representative role information if any"""
        try:
            rep_role = obj.representative_role
            if rep_role.is_current:
                return StudentRepresentativeSerializer(rep_role).data
        except StudentRepresentative.DoesNotExist:
            pass
        return None


class StudentPortalProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating student profile (limited fields)"""
    
    class Meta:
        model = Student
        fields = [
            'student_mobile', 'address_line1', 'address_line2', 'city', 
            'state', 'postal_code', 'emergency_contact_name', 'emergency_contact_phone',
            'profile_picture'
        ]


class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student dashboard data"""
    student = StudentPortalProfileSerializer(read_only=True)
    academic_summary = serializers.DictField(read_only=True)
    stats = serializers.DictField(read_only=True)
    recent_activities = serializers.ListField(read_only=True)
    announcements = serializers.ListField(read_only=True)
    upcoming_events = serializers.ListField(read_only=True)
    feedback_summary = serializers.DictField(read_only=True)


class StudentRepresentativeDashboardSerializer(serializers.Serializer):
    """Serializer for representative dashboard data"""
    representative = StudentRepresentativeSerializer(read_only=True)
    represented_students_count = serializers.IntegerField(read_only=True)
    recent_activities = serializers.ListField(read_only=True)
    pending_feedback = serializers.ListField(read_only=True)
    feedback_stats = serializers.DictField(read_only=True)
    upcoming_events = serializers.ListField(read_only=True)
    announcements = serializers.ListField(read_only=True)


class StudentFeedbackSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submitting student feedback"""
    
    class Meta:
        model = StudentFeedback
        fields = [
            'feedback_type', 'title', 'description', 'priority',
            'attachments', 'is_anonymous'
        ]
    
    def create(self, validated_data):
        """Create feedback submission"""
        validated_data['student'] = self.context['request'].user.student_profile
        return super().create(validated_data)


class StudentRepresentativeActivitySubmissionSerializer(serializers.ModelSerializer):
    """Serializer for representative activity submission"""
    
    class Meta:
        model = StudentRepresentativeActivity
        fields = [
            'activity_type', 'title', 'description', 'activity_date',
            'location', 'participants_count', 'target_audience',
            'outcomes', 'feedback_received', 'follow_up_required',
            'follow_up_notes', 'attachments', 'tags'
        ]
    
    def create(self, validated_data):
        """Create activity submission"""
        validated_data['representative'] = self.context['request'].user.student_profile.representative_role
        return super().create(validated_data)


class StudentAnnouncementSerializer(serializers.Serializer):
    """Serializer for student announcements"""
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    author = serializers.CharField(read_only=True)
    announcement_type = serializers.CharField(read_only=True)
    target_audience = serializers.CharField(read_only=True)
    priority = serializers.CharField(read_only=True)
    is_important = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)


class StudentEventSerializer(serializers.Serializer):
    """Serializer for student events"""
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    event_type = serializers.CharField(read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)
    location = serializers.CharField(read_only=True)
    organizer = serializers.CharField(read_only=True)
    target_audience = serializers.CharField(read_only=True)
    registration_required = serializers.BooleanField(read_only=True)
    max_participants = serializers.IntegerField(read_only=True)
    current_participants = serializers.IntegerField(read_only=True)
    is_registered = serializers.BooleanField(read_only=True)
