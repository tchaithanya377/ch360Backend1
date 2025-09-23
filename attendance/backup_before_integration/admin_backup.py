from django.contrib import admin
from django import forms
from django.db.models import Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest,
    LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
    AttendanceConfiguration, StudentSnapshot, AttendanceStatistics,
    BiometricDevice, BiometricTemplate, AttendanceAuditLog
)
from students.models import Student


class AttendanceRecordForm(forms.ModelForm):
    """Custom form for AttendanceRecord that filters students based on selected session"""
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        widgets = {
            'session': forms.Select(attrs={'onchange': 'filterStudents()'}),
            'student': forms.Select(),
            'mark': forms.Select(),
            'marked_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the session from the form data or instance
        session = None
        if 'session' in self.data:
            try:
                session_id = self.data.get('session')
                if session_id:
                    session = AttendanceSession.objects.get(id=session_id)
            except (ValueError, AttendanceSession.DoesNotExist):
                pass
        elif self.instance.pk and self.instance.session:
            session = self.instance.session
        
        # Filter students based on the session's course section
        if session and session.course_section and session.course_section.student_batch:
            # Only show students from the specific student batch assigned to this course section
            self.fields['student'].queryset = Student.objects.filter(
                student_batch=session.course_section.student_batch
            ).order_by('roll_number')
        else:
            # If no session or no student batch assigned, show all students
            self.fields['student'].queryset = Student.objects.all().order_by('roll_number')


@admin.register(AttendanceCorrectionRequest)
class AttendanceCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'session', 'from_mark', 'to_mark', 'status', 
        'requested_by', 'created_at'
    ]
    list_filter = ['status', 'from_mark', 'to_mark', 'created_at']
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name', 
        'reason'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'requested_by', 'decided_by', 'decided_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Correction Request', {
            'fields': ('student', 'session', 'from_mark', 'to_mark', 'reason', 'status')
        }),
        ('Supporting Documents', {
            'fields': ('supporting_document',),
            'classes': ('collapse',)
        }),
        ('Approval Process', {
            'fields': ('requested_by', 'decided_by', 'decided_at', 'decision_reason'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'leave_type', 'start_date', 'end_date', 'status', 
        'affects_attendance'
    ]
    list_filter = [
        'leave_type', 'status', 'affects_attendance', 'start_date',
        'auto_apply_to_sessions'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name', 
        'reason'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'decided_by', 'decided_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Leave Information', {
            'fields': (
                'student', 'leave_type', 'start_date', 'end_date', 
                'reason', 'status'
            )
        }),
        ('Attendance Impact', {
            'fields': ('affects_attendance', 'auto_apply_to_sessions'),
        }),
        ('Approval Process', {
            'fields': ('decided_by', 'decided_at', 'decision_reason'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = [
        'course_section', 'faculty', 'day_of_week', 'start_time', 
        'end_time', 'room', 'slot_type', 'is_active'
    ]
    list_filter = [
        'day_of_week', 'is_active', 'academic_year', 'semester', 'slot_type'
    ]
    search_fields = [
        'course_section__course__code', 'faculty__first_name', 
        'faculty__last_name', 'room'
    ]
    ordering = ['day_of_week', 'start_time']
    
    fieldsets = (
        ('Slot Information', {
            'fields': (
                'course_section', 'faculty', 'day_of_week', 
                'start_time', 'end_time', 'room'
            )
        }),
        ('Configuration', {
            'fields': ('slot_type', 'max_students', 'is_active'),
        }),
        ('Academic Period', {
            'fields': ('academic_year', 'semester'),
        }),
    )


@admin.register(AcademicCalendarHoliday)
class AcademicCalendarHolidayAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'date', 'is_full_day', 'affects_attendance', 'academic_year'
    ]
    list_filter = [
        'is_full_day', 'affects_attendance', 'academic_year', 'date'
    ]
    search_fields = ['name', 'description']
    ordering = ['-date']
    
    fieldsets = (
        ('Holiday Information', {
            'fields': ('name', 'date', 'is_full_day', 'description')
        }),
        ('Academic Impact', {
            'fields': ('academic_year', 'affects_attendance'),
        }),
    )


@admin.register(StudentSnapshot)
class StudentSnapshotAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'roll_number', 'full_name', 'course_section']
    list_filter = ['session__scheduled_date', 'course_section__course__department']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'roll_number', 'full_name']
    ordering = ['session__scheduled_date', 'roll_number']


@admin.register(AttendanceStatistics)
class AttendanceStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course_section', 'academic_year', 'semester', 
        'attendance_percentage', 'is_eligible_for_exam', 'total_sessions'
    ]
    list_filter = [
        'academic_year', 'semester', 'is_eligible_for_exam', 
        'course_section__course__department'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'course_section__course__code'
    ]
    ordering = ['-academic_year', 'semester', 'student__roll_number']
    readonly_fields = [
        'total_sessions', 'present_count', 'absent_count', 'late_count', 
        'excused_count', 'attendance_percentage', 'is_eligible_for_exam',
        'last_calculated'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'course_section', 'course_section__course'
        )


@admin.register(BiometricDevice)
class BiometricDeviceAdmin(admin.ModelAdmin):
    list_display = [
        'device_id', 'device_name', 'device_type', 'location', 
        'status', 'is_enabled', 'last_seen'
    ]
    list_filter = ['device_type', 'status', 'is_enabled', 'auto_sync']
    search_fields = ['device_id', 'device_name', 'location', 'room']
    ordering = ['device_id']
    readonly_fields = ['last_seen']
    
    fieldsets = (
        ('Device Information', {
            'fields': ('device_id', 'device_name', 'device_type', 'location', 'room')
        }),
        ('Status & Configuration', {
            'fields': ('status', 'is_enabled', 'auto_sync', 'sync_interval_minutes')
        }),
        ('Network Configuration', {
            'fields': ('ip_address', 'port', 'api_endpoint', 'api_key')
        }),
        ('Technical Details', {
            'fields': ('firmware_version', 'last_seen'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BiometricTemplate)
class BiometricTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'device', 'quality_score', 'is_active', 
        'enrolled_at', 'last_used'
    ]
    list_filter = ['is_active', 'device__device_type', 'enrolled_at']
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'device__device_id', 'template_hash'
    ]
    ordering = ['-enrolled_at']
    readonly_fields = ['template_hash', 'enrolled_at', 'last_used']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'device'
        )


@admin.register(AttendanceAuditLog)
class AttendanceAuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'entity_type', 'entity_id', 'action', 'performed_by', 
        'created_at', 'source', 'ip_address'
    ]
    list_filter = [
        'entity_type', 'action', 'source', 'created_at',
        'performed_by'
    ]
    search_fields = [
        'entity_type', 'entity_id', 'performed_by__username', 
        'performed_by__email', 'ip_address'
    ]
    ordering = ['-created_at']
    readonly_fields = [
        'entity_type', 'entity_id', 'action', 'performed_by', 
        'before', 'after', 'created_at', 'source', 
        'ip_address', 'user_agent', 'session_id', 'student_id'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('performed_by')


# Enhanced AttendanceSession Admin
@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = [
        'course_section', 'scheduled_date', 'start_datetime', 'end_datetime', 
        'room', 'status', 'faculty', 'attendance_count'
    ]
    list_filter = [
        'scheduled_date', 'status', 'course_section__course__department', 
        'faculty', 'auto_opened', 'auto_closed', 'makeup'
    ]
    search_fields = [
        'course_section__course__code', 'room', 'notes', 
        'faculty__first_name', 'faculty__last_name'
    ]
    ordering = ['-scheduled_date', 'start_datetime']
    readonly_fields = [
        'auto_opened', 'auto_closed', 'qr_token', 'qr_expires_at',
        'qr_generated_at', 'offline_sync_token', 'last_sync_at'
    ]
    
    fieldsets = (
        ('Session Information', {
            'fields': (
                'course_section', 'faculty', 'timetable_slot',
                'scheduled_date', 'start_datetime', 'end_datetime',
                'actual_start_datetime', 'actual_end_datetime'
            )
        }),
        ('Location & Status', {
            'fields': ('room', 'status', 'notes', 'makeup')
        }),
        ('QR Code Configuration', {
            'fields': ('qr_token', 'qr_expires_at', 'qr_generated_at'),
            'classes': ('collapse',)
        }),
        ('Biometric Configuration', {
            'fields': ('biometric_enabled', 'biometric_device_id'),
            'classes': ('collapse',)
        }),
        ('Offline Sync', {
            'fields': ('offline_sync_token', 'last_sync_at'),
            'classes': ('collapse',)
        }),
        ('Automation', {
            'fields': ('auto_opened', 'auto_closed'),
            'classes': ('collapse',)
        }),
    )
    
    def attendance_count(self, obj):
        if obj.pk:
            count = obj.attendance_records.count()
            return format_html(
                '<a href="{}?session__id__exact={}">{} records</a>',
                reverse('admin:attendance_attendancerecord_changelist'),
                obj.pk,
                count
            )
        return '0 records'
    attendance_count.short_description = 'Attendance Records'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course_section', 'course_section__course', 'faculty'
        ).prefetch_related('attendance_records')


