from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    AcademicProgram, Course, CourseSection, Syllabus, SyllabusTopic, 
    Timetable, CourseEnrollment, AcademicCalendar, BatchCourseEnrollment, CoursePrerequisite
)


@admin.register(AcademicProgram)
class AcademicProgramAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'level', 'department', 'duration_years', 'total_credits', 'status', 'is_active']
    list_filter = ['level', 'department', 'status', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering = ['level', 'name']
    fields = ['name', 'code', 'level', 'department', 'duration_years', 'total_credits', 'description', 'status', 'is_active']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Provide default status in the admin add form
        if not obj:
            form.base_fields['status'].initial = 'ACTIVE'
        return form

    def save_model(self, request, obj, form, change):
        if not obj.status:
            obj.status = 'ACTIVE'
        super().save_model(request, obj, form, change)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'level', 'credits', 'department', 'get_total_sections', 'status', 'created_at']
    list_filter = ['level', 'status', 'department', 'programs']
    search_fields = ['code', 'title', 'description']
    ordering = ['code', 'title']
    filter_horizontal = ['prerequisites', 'programs']
    
    def get_total_sections(self, obj):
        return obj.get_total_sections()
    get_total_sections.short_description = 'Total Sections'


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = [
        'course', 'student_batch', 'section_number_display', 'section_type', 'faculty', 
        'current_enrollment', 'max_students', 'available_seats_display', 'is_active'
    ]
    list_filter = [
        'section_type', 'is_active', 'course__department', 'faculty',
        'student_batch__department', 'student_batch__academic_program'
    ]
    search_fields = [
        'course__code', 'course__title', 'student_batch__batch_name', 
        'faculty__first_name', 'faculty__last_name'
    ]
    ordering = ['course__code', 'student_batch__batch_name']
    list_editable = ['is_active', 'max_students']
    readonly_fields = ['current_enrollment', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'student_batch', 'section_type', 'faculty')
        }),
        ('Capacity Settings', {
            'fields': ('max_students', 'current_enrollment'),
            'description': 'Max students is optional. Leave blank for unlimited capacity.'
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'student_batch', 'student_batch__department', 
            'student_batch__academic_program', 'faculty'
        )
    
    def section_number_display(self, obj):
        """Display section number from student batch"""
        return obj.section_number
    section_number_display.short_description = 'Section'
    
    def available_seats_display(self, obj):
        """Display available seats with color coding"""
        try:
            available = obj.get_available_seats()
            if available is None:
                return format_html('<span style="color: blue;">Unlimited</span>')
            elif int(available) > 0:
                return format_html('<span style="color: green;">{}</span>', int(available))
            else:
                return format_html('<span style="color: red;">Full</span>')
        except (ValueError, TypeError, AttributeError):
            return format_html('<span style="color: #999;">N/A</span>')
    available_seats_display.short_description = 'Available Seats'
    
    def save_model(self, request, obj, form, change):
        # Set current_enrollment to 0 if not provided
        if not change and obj.current_enrollment is None:
            obj.current_enrollment = 0
        super().save_model(request, obj, form, change)


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ['course', 'version', 'academic_year', 'semester', 'status', 'approved_by', 'approved_at']
    list_filter = ['status', 'academic_year', 'semester', 'course__department']
    search_fields = ['course__code', 'course__title', 'learning_objectives']
    ordering = ['-academic_year', '-semester', 'course__code']
    readonly_fields = ['approved_at']
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'APPROVED' and not obj.approved_by:
            obj.approved_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SyllabusTopic)
