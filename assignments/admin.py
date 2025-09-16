from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    Assignment, AssignmentSubmission, AssignmentFile, 
    AssignmentGrade, AssignmentComment, AssignmentCategory,
    AssignmentRubric, AssignmentRubricGrade, AssignmentPeerReview,
    AssignmentPlagiarismCheck, AssignmentLearningOutcome, AssignmentAnalytics,
    AssignmentNotification, AssignmentSchedule, AssignmentTemplate, AssignmentGroup
)
from students.models import AcademicYear, Semester


class AssignmentAdminForm(forms.ModelForm):
    """Custom admin form for Assignment model"""
    
    class Meta:
        model = Assignment
        fields = '__all__'
        widgets = {
            'academic_year': forms.Select(choices=[]),
            'semester': forms.Select(choices=[]),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate academic year choices
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)
        self.fields['academic_year'].empty_label = "Select Academic Year"
        
        # Populate semester choices
        self.fields['semester'].queryset = Semester.objects.filter(is_active=True)
        self.fields['semester'].empty_label = "Select Semester"


@admin.register(AssignmentCategory)
class AssignmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color_code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    form = AssignmentAdminForm
    list_display = [
        'title', 'faculty', 'category', 'due_date', 'status', 
        'max_marks', 'submission_count', 'created_at'
    ]
    list_filter = [
        'status', 'category', 'faculty__department', 
        'due_date', 'created_at', 'academic_year', 'semester'
    ]
    search_fields = [
        'title', 'description', 'faculty__name', 
        'faculty__apaar_faculty_id'
    ]
    readonly_fields = ['created_at', 'updated_at', 'submission_count']
    filter_horizontal = [
        'assigned_to_programs', 'assigned_to_departments', 
        'assigned_to_courses', 'assigned_to_course_sections', 'assigned_to_students'
    ]
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'faculty')
        }),
        ('Assignment Details', {
            'fields': ('instructions', 'max_marks', 'due_date', 'late_submission_allowed', 'academic_year', 'semester')
        }),
        ('Assignment Settings', {
            'fields': ('status', 'is_group_assignment', 'max_group_size')
        }),
        ('Target Audience', {
            'fields': ('assigned_to_programs', 'assigned_to_departments', 'assigned_to_courses', 'assigned_to_course_sections', 'assigned_to_students'),
            'classes': ('collapse',)
        }),
        ('Files', {
            'fields': ('attachment_files',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'
    
    def get_form(self, request, obj=None, **kwargs):
        """Override to set faculty field based on current user"""
        form = super().get_form(request, obj, **kwargs)
        if hasattr(request.user, 'faculty_profile'):
            # Set the faculty field to the current user's faculty profile
            form.base_fields['faculty'].initial = request.user.faculty_profile
            form.base_fields['faculty'].widget.attrs['readonly'] = True
        return form


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        'assignment', 'student', 'submission_date', 'status', 
        'is_late', 'grade_display'
    ]
    list_filter = [
        'status', 'is_late', 'assignment__faculty', 
        'submission_date', 'assignment__category'
    ]
    search_fields = [
        'assignment__title', 'student__name', 
        'student__apaar_student_id'
    ]
    readonly_fields = ['submission_date', 'is_late', 'created_at', 'updated_at']
    date_hierarchy = 'submission_date'
    
    fieldsets = (
        ('Submission Details', {
            'fields': ('assignment', 'student', 'submission_date', 'status')
        }),
        ('Content', {
            'fields': ('content', 'notes')
        }),
        ('Files', {
            'fields': ('attachment_files',),
            'classes': ('collapse',)
        }),
        ('Grading', {
            'fields': ('grade', 'feedback', 'graded_by', 'graded_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def grade_display(self, obj):
        if obj.grade:
            return f"{obj.grade.marks_obtained}/{obj.assignment.max_marks}"
        return "Not Graded"
    grade_display.short_description = 'Grade'


@admin.register(AssignmentFile)
class AssignmentFileAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'assignment', 'file_type', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at', 'assignment__faculty']
    search_fields = ['file_name', 'assignment__title']
    readonly_fields = ['file_size', 'uploaded_at']


@admin.register(AssignmentGrade)
class AssignmentGradeAdmin(admin.ModelAdmin):
    list_display = [
        'submission', 'marks_obtained', 'max_marks', 'grade_letter', 
        'graded_by', 'graded_at'
    ]
    list_filter = ['grade_letter', 'graded_at', 'graded_by']
    search_fields = [
        'submission__student__name', 'submission__assignment__title'
    ]
    readonly_fields = ['graded_at']
    
    def max_marks(self, obj):
        return obj.submission.assignment.max_marks
    max_marks.short_description = 'Max Marks'


@admin.register(AssignmentComment)
class AssignmentCommentAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'author', 'comment_type', 'created_at']
    list_filter = ['comment_type', 'created_at', 'author']
    search_fields = ['content', 'assignment__title', 'author__name']
    readonly_fields = ['created_at']


@admin.register(AssignmentRubric)
class AssignmentRubricAdmin(admin.ModelAdmin):
    list_display = ['name', 'rubric_type', 'total_points', 'created_by', 'is_public', 'created_at']
    list_filter = ['rubric_type', 'is_public', 'created_at', 'created_by']
    search_fields = ['name', 'description', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = []


@admin.register(AssignmentRubricGrade)
class AssignmentRubricGradeAdmin(admin.ModelAdmin):
    list_display = ['submission', 'rubric', 'total_score', 'graded_by', 'graded_at']
    list_filter = ['graded_at', 'graded_by', 'rubric']
    search_fields = ['submission__student__name', 'submission__assignment__title', 'rubric__name']
    readonly_fields = ['graded_at']


@admin.register(AssignmentPeerReview)
class AssignmentPeerReviewAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'reviewer', 'reviewee', 'overall_rating', 'is_completed', 'submitted_at']
    list_filter = ['is_completed', 'overall_rating', 'submitted_at', 'assignment']
    search_fields = ['assignment__title', 'reviewer__name', 'reviewee__name']
    readonly_fields = ['submitted_at']


@admin.register(AssignmentPlagiarismCheck)
class AssignmentPlagiarismCheckAdmin(admin.ModelAdmin):
    list_display = ['submission', 'status', 'similarity_percentage', 'checked_by', 'checked_at']
    list_filter = ['status', 'checked_at', 'checked_by']
    search_fields = ['submission__student__name', 'submission__assignment__title']
    readonly_fields = ['checked_at']


@admin.register(AssignmentLearningOutcome)
class AssignmentLearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'outcome_code', 'bloom_level', 'weight']
    list_filter = ['bloom_level', 'assignment']
    search_fields = ['outcome_code', 'description', 'assignment__title']
    ordering = ['assignment', 'outcome_code']


@admin.register(AssignmentAnalytics)
class AssignmentAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'submission_rate', 'average_grade', 'plagiarism_rate', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['assignment__title']
    readonly_fields = ['last_updated']


@admin.register(AssignmentNotification)
class AssignmentNotificationAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'assignment__title', 'recipient__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AssignmentSchedule)
class AssignmentScheduleAdmin(admin.ModelAdmin):
    list_display = ['name', 'schedule_type', 'is_active', 'next_run', 'created_by']
    list_filter = ['schedule_type', 'is_active', 'created_by']
    search_fields = ['name', 'description', 'created_by__email']
    readonly_fields = ['last_run', 'next_run']
    filter_horizontal = ['target_programs', 'target_departments', 'target_courses']


@admin.register(AssignmentTemplate)
class AssignmentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'max_marks', 'is_group_assignment', 'is_public', 'created_by']
    list_filter = ['category', 'is_group_assignment', 'is_public', 'created_by']
    search_fields = ['name', 'description', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AssignmentGroup)
class AssignmentGroupAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'group_name', 'leader', 'member_count']
    list_filter = ['assignment']
    search_fields = ['group_name', 'assignment__title', 'leader__name']
    filter_horizontal = ['members']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'
