from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
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
        'title', 'course_section', 'academic_year', 'semester', 'due_date', 'status', 
        'max_marks', 'submission_count', 'created_at'
    ]
    list_editable = ['due_date', 'status', 'max_marks']
    list_filter = [
        'status', 'category', 'faculty__department', 'course', 'course_section',
        'due_date', 'created_at', 'academic_year', 'semester'
    ]
    search_fields = [
        'title', 'description', 'faculty__name', 
        'faculty__apaar_faculty_id'
    ]
    readonly_fields = ['created_at', 'updated_at', 'submission_count']
    exclude = ('faculty', 'department', 'course')
    filter_horizontal = [
        'assigned_to_programs', 'assigned_to_departments', 
        'assigned_to_courses', 'assigned_to_course_sections', 'assigned_to_students'
    ]
    autocomplete_fields = ['course_section', 'academic_year', 'semester']
    list_select_related = ['course_section', 'academic_year', 'semester']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'course_section')
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
    
    def save_model(self, request, obj, form, change):
        """Auto-derive hidden linking fields from selected course_section."""
        # Auto-set faculty from current user on create if missing
        if not obj.faculty_id and hasattr(request.user, 'faculty_profile'):
            obj.faculty = request.user.faculty_profile
        # Derive department/course/year/semester from course_section
        try:
            if obj.course_section:
                obj.course = obj.course_section.course
                try:
                    obj.department = obj.course_section.course.department
                except Exception:
                    pass
                batch = obj.course_section.student_batch
                if batch and hasattr(batch, 'academic_year'):
                    obj.academic_year = batch.academic_year
                if batch and hasattr(batch, 'get_semester_object'):
                    sem_obj = batch.get_semester_object()
                    if sem_obj:
                        obj.semester = sem_obj
                # If faculty still missing, derive from section faculty
                if not obj.faculty_id and getattr(obj.course_section, 'faculty_id', None):
                    obj.faculty_id = obj.course_section.faculty_id
        except Exception:
            pass
        # Final guard: ensure faculty resolved
        if not obj.faculty_id:
            raise ValidationError("Faculty could not be determined. Please select a course section with an assigned faculty.")
        super().save_model(request, obj, form, change)


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


@admin.register(AssignmentGrade)
class AssignmentGradeAdmin(admin.ModelAdmin):
    list_display = [
        'submission', 'marks_obtained', 'max_marks', 'percentage_display', 'grade_letter', 
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

    def percentage_display(self, obj):
        try:
            max_m = obj.submission.assignment.max_marks
            if max_m and obj.marks_obtained is not None and max_m > 0:
                return f"{round((obj.marks_obtained / max_m) * 100, 2)}%"
        except Exception:
            return '-'
        return '-'
    percentage_display.short_description = 'Percentage'


"""
Minimal admin: keep only Categories, Assignments, Submissions, Grades.
Hide advanced models to simplify the admin UI per product direction.
"""

from django.contrib.admin.sites import NotRegistered

def _safe_unregister(model):
    try:
        admin.site.unregister(model)
    except NotRegistered:
        pass

# Hide advanced/optional models
_safe_unregister(AssignmentFile)
_safe_unregister(AssignmentComment)
_safe_unregister(AssignmentRubric)
_safe_unregister(AssignmentRubricGrade)
_safe_unregister(AssignmentPeerReview)
_safe_unregister(AssignmentPlagiarismCheck)
_safe_unregister(AssignmentLearningOutcome)
_safe_unregister(AssignmentAnalytics)
_safe_unregister(AssignmentNotification)
_safe_unregister(AssignmentSchedule)
_safe_unregister(AssignmentTemplate)
_safe_unregister(AssignmentGroup)