class SyllabusTopicAdmin(admin.ModelAdmin):
    list_display = ['syllabus', 'week_number', 'title', 'duration_hours', 'order']
    list_filter = ['week_number', 'syllabus__academic_year', 'syllabus__semester']
    search_fields = ['title', 'description', 'syllabus__course__code']
    ordering = ['syllabus__course__code', 'week_number', 'order']


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['course_section', 'timetable_type', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active']
    list_filter = ['timetable_type', 'day_of_week', 'is_active']
    search_fields = ['course_section__course__code', 'room', 'notes']
    ordering = ['day_of_week', 'start_time']
    list_editable = ['is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course_section__course', 'course_section__faculty')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'student_batch_display', 'course_section', 'section_batch_display',
        'status', 'enrollment_type', 'enrollment_date', 'grade', 'attendance_percentage'
    ]
    list_filter = [
        'status', 'enrollment_type', 'course_section__course__department',
        'student__student_batch__department', 'student__student_batch__academic_program'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name', 
        'course_section__course__code', 'student__student_batch__batch_name',
        'course_section__student_batch__batch_name'
    ]
    ordering = ['-enrollment_date', 'student__student_batch__batch_name', 'course_section__course__code']
    list_editable = ['status', 'grade', 'attendance_percentage']
    readonly_fields = ['enrollment_date', 'created_at', 'updated_at', 'student_batch_info', 'section_batch_info']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'student_batch_info')
        }),
        ('Course Information', {
            'fields': ('course_section', 'section_batch_info')
        }),
        ('Enrollment Details', {
            'fields': ('status', 'enrollment_type', 'enrollment_date', 'grade', 'grade_points', 'attendance_percentage')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'student__student_batch', 'student__student_batch__department',
            'student__student_batch__academic_program', 'student__student_batch__academic_year',
            'course_section__course', 'course_section__faculty', 'course_section__student_batch'
        )
    
    def student_batch_display(self, obj):
        """Display student's batch information"""
        if obj.student and obj.student.student_batch:
            batch = obj.student.student_batch
            return format_html(
                '<span style="color: #0066cc; font-weight: bold;">{}</span><br/>'
                '<small style="color: #666;">{}</small>',
                batch.batch_name,
                f"{batch.department.name if batch.department else 'No Dept'} - {batch.academic_program.name if batch.academic_program else 'No Program'}"
            )
        return format_html('<span style="color: #999;">No Batch</span>')
    student_batch_display.short_description = 'Student Batch'
    
    def section_batch_display(self, obj):
        """Display course section's batch information"""
        if obj.course_section and obj.course_section.student_batch:
            batch = obj.course_section.student_batch
            return format_html(
                '<span style="color: #009900; font-weight: bold;">{}</span><br/>'
                '<small style="color: #666;">Section {}</small>',
                batch.batch_name,
                batch.section
            )
        return format_html('<span style="color: #999;">No Batch</span>')
    section_batch_display.short_description = 'Section Batch'
    
    def student_batch_info(self, obj):
        """Display detailed student batch information"""
        if obj.student and obj.student.student_batch:
            batch = obj.student.student_batch
            return format_html(
                '<strong>Batch:</strong> {}<br/>'
                '<strong>Department:</strong> {}<br/>'
                '<strong>Program:</strong> {}<br/>'
                '<strong>Academic Year:</strong> {}<br/>'
                '<strong>Year of Study:</strong> {}<br/>'
                '<strong>Section:</strong> {}',
                batch.batch_name,
                batch.department.name if batch.department else 'Not specified',
                batch.academic_program.name if batch.academic_program else 'Not specified',
                batch.academic_year.year if batch.academic_year else 'Not specified',
                batch.year_of_study,
                batch.section
            )
        return 'No batch assigned'
    student_batch_info.short_description = 'Student Batch Details'
    
    def section_batch_info(self, obj):
        """Display detailed course section batch information"""
        if obj.course_section and obj.course_section.student_batch:
            batch = obj.course_section.student_batch
            return format_html(
                '<strong>Section Batch:</strong> {}<br/>'
                '<strong>Section:</strong> {}<br/>'
                '<strong>Department:</strong> {}<br/>'
                '<strong>Program:</strong> {}',
                batch.batch_name,
                batch.section,
                batch.department.name if batch.department else 'Not specified',
                batch.academic_program.name if batch.academic_program else 'Not specified'
            )
        return 'No batch assigned to section'
    section_batch_info.short_description = 'Section Batch Details'


@admin.register(AcademicCalendar)
class AcademicCalendarAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'start_date', 'end_date', 'academic_year', 'semester', 'is_academic_day']
    list_filter = ['event_type', 'academic_year', 'semester', 'is_academic_day']
    search_fields = ['title', 'description']
    ordering = ['start_date', 'title']
    list_editable = ['is_academic_day']


