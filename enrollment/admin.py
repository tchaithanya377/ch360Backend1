from django.contrib import admin
from .models import (
    EnrollmentRule, CourseAssignment, FacultyAssignment, StudentEnrollmentPlan,
    PlannedCourse, EnrollmentRequest, WaitlistEntry
)


@admin.register(EnrollmentRule)
class EnrollmentRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'department', 'academic_program', 'academic_year', 'semester', 'is_active']
    list_filter = ['rule_type', 'department', 'academic_program', 'academic_year', 'semester', 'is_active']
    search_fields = ['name', 'description', 'department__name', 'academic_program__name']
    ordering = ['academic_year', 'semester', 'rule_type']
    list_editable = ['is_active']


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'department', 'academic_program', 'academic_year', 'semester', 'year_of_study', 'assignment_type', 'is_active']
    list_filter = ['assignment_type', 'department', 'academic_program', 'academic_year', 'semester', 'year_of_study', 'is_active']
    search_fields = ['course__code', 'course__title', 'department__name', 'academic_program__name']
    ordering = ['academic_year', 'semester', 'year_of_study', 'course__code']
    list_editable = ['is_active', 'assignment_type']


@admin.register(FacultyAssignment)
class FacultyAssignmentAdmin(admin.ModelAdmin):
    list_display = ['faculty', 'course_section', 'status', 'workload_hours', 'is_primary', 'assignment_date']
    list_filter = ['status', 'is_primary', 'faculty__department_ref']
    search_fields = ['faculty__first_name', 'faculty__last_name', 'course_section__course__code', 'course_section__section_number']
    ordering = ['-assignment_date', 'faculty__first_name']
    list_editable = ['status', 'workload_hours', 'is_primary']
    readonly_fields = ['assignment_date', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'faculty', 'course_section__course', 'course_section__faculty'
        )


@admin.register(StudentEnrollmentPlan)
class StudentEnrollmentPlanAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_program', 'academic_year', 'semester', 'year_of_study', 'status', 'total_credits', 'advisor']
    list_filter = ['status', 'academic_program', 'academic_year', 'semester', 'year_of_study', 'advisor__department_ref']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'academic_program__name']
    ordering = ['-academic_year', '-semester', 'student__roll_number']
    list_editable = ['status', 'advisor']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'academic_program', 'advisor'
        )


@admin.register(PlannedCourse)
class PlannedCourseAdmin(admin.ModelAdmin):
    list_display = ['enrollment_plan', 'course', 'priority', 'is_mandatory', 'created_at']
    list_filter = ['is_mandatory', 'priority', 'course__department', 'enrollment_plan__academic_year', 'enrollment_plan__semester']
    search_fields = ['course__code', 'course__title', 'enrollment_plan__student__roll_number']
    ordering = ['enrollment_plan__academic_year', 'enrollment_plan__semester', 'priority', 'course__code']
    list_editable = ['priority', 'is_mandatory']


@admin.register(EnrollmentRequest)
class EnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'course_section', 'status', 'request_date', 'requested_by', 'approved_by', 'approved_at']
    list_filter = ['status', 'course_section__course__department']
    search_fields = ['student__roll_number', 'student__first_name', 'course_section__course__code', 'requested_by__username']
    ordering = ['-request_date']
    list_editable = ['status']
    readonly_fields = ['request_date']
    actions = ['approve_requests', 'reject_requests']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'course_section__course', 'course_section__faculty', 'requested_by', 'approved_by'
        )
    
    def approve_requests(self, request, queryset):
        """Approve selected enrollment requests"""
        approved_count = 0
        for enrollment_request in queryset.filter(status='PENDING'):
            try:
                enrollment_request.approve(request.user)
                approved_count += 1
            except Exception as e:
                self.message_user(request, f"Error approving {enrollment_request}: {str(e)}", level='ERROR')
        
        self.message_user(request, f"Successfully approved {approved_count} enrollment requests.")
    approve_requests.short_description = "Approve selected enrollment requests"
    
    def reject_requests(self, request, queryset):
        """Reject selected enrollment requests"""
        rejected_count = 0
        for enrollment_request in queryset.filter(status='PENDING'):
            try:
                enrollment_request.reject(request.user, "Bulk rejection by admin")
                rejected_count += 1
            except Exception as e:
                self.message_user(request, f"Error rejecting {enrollment_request}: {str(e)}", level='ERROR')
        
        self.message_user(request, f"Successfully rejected {rejected_count} enrollment requests.")
    reject_requests.short_description = "Reject selected enrollment requests"


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ['student', 'course_section', 'position', 'added_date', 'is_active']
    list_filter = ['is_active', 'course_section__course__department']
    search_fields = ['student__roll_number', 'student__first_name', 'course_section__course__code']
    ordering = ['course_section__course__code', 'position', 'added_date']
    list_editable = ['is_active']
    actions = ['move_to_enrollment']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'course_section__course', 'course_section__faculty'
        )
    
    def move_to_enrollment(self, request, queryset):
        """Move selected waitlist entries to enrollment if possible"""
        moved_count = 0
        for waitlist_entry in queryset.filter(is_active=True, position=1):
            try:
                if waitlist_entry.move_to_enrollment():
                    moved_count += 1
            except Exception as e:
                self.message_user(request, f"Error moving {waitlist_entry}: {str(e)}", level='ERROR')
        
        self.message_user(request, f"Successfully moved {moved_count} students from waitlist to enrollment.")
    move_to_enrollment.short_description = "Move selected waitlist entries to enrollment"
