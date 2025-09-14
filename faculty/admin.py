from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Faculty, FacultySubject, FacultySchedule, FacultyLeave,
    FacultyPerformance, FacultyDocument, CustomField, CustomFieldValue
)
from departments.models import Department


@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    """Admin interface for CustomField model"""
    list_display = ['name', 'label', 'field_type', 'required', 'is_active', 'order']
    list_filter = ['field_type', 'required', 'is_active']
    search_fields = ['name', 'label', 'help_text']
    ordering = ['order', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'label', 'field_type', 'required')
        }),
        ('Field Configuration', {
            'fields': ('default_value', 'choices', 'help_text', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    """Admin interface for CustomFieldValue model"""
    list_display = ['faculty', 'custom_field', 'value', 'created_at']
    list_filter = ['custom_field', 'custom_field__field_type']
    search_fields = ['faculty__name', 'custom_field__label', 'value']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Field Information', {
            'fields': ('faculty', 'custom_field', 'value')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class FacultyAdminForm(forms.ModelForm):
    """Custom form for Faculty admin to use Department table"""
    
    class Meta:
        model = Faculty
        fields = '__all__'
        exclude = ['department']  # Exclude the old department field
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up department_ref choices from Department table
        self.fields['department_ref'].queryset = Department.objects.filter(
            is_active=True, 
            status='ACTIVE'
        ).order_by('name')
        self.fields['department_ref'].empty_label = "Select Department"
        self.fields['department_ref'].help_text = "Select department from Department table"
        self.fields['department_ref'].required = True
        
        # Make department_ref more prominent
        self.fields['department_ref'].widget.attrs.update({
            'class': 'form-control',
            'style': 'font-weight: bold; background-color: #e3f2fd;'
        })
        
        # Add a label to make it clear this is the main department field
        self.fields['department_ref'].label = "Department (from Department table)"


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    """Admin interface for Faculty model"""
    form = FacultyAdminForm
    
    list_display = [
        'name', 'apaar_faculty_id', 'employee_id', 'present_designation',
        'get_department_name', 'currently_associated', 'status', 'email', 'phone_number'
    ]
    list_filter = [
        'status', 'department_ref', 'employment_type', 'designation',
        'is_head_of_department', 'is_mentor', 'gender', 'currently_associated',
        'nature_of_association', 'contractual_full_time_part_time'
    ]
    search_fields = [
        'name', 'first_name', 'last_name', 'middle_name', 'employee_id',
        'apaar_faculty_id', 'email', 'phone_number', 'pan_no', 'department_ref__name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'user', 'full_name', 'is_active_faculty'
    ]
    ordering = ['name']
    
    def get_department_name(self, obj):
        """Display department name from department_ref"""
        if obj.department_ref:
            return obj.department_ref.name
        return obj.get_department_display() if obj.department else '-'
    get_department_name.short_description = 'Department'
    get_department_name.admin_order_field = 'department_ref__name'

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'apaar_faculty_id', 'employee_id', 'pan_no',
                'first_name', 'last_name', 'middle_name', 'date_of_birth', 'gender'
            )
        }),
        ('Academic Information', {
            'fields': (
                'highest_degree', 'university', 'area_of_specialization',
                'highest_qualification', 'specialization', 'year_of_completion'
            )
        }),
        ('Employment Information', {
            'fields': (
                'date_of_joining_institution', 'designation_at_joining', 'present_designation',
                'date_designated_as_professor', 'nature_of_association',
                'contractual_full_time_part_time', 'currently_associated', 'date_of_leaving',
                'experience_in_current_institute', 'designation', 'department_ref',
                'employment_type', 'status', 'date_of_joining', 'experience_years',
                'previous_institution'
            )
        }),
        ('Contact Information', {
            'fields': (
                'email', 'phone_number', 'alternate_phone', 'address_line_1',
                'address_line_2', 'city', 'state', 'postal_code', 'country'
            )
        }),
        ('Professional Information', {
            'fields': (
                'achievements', 'research_interests', 'is_head_of_department',
                'is_mentor', 'mentor_for_grades'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relationship'
            )
        }),
        ('Additional Information', {
            'fields': ('profile_picture', 'bio', 'notes')
        }),
        ('System Information', {
            'fields': ('user', 'full_name', 'is_active_faculty'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['reset_passwords', 'activate_faculty', 'deactivate_faculty']

    def reset_passwords(self, request, queryset):
        """Reset passwords for selected faculty members"""
        count = 0
        for faculty in queryset:
            if faculty.user:
                faculty.user.set_password('Campus@360')
                faculty.user.save()
                count += 1
        self.message_user(request, f'Successfully reset passwords for {count} faculty members.')
    reset_passwords.short_description = "Reset passwords to default"

    def activate_faculty(self, request, queryset):
        """Activate selected faculty members"""
        updated = queryset.update(status='ACTIVE', currently_associated=True)
        self.message_user(request, f'Successfully activated {updated} faculty members.')
    activate_faculty.short_description = "Activate selected faculty members"

    def deactivate_faculty(self, request, queryset):
        """Deactivate selected faculty members"""
        updated = queryset.update(status='INACTIVE', currently_associated=False)
        self.message_user(request, f'Successfully deactivated {updated} faculty members.')
    deactivate_faculty.short_description = "Deactivate selected faculty members"


@admin.register(FacultySubject)
class FacultySubjectAdmin(admin.ModelAdmin):
    """Admin interface for FacultySubject model"""
    list_display = ['faculty', 'subject_name', 'grade_level', 'academic_year', 'is_primary_subject']
    list_filter = ['grade_level', 'academic_year', 'is_primary_subject']
    search_fields = ['faculty__name', 'subject_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['faculty__name', 'subject_name']


@admin.register(FacultySchedule)
class FacultyScheduleAdmin(admin.ModelAdmin):
    """Admin interface for FacultySchedule model"""
    list_display = [
        'faculty', 'day_of_week', 'start_time', 'end_time', 'subject',
        'grade_level', 'room_number', 'is_online'
    ]
    list_filter = ['day_of_week', 'grade_level', 'is_online']
    search_fields = ['faculty__name', 'subject', 'room_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['faculty__name', 'day_of_week', 'start_time']


@admin.register(FacultyLeave)
class FacultyLeaveAdmin(admin.ModelAdmin):
    """Admin interface for FacultyLeave model"""
    list_display = [
        'faculty', 'leave_type', 'start_date', 'end_date', 'status',
        'approved_by', 'leave_days'
    ]
    list_filter = ['leave_type', 'status', 'approved_by']
    search_fields = ['faculty__name', 'reason']
    readonly_fields = ['id', 'created_at', 'updated_at', 'leave_days']
    ordering = ['-start_date']

    actions = ['approve_leaves', 'reject_leaves']

    class Form(forms.ModelForm):
        """Custom form to provide calendar date pickers for leave dates"""
        class Meta:
            from .models import FacultyLeave
            model = FacultyLeave
            fields = '__all__'
            widgets = {
                'start_date': AdminDateWidget(),
                'end_date': AdminDateWidget(),
            }

    form = Form

    fieldsets = (
        ('Leave Details', {
            'fields': ('faculty', 'leave_type', 'reason', 'start_date', 'end_date')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at', 'leave_days'),
            'classes': ('collapse',)
        }),
    )

    def approve_leaves(self, request, queryset):
        """Approve selected leave requests"""
        count = 0
        for leave in queryset.filter(status='PENDING'):
            leave.status = 'APPROVED'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()
            count += 1
        self.message_user(request, f'Successfully approved {count} leave requests.')
    approve_leaves.short_description = "Approve selected leave requests"

    def reject_leaves(self, request, queryset):
        """Reject selected leave requests"""
        updated = queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, f'Successfully rejected {updated} leave requests.')
    reject_leaves.short_description = "Reject selected leave requests"


@admin.register(FacultyPerformance)
class FacultyPerformanceAdmin(admin.ModelAdmin):
    """Admin interface for FacultyPerformance model"""
    list_display = [
        'faculty', 'academic_year', 'evaluation_period', 'overall_score',
        'evaluated_by', 'evaluation_date'
    ]
    list_filter = ['academic_year', 'evaluation_period', 'evaluated_by']
    search_fields = ['faculty__name', 'academic_year']
    readonly_fields = ['id', 'created_at', 'updated_at', 'overall_score']
    ordering = ['-evaluation_date']

    fieldsets = (
        ('Basic Information', {
            'fields': ('faculty', 'academic_year', 'evaluation_period')
        }),
        ('Evaluation Scores', {
            'fields': (
                'teaching_effectiveness', 'student_satisfaction', 'research_contribution',
                'administrative_work', 'professional_development', 'overall_score'
            )
        }),
        ('Assessment Details', {
            'fields': ('strengths', 'areas_for_improvement', 'recommendations')
        }),
        ('Evaluation Information', {
            'fields': ('evaluated_by', 'evaluation_date', 'comments')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FacultyDocument)
class FacultyDocumentAdmin(admin.ModelAdmin):
    """Admin interface for FacultyDocument model"""
    list_display = [
        'faculty', 'document_type', 'title', 'is_verified', 'verified_by',
        'verified_at'
    ]
    list_filter = ['document_type', 'is_verified', 'verified_by']
    search_fields = ['faculty__name', 'title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    actions = ['verify_documents']

    def verify_documents(self, request, queryset):
        """Verify selected documents"""
        count = 0
        for document in queryset.filter(is_verified=False):
            document.is_verified = True
            document.verified_by = request.user
            document.verified_at = timezone.now()
            document.save()
            count += 1
        self.message_user(request, f'Successfully verified {count} documents.')
    verify_documents.short_description = "Verify selected documents"