@admin.register(BatchCourseEnrollment)
class BatchCourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_batch', 'course', 'academic_year', 'semester', 'status', 
        'enrollment_percentage_display', 'auto_enroll_new_students', 'created_by', 'enrollment_date'
    ]
    list_filter = [
        'status', 'academic_year', 'semester', 'auto_enroll_new_students',
        'student_batch__department', 'student_batch__academic_program', 'course__department'
    ]
    search_fields = [
        'student_batch__batch_name', 'course__code', 'course__title',
        'academic_year', 'semester'
    ]
    ordering = ['-enrollment_date', 'student_batch__batch_name', 'course__code']
    list_editable = ['status', 'auto_enroll_new_students']
    readonly_fields = ['enrollment_date', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('student_batch', 'course', 'course_section', 'academic_year', 'semester')
        }),
        ('Enrollment Settings', {
            'fields': ('status', 'auto_enroll_new_students', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'enrollment_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student_batch', 'student_batch__department', 'student_batch__academic_program',
            'course', 'course_section', 'created_by'
        )
    
    def enrollment_percentage_display(self, obj):
        """Display enrollment percentage with color coding"""
        try:
            percentage = float(obj.get_enrollment_percentage())
            if percentage >= 90:
                color = 'green'
            elif percentage >= 70:
                color = 'orange'
            else:
                color = 'red'
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, percentage
            )
        except (ValueError, TypeError, AttributeError):
            return format_html('<span style="color: #999;">N/A</span>')
    enrollment_percentage_display.short_description = 'Enrollment %'
    
    def save_model(self, request, obj, form, change):
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_enrollments', 'deactivate_enrollments', 'enroll_students']
    
    def activate_enrollments(self, request, queryset):
        """Activate selected batch enrollments"""
        updated = queryset.update(status='ACTIVE')
        self.message_user(request, f'{updated} batch enrollments activated.')
    activate_enrollments.short_description = "Activate selected batch enrollments"
    
    def deactivate_enrollments(self, request, queryset):
        """Deactivate selected batch enrollments"""
        updated = queryset.update(status='INACTIVE')
        self.message_user(request, f'{updated} batch enrollments deactivated.')
    deactivate_enrollments.short_description = "Deactivate selected batch enrollments"
    
    def enroll_students(self, request, queryset):
        """Enroll students for selected batch enrollments"""
        total_enrolled = 0
        errors = []
        
        for batch_enrollment in queryset.filter(status='ACTIVE'):
            result = batch_enrollment.enroll_batch_students()
            if result['success']:
                total_enrolled += result['enrolled_count']
            else:
                errors.append(f"{batch_enrollment}: {result['message']}")
        
        message = f'Successfully enrolled {total_enrolled} students.'
        if errors:
            message += f' Errors: {"; ".join(errors)}'
        
        self.message_user(request, message)
    enroll_students.short_description = "Enroll students for selected batch enrollments"


@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = [
        'course', 'prerequisite_course', 'student_batch', 'is_mandatory', 
        'minimum_grade', 'created_at'
    ]
    list_filter = [
        'is_mandatory', 'course__department', 'course__level',
        'prerequisite_course__department', 'student_batch__department'
    ]
    search_fields = [
        'course__code', 'course__title', 'prerequisite_course__code', 
        'prerequisite_course__title', 'student_batch__batch_name'
    ]
    ordering = ['course__code', 'prerequisite_course__code']
    list_editable = ['is_mandatory', 'minimum_grade']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 'prerequisite_course', 'student_batch'
        )
    
    fieldsets = (
        ('Prerequisite Information', {
            'fields': ('course', 'prerequisite_course', 'student_batch')
        }),
        ('Requirements', {
            'fields': ('is_mandatory', 'minimum_grade')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = "CampsHub360 Academic Administration"
admin.site.site_title = "Academic Admin Portal"
admin.site.index_title = "Welcome to Academic Administration Portal"
