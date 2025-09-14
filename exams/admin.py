from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    ExamSession, ExamSchedule, ExamRoom, ExamRoomAllocation,
    ExamStaffAssignment, StudentDue, ExamRegistration, HallTicket,
    ExamAttendance, ExamViolation, ExamResult
)


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'session_type', 'academic_year', 'semester', 'start_date', 'end_date', 'status', 'is_active']
    list_filter = ['session_type', 'academic_year', 'semester', 'status', 'is_active']
    search_fields = ['name', 'academic_year', 'description']
    list_editable = ['status', 'is_active']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'session_type', 'academic_year', 'semester', 'description')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'registration_start', 'registration_end')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'exam_type', 'exam_date', 'start_time', 'end_time', 'status', 'is_online']
    list_filter = ['exam_session', 'exam_type', 'status', 'is_online', 'exam_date']
    search_fields = ['course__code', 'course__title', 'title', 'description']
    list_editable = ['status']
    date_hierarchy = 'exam_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('exam_session', 'course', 'exam_type', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('exam_date', 'start_time', 'end_time', 'duration_minutes')
        }),
        ('Marks & Capacity', {
            'fields': ('total_marks', 'passing_marks', 'max_students')
        }),
        ('Online Exam', {
            'fields': ('is_online', 'online_platform'),
            'classes': ('collapse',)
        }),
        ('Status & Instructions', {
            'fields': ('status', 'instructions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamRoom)
class ExamRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'room_type', 'building', 'floor', 'capacity', 'is_accessible', 'is_active']
    list_filter = ['room_type', 'building', 'floor', 'is_accessible', 'has_projector', 'has_air_conditioning', 'is_active']
    search_fields = ['name', 'building', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'room_type', 'capacity', 'description')
        }),
        ('Location', {
            'fields': ('building', 'floor')
        }),
        ('Features', {
            'fields': ('is_accessible', 'has_projector', 'has_air_conditioning')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamRoomAllocation)
class ExamRoomAllocationAdmin(admin.ModelAdmin):
    list_display = ['exam_schedule', 'exam_room', 'allocated_capacity', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'exam_room__building', 'exam_room__room_type']
    search_fields = ['exam_schedule__title', 'exam_room__name', 'exam_room__building']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Allocation', {
            'fields': ('exam_schedule', 'exam_room', 'allocated_capacity', 'is_primary')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamStaffAssignment)
class ExamStaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ['faculty', 'exam_schedule', 'role', 'exam_room', 'is_available', 'assigned_date']
    list_filter = ['role', 'is_available', 'exam_room__building', 'assigned_date']
    search_fields = ['faculty__user__first_name', 'faculty__user__last_name', 'exam_schedule__title']
    list_editable = ['is_available']
    readonly_fields = ['assigned_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('exam_schedule', 'faculty', 'role', 'exam_room')
        }),
        ('Status', {
            'fields': ('is_available', 'notes')
        }),
        ('Timestamps', {
            'fields': ('assigned_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentDue)
class StudentDueAdmin(admin.ModelAdmin):
    list_display = ['student', 'due_type', 'amount', 'paid_amount', 'remaining_amount', 'due_date', 'status', 'is_overdue']
    list_filter = ['due_type', 'status', 'due_date']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'description']
    list_editable = ['status', 'paid_amount']
    readonly_fields = ['remaining_amount', 'is_overdue', 'created_at', 'updated_at']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Student & Due', {
            'fields': ('student', 'due_type', 'amount', 'paid_amount')
        }),
        ('Timeline', {
            'fields': ('due_date', 'status')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Calculated Fields', {
            'fields': ('remaining_amount', 'is_overdue'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamRegistration)
class ExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam_schedule', 'status', 'registration_date', 'approved_by', 'approved_date']
    list_filter = ['status', 'registration_date', 'exam_schedule__exam_session', 'exam_schedule__exam_type']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'exam_schedule__title']
    list_editable = ['status']
    readonly_fields = ['registration_date', 'created_at', 'updated_at']
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Registration', {
            'fields': ('student', 'exam_schedule', 'status')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_date', 'rejection_reason')
        }),
        ('Special Requirements', {
            'fields': ('special_requirements',)
        }),
        ('Timestamps', {
            'fields': ('registration_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HallTicket)
class HallTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'student_info', 'exam_info', 'exam_room', 'seat_number', 'status', 'generated_date']
    list_filter = ['status', 'exam_room__building', 'generated_date']
    search_fields = ['ticket_number', 'exam_registration__student__roll_number', 'exam_registration__student__first_name']
    list_editable = ['status', 'seat_number']
    readonly_fields = ['ticket_number', 'generated_date', 'created_at', 'updated_at']
    date_hierarchy = 'generated_date'
    
    def student_info(self, obj):
        student = obj.exam_registration.student
        return f"{student.roll_number} - {student.first_name} {student.last_name}"
    student_info.short_description = 'Student'
    
    def exam_info(self, obj):
        exam = obj.exam_registration.exam_schedule
        return f"{exam.course.code} - {exam.title}"
    exam_info.short_description = 'Exam'
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'exam_registration', 'status')
        }),
        ('Room & Seat', {
            'fields': ('exam_room', 'seat_number')
        }),
        ('Timeline', {
            'fields': ('generated_date', 'printed_date', 'issued_date', 'used_date')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamAttendance)
class ExamAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_info', 'exam_info', 'status', 'check_in_time', 'check_out_time', 'invigilator']
    list_filter = ['status', 'check_in_time', 'exam_registration__exam_schedule__exam_date']
    search_fields = ['exam_registration__student__roll_number', 'exam_registration__student__first_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def student_info(self, obj):
        student = obj.exam_registration.student
        return f"{student.roll_number} - {student.first_name} {student.last_name}"
    student_info.short_description = 'Student'
    
    def exam_info(self, obj):
        exam = obj.exam_registration.exam_schedule
        return f"{exam.course.code} - {exam.title}"
    exam_info.short_description = 'Exam'
    
    fieldsets = (
        ('Attendance', {
            'fields': ('exam_registration', 'status')
        }),
        ('Timing', {
            'fields': ('check_in_time', 'check_out_time')
        }),
        ('Supervision', {
            'fields': ('invigilator', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamViolation)
class ExamViolationAdmin(admin.ModelAdmin):
    list_display = ['student_info', 'exam_info', 'violation_type', 'severity', 'reported_by', 'reported_at', 'is_resolved']
    list_filter = ['violation_type', 'severity', 'is_resolved', 'reported_at']
    search_fields = ['exam_registration__student__roll_number', 'description', 'action_taken']
    list_editable = ['is_resolved']
    readonly_fields = ['reported_at', 'created_at', 'updated_at']
    date_hierarchy = 'reported_at'
    
    def student_info(self, obj):
        student = obj.exam_registration.student
        return f"{student.roll_number} - {student.first_name} {student.last_name}"
    student_info.short_description = 'Student'
    
    def exam_info(self, obj):
        exam = obj.exam_registration.exam_schedule
        return f"{exam.course.code} - {exam.title}"
    exam_info.short_description = 'Exam'
    
    fieldsets = (
        ('Violation Details', {
            'fields': ('exam_registration', 'violation_type', 'severity', 'description')
        }),
        ('Reporting', {
            'fields': ('reported_by', 'reported_at')
        }),
        ('Resolution', {
            'fields': ('action_taken', 'penalty', 'is_resolved', 'resolved_at', 'resolved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student_info', 'exam_info', 'marks_obtained', 'grade', 'percentage', 'is_pass', 'is_published']
    list_filter = ['grade', 'is_pass', 'is_published', 'evaluated_at']
    search_fields = ['exam_registration__student__roll_number', 'exam_registration__student__first_name']
    list_editable = ['is_published']
    readonly_fields = ['percentage', 'grade', 'is_pass', 'created_at', 'updated_at']
    
    def student_info(self, obj):
        student = obj.exam_registration.student
        return f"{student.roll_number} - {student.first_name} {student.last_name}"
    student_info.short_description = 'Student'
    
    def exam_info(self, obj):
        exam = obj.exam_registration.exam_schedule
        return f"{exam.course.code} - {exam.title}"
    exam_info.short_description = 'Exam'
    
    fieldsets = (
        ('Result', {
            'fields': ('exam_registration', 'marks_obtained')
        }),
        ('Grade & Status', {
            'fields': ('grade', 'percentage', 'is_pass')
        }),
        ('Evaluation', {
            'fields': ('evaluated_by', 'evaluated_at', 'remarks')
        }),
        ('Publication', {
            'fields': ('is_published', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.marks_obtained is not None:
            obj.calculate_grade_and_percentage()
        super().save_model(request, obj, form, change)


# Custom admin site configuration
admin.site.site_header = "CampsHub360 Exam Management"
admin.site.site_title = "Exam Admin"
admin.site.index_title = "Welcome to Exam Management Portal"
