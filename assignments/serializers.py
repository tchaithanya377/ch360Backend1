from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Assignment, AssignmentSubmission, AssignmentFile, 
    AssignmentGrade, AssignmentComment, AssignmentCategory,
    AssignmentGroup, AssignmentTemplate, AssignmentRubric,
    AssignmentRubricGrade, AssignmentPeerReview, AssignmentPlagiarismCheck,
    AssignmentLearningOutcome, AssignmentAnalytics, AssignmentNotification,
    AssignmentSchedule
)

User = get_user_model()


class AssignmentCategorySerializer(serializers.ModelSerializer):
    """Serializer for AssignmentCategory model"""
    
    class Meta:
        model = AssignmentCategory
        fields = [
            'id', 'name', 'description', 'color_code', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssignmentFileSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentFile model"""
    
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentFile
        fields = [
            'id', 'file_name', 'file_path', 'file_url', 'file_type',
            'file_size', 'file_size_mb', 'mime_type', 'uploaded_by',
            'uploaded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'uploaded_at', 'created_at', 'updated_at'
        ]
    
    def get_file_url(self, obj):
        """Get the URL for the file"""
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None
    
    def get_file_size_mb(self, obj):
        """Get file size in MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class AssignmentCommentSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentComment model"""
    
    author_name = serializers.CharField(source='author.email', read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentComment
        fields = [
            'id', 'assignment', 'author', 'author_name', 'content',
            'comment_type', 'parent_comment', 'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        """Get replies to this comment"""
        replies = obj.replies.all()
        return AssignmentCommentSerializer(replies, many=True, context=self.context).data


class AssignmentGradeSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentGrade model"""
    
    graded_by_name = serializers.CharField(source='graded_by.email', read_only=True)
    
    class Meta:
        model = AssignmentGrade
        fields = [
            'id', 'marks_obtained', 'grade_letter', 'feedback',
            'graded_by', 'graded_by_name', 'graded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'graded_at', 'created_at', 'updated_at']


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentSubmission model"""
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.apaar_student_id', read_only=True)
    grade = AssignmentGradeSerializer(read_only=True)
    files = AssignmentFileSerializer(many=True, read_only=True)
    graded_by_name = serializers.CharField(source='graded_by.email', read_only=True)
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'id', 'assignment', 'student', 'student_name', 'student_id',
            'content', 'notes', 'status', 'submission_date', 'is_late',
            'attachment_files', 'files', 'grade', 'feedback', 'graded_by',
            'graded_by_name', 'graded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'submission_date', 'is_late', 'graded_at', 'created_at', 'updated_at'
        ]


class AssignmentSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AssignmentSubmission"""
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'assignment', 'content', 'notes', 'attachment_files'
        ]
    
    def create(self, validated_data):
        """Create a new submission"""
        # Get student from request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'student_profile'):
            validated_data['student'] = request.user.student_profile
        else:
            raise serializers.ValidationError("Student profile not found")
        
        return super().create(validated_data)


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model"""
    
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    faculty_id = serializers.CharField(source='faculty.apaar_faculty_id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    academic_year_name = serializers.CharField(source='academic_year.year', read_only=True)
    semester_name = serializers.CharField(source='semester.name', read_only=True)
    submission_count = serializers.IntegerField(read_only=True)
    graded_count = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    files = AssignmentFileSerializer(many=True, read_only=True)
    comments = AssignmentCommentSerializer(many=True, read_only=True)
    submissions = AssignmentSubmissionSerializer(many=True, read_only=True)
    assigned_to_programs_names = serializers.StringRelatedField(
        source='assigned_to_programs', many=True, read_only=True
    )
    assigned_to_departments_names = serializers.StringRelatedField(
        source='assigned_to_departments', many=True, read_only=True
    )
    assigned_to_courses_names = serializers.StringRelatedField(
        source='assigned_to_courses', many=True, read_only=True
    )
    assigned_to_course_sections_names = serializers.StringRelatedField(
        source='assigned_to_course_sections', many=True, read_only=True
    )
    assigned_to_students_names = serializers.StringRelatedField(
        source='assigned_to_students', many=True, read_only=True
    )
    
    # New enhanced fields - will be defined after the related serializers
    rubric_name = serializers.CharField(source='rubric.name', read_only=True)
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'instructions', 'category', 'category_name',
            'faculty', 'faculty_name', 'faculty_id', 'assignment_type', 'difficulty_level',
            'max_marks', 'due_date', 'late_submission_allowed', 'late_penalty_percentage',
            'status', 'is_group_assignment', 'max_group_size', 'is_apaar_compliant',
            'requires_plagiarism_check', 'plagiarism_threshold', 'rubric', 'rubric_name',
            'enable_peer_review', 'peer_review_weight', 'learning_objectives',
            'estimated_time_hours', 'submission_reminder_days',
            'academic_year', 'academic_year_name', 'semester', 'semester_name',
            'assigned_to_programs', 'assigned_to_programs_names',
            'assigned_to_departments', 'assigned_to_departments_names',
            'assigned_to_courses', 'assigned_to_courses_names',
            'assigned_to_course_sections', 'assigned_to_course_sections_names',
            'assigned_to_students', 'assigned_to_students_names', 'attachment_files', 
            'files', 'comments', 'submissions', 'submission_count', 'graded_count', 
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'submission_count', 'graded_count', 'is_overdue',
            'created_at', 'updated_at'
        ]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Assignment"""
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'instructions', 'category', 'assignment_type',
            'difficulty_level', 'max_marks', 'due_date', 'late_submission_allowed',
            'late_penalty_percentage', 'is_group_assignment', 'max_group_size',
            'is_apaar_compliant', 'requires_plagiarism_check', 'plagiarism_threshold',
            'rubric', 'enable_peer_review', 'peer_review_weight', 'learning_objectives',
            'estimated_time_hours', 'submission_reminder_days', 'academic_year', 'semester',
            'assigned_to_programs', 'assigned_to_departments', 'assigned_to_courses',
            'assigned_to_course_sections', 'assigned_to_students', 'attachment_files'
        ]
    
    def create(self, validated_data):
        """Create a new assignment"""
        # Get faculty from request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'faculty_profile'):
            validated_data['faculty'] = request.user.faculty_profile
        else:
            raise serializers.ValidationError("Faculty profile not found")
        
        return super().create(validated_data)


class AssignmentGroupSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentGroup model"""
    
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    leader_name = serializers.CharField(source='leader.name', read_only=True)
    members_names = serializers.StringRelatedField(source='members', many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AssignmentGroup
        fields = [
            'id', 'assignment', 'assignment_title', 'group_name', 'members',
            'members_names', 'leader', 'leader_name', 'member_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Get the number of members in the group"""
        return obj.members.count()


class AssignmentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentTemplate model"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = AssignmentTemplate
        fields = [
            'id', 'name', 'description', 'instructions', 'category', 'category_name',
            'max_marks', 'is_group_assignment', 'max_group_size', 'template_data',
            'created_by', 'created_by_name', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class AssignmentTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AssignmentTemplate"""
    
    class Meta:
        model = AssignmentTemplate
        fields = [
            'name', 'description', 'instructions', 'category', 'max_marks',
            'is_group_assignment', 'max_group_size', 'template_data', 'is_public'
        ]
    
    def create(self, validated_data):
        """Create a new assignment template"""
        # Get user from request context
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
        else:
            raise serializers.ValidationError("User not found")
        
        return super().create(validated_data)


class AssignmentStatsSerializer(serializers.Serializer):
    """Serializer for assignment statistics"""
    
    total_assignments = serializers.IntegerField()
    published_assignments = serializers.IntegerField()
    draft_assignments = serializers.IntegerField()
    overdue_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    graded_submissions = serializers.IntegerField()
    pending_grades = serializers.IntegerField()
    average_grade = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)


class StudentAssignmentStatsSerializer(serializers.Serializer):
    """Serializer for student assignment statistics"""
    
    total_assignments = serializers.IntegerField()
    submitted_assignments = serializers.IntegerField()
    pending_assignments = serializers.IntegerField()
    late_submissions = serializers.IntegerField()
    average_grade = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    total_marks_obtained = serializers.DecimalField(max_digits=8, decimal_places=2)
    total_max_marks = serializers.DecimalField(max_digits=8, decimal_places=2)


class FacultyAssignmentStatsSerializer(serializers.Serializer):
    """Serializer for faculty assignment statistics"""
    
    total_assignments = serializers.IntegerField()
    published_assignments = serializers.IntegerField()
    draft_assignments = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    graded_submissions = serializers.IntegerField()
    pending_grades = serializers.IntegerField()
    average_grade = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    overdue_assignments = serializers.IntegerField()


class AssignmentRubricSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentRubric model"""
    
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = AssignmentRubric
        fields = [
            'id', 'name', 'description', 'rubric_type', 'criteria',
            'total_points', 'created_by', 'created_by_name', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class AssignmentRubricGradeSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentRubricGrade model"""
    
    graded_by_name = serializers.CharField(source='graded_by.email', read_only=True)
    
    class Meta:
        model = AssignmentRubricGrade
        fields = [
            'id', 'submission', 'rubric', 'criteria_scores', 'total_score',
            'feedback', 'graded_by', 'graded_by_name', 'graded_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'graded_at', 'created_at', 'updated_at']


class AssignmentPeerReviewSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentPeerReview model"""
    
    reviewer_name = serializers.CharField(source='reviewer.name', read_only=True)
    reviewee_name = serializers.CharField(source='reviewee.name', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = AssignmentPeerReview
        fields = [
            'id', 'assignment', 'assignment_title', 'reviewer', 'reviewer_name',
            'reviewee', 'reviewee_name', 'submission', 'content_rating',
            'clarity_rating', 'creativity_rating', 'overall_rating', 'strengths',
            'improvements', 'additional_comments', 'is_completed', 'submitted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at', 'updated_at']


class AssignmentPlagiarismCheckSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentPlagiarismCheck model"""
    
    student_name = serializers.CharField(source='submission.student.name', read_only=True)
    assignment_title = serializers.CharField(source='submission.assignment.title', read_only=True)
    checked_by_name = serializers.CharField(source='checked_by.email', read_only=True)
    
    class Meta:
        model = AssignmentPlagiarismCheck
        fields = [
            'id', 'submission', 'student_name', 'assignment_title', 'status',
            'similarity_percentage', 'sources', 'checked_at', 'checked_by',
            'checked_by_name', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'checked_at', 'created_at', 'updated_at']


class AssignmentLearningOutcomeSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentLearningOutcome model"""
    
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = AssignmentLearningOutcome
        fields = [
            'id', 'assignment', 'assignment_title', 'outcome_code', 'description',
            'bloom_level', 'weight', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssignmentAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentAnalytics model"""
    
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = AssignmentAnalytics
        fields = [
            'id', 'assignment', 'assignment_title', 'total_expected_submissions',
            'actual_submissions', 'submission_rate', 'average_grade', 'median_grade',
            'grade_distribution', 'average_submission_time', 'late_submission_rate',
            'outcome_achievement', 'plagiarism_rate', 'last_updated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_updated', 'created_at', 'updated_at']


class AssignmentNotificationSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentNotification model"""
    
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    recipient_name = serializers.CharField(source='recipient.email', read_only=True)
    
    class Meta:
        model = AssignmentNotification
        fields = [
            'id', 'assignment', 'assignment_title', 'recipient', 'recipient_name',
            'notification_type', 'title', 'message', 'is_read', 'read_at',
            'context_data', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'read_at', 'created_at', 'updated_at']


class AssignmentScheduleSerializer(serializers.ModelSerializer):
    """Serializer for AssignmentSchedule model"""
    
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.email', read_only=True)
    
    class Meta:
        model = AssignmentSchedule
        fields = [
            'id', 'name', 'description', 'template', 'template_name', 'schedule_type',
            'interval_days', 'target_programs', 'target_departments', 'target_courses',
            'is_active', 'start_date', 'end_date', 'last_run', 'next_run',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'next_run', 'created_by', 'created_at', 'updated_at']
