from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import (
    Assignment, AssignmentSubmission, AssignmentFile, 
    AssignmentGrade, AssignmentComment, AssignmentCategory
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