# Enhanced AttendanceRecord Admin
@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    form = AttendanceRecordForm
    list_display = [
        'session', 'student', 'mark', 'marked_at', 'source', 
        'device_type', 'sync_status'
    ]
    list_filter = [
        'mark', 'source', 'device_type', 'sync_status',
        'session__scheduled_date', 'marked_at'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'session__course_section__course__code', 'client_uuid'
    ]
    ordering = ['session__scheduled_date', 'student__roll_number']
    readonly_fields = [
        'marked_at', 'marked_by', 'last_modified_by', 'ip_address', 
        'user_agent', 'client_uuid', 'vendor_event_id'
    ]
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('session', 'student', 'mark', 'marked_at', 'notes')
        }),
        ('Device & Location', {
            'fields': (
                'source', 'device_id', 'device_type', 'ip_address',
                'location_lat', 'location_lng'
            )
        }),
        ('User & Session Info', {
            'fields': ('user_agent', 'client_uuid', 'session_id'),
            'classes': ('collapse',)
        }),
        ('Vendor Integration', {
            'fields': ('vendor_event_id', 'vendor_data'),
            'classes': ('collapse',)
        }),
        ('Sync & Modification', {
            'fields': ('sync_status', 'marked_by', 'last_modified_by'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        js = ('admin/js/attendance_record_filter.js',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'session', 'session__course_section', 'student'
        )


# Enhanced AttendanceConfiguration Admin
@admin.register(AttendanceConfiguration)
class AttendanceConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'key', 'value', 'data_type', 'is_active', 'updated_by', 'updated_at'
    ]
    list_filter = ['data_type', 'is_active']
    search_fields = ['key', 'description']
    ordering = ['key']
    readonly_fields = ['updated_by', 'updated_at']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'value', 'data_type', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set updated_by on creation
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Custom Admin Actions
@admin.action(description='Mark selected sessions as open')
def open_sessions(modeladmin, request, queryset):
    """Admin action to open multiple sessions"""
    updated = queryset.filter(status='scheduled').update(status='open')
    modeladmin.message_user(
        request, 
        f'{updated} sessions have been marked as open.'
    )


@admin.action(description='Mark selected sessions as closed')
def close_sessions(modeladmin, request, queryset):
    """Admin action to close multiple sessions"""
    updated = queryset.filter(status='open').update(status='closed')
    modeladmin.message_user(
        request, 
        f'{updated} sessions have been marked as closed.'
    )


@admin.action(description='Generate QR codes for selected sessions')
def generate_qr_codes(modeladmin, request, queryset):
    """Admin action to generate QR codes for sessions"""
    from .tasks import generate_qr_for_session
    
    count = 0
    for session in queryset.filter(status__in=['scheduled', 'open']):
        generate_qr_for_session.delay(session.id)
        count += 1
    
    modeladmin.message_user(
        request, 
        f'QR code generation initiated for {count} sessions.'
    )


@admin.action(description='Calculate statistics for selected students')
def calculate_statistics(modeladmin, request, queryset):
    """Admin action to calculate attendance statistics"""
    from .tasks import calculate_attendance_statistics
    
    student_ids = list(queryset.values_list('id', flat=True))
    calculate_attendance_statistics.delay(student_ids=student_ids)
    
    modeladmin.message_user(
        request, 
        f'Statistics calculation initiated for {len(student_ids)} students.'
    )


# Add actions to the enhanced admin classes
AttendanceSessionAdmin.actions = [open_sessions, close_sessions, generate_qr_codes]
AttendanceStatisticsAdmin.actions = [calculate_statistics]


# Custom Admin Site Configuration
class AttendanceAdminSite(admin.AdminSite):
    """Custom admin site for attendance management"""
    site_header = "CampsHub360 Attendance Management"
    site_title = "Attendance Admin"
    index_title = "Attendance System Administration"


# Admin Dashboard Customization
def get_admin_stats():
    """Get statistics for admin dashboard"""
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_sessions': AttendanceSession.objects.count(),
        'open_sessions': AttendanceSession.objects.filter(status='open').count(),
        'today_sessions': AttendanceSession.objects.filter(scheduled_date=today).count(),
        'week_sessions': AttendanceSession.objects.filter(
            scheduled_date__gte=week_ago
        ).count(),
        'total_records': AttendanceRecord.objects.count(),
        'today_records': AttendanceRecord.objects.filter(
            marked_at__date=today
        ).count(),
        'pending_corrections': AttendanceCorrectionRequest.objects.filter(
            status='pending'
        ).count(),
        'pending_leaves': LeaveApplication.objects.filter(
            status='pending'
        ).count(),
    }
    
    return stats


# Add custom admin views
def attendance_dashboard(request):
    """Custom admin dashboard view"""
    from django.shortcuts import render
    
    stats = get_admin_stats()
    context = {
        'title': 'Attendance Dashboard',
        'stats': stats,
    }
    return render(request, 'admin/attendance/dashboard.html', context)

