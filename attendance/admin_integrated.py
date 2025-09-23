"""
Enhanced Admin Interface for Integrated Academic System
Provides centralized management of Academic Periods, Timetable, and Attendance
"""

from django.contrib import admin
from django import forms
from django.db.models import Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import date, timedelta

from .models_integrated import (
    AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord
)
from students.models import AcademicYear, Semester
from academics.models import CourseSection
from faculty.models import Faculty


# =============================================================================
# ACADEMIC PERIOD ADMIN
# =============================================================================

class AcademicPeriodForm(forms.ModelForm):
    """Custom form for Academic Period with validation"""
    
    class Meta:
        model = AcademicPeriod
        fields = '__all__'
        widgets = {
            'period_start': forms.DateInput(attrs={'type': 'date'}),
            'period_end': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        is_current = cleaned_data.get('is_current')
        
        if period_start and period_end:
            if period_start >= period_end:
                raise forms.ValidationError("Period start date must be before end date")
        
        if is_current:
            # Check if another period is already current
            existing_current = AcademicPeriod.objects.filter(
                is_current=True
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_current.exists():
                raise forms.ValidationError("Only one academic period can be current")
        
        return cleaned_data


@admin.register(AcademicPeriod)
class AcademicPeriodAdmin(admin.ModelAdmin):
    form = AcademicPeriodForm
    list_display = [
        'display_name', 'academic_year', 'semester', 'period_start', 
        'period_end', 'is_current', 'is_active', 'duration_days'
    ]
    list_filter = [
        'academic_year', 'semester', 'is_current', 'is_active',
        'period_start', 'period_end'
    ]
    search_fields = [
        'academic_year__year', 'semester__name', 'description'
    ]
    ordering = ['-academic_year__year', '-semester__semester_type']
    readonly_fields = ['created_at', 'updated_at', 'duration_days']
    
    fieldsets = (
        ('Academic Period Information', {
            'fields': (
                'academic_year', 'semester', 'period_start', 'period_end'
            )
        }),
        ('Status & Configuration', {
            'fields': ('is_current', 'is_active', 'description')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_days(self, obj):
        """Display duration in days"""
        if obj.period_start and obj.period_end:
            return obj.get_duration_days()
        return '-'
    duration_days.short_description = 'Duration (Days)'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['set_as_current', 'generate_timetable_slots', 'generate_attendance_sessions']
    
    def set_as_current(self, request, queryset):
        """Set selected academic period as current"""
        if queryset.count() > 1:
            self.message_user(request, "Please select only one academic period.", level=messages.ERROR)
            return
        
        period = queryset.first()
        
        # Set all other periods as not current
        AcademicPeriod.objects.filter(is_current=True).update(is_current=False)
        
        # Set selected period as current
        period.is_current = True
        period.save()
        
        self.message_user(
            request, 
            f"Academic period '{period}' has been set as current.",
            level=messages.SUCCESS
        )
    set_as_current.short_description = "Set as current academic period"
    
    def generate_timetable_slots(self, request, queryset):
        """Generate timetable slots for selected academic periods"""
        if request.POST.get('post'):
            # Process the form submission
            periods = queryset.filter(is_active=True)
            slots_created = 0
            
            for period in periods:
                # Get all course sections for this academic period
                course_sections = CourseSection.objects.filter(
                    student_batch__academic_year=period.academic_year
                )
                
                for section in course_sections:
                    # Create basic timetable slots (this would be customized based on requirements)
                    # For now, create a sample slot
                    TimetableSlot.objects.get_or_create(
                        academic_period=period,
                        course_section=section,
                        faculty=section.faculty,
                        day_of_week=0,  # Monday
                        start_time='09:00:00',
                        end_time='10:00:00',
                        defaults={
                            'slot_type': 'LECTURE',
                            'room': 'A101',
                            'is_active': True,
                            'created_by': request.user
                        }
                    )
                    slots_created += 1
            
            self.message_user(
                request,
                f"Generated {slots_created} timetable slots for {periods.count()} academic periods.",
                level=messages.SUCCESS
            )
            return HttpResponseRedirect(request.get_full_path())
        
        # Show confirmation page
        context = {
            'title': 'Generate Timetable Slots',
            'queryset': queryset,
            'action_name': 'generate_timetable_slots',
        }
        return render(request, 'admin/attendance/academicperiod/generate_slots.html', context)
    generate_timetable_slots.short_description = "Generate timetable slots"
    
    def generate_attendance_sessions(self, request, queryset):
        """Generate attendance sessions for selected academic periods"""
        if request.POST.get('post'):
            periods = queryset.filter(is_active=True)
            sessions_created = 0
            
            for period in periods:
                # Generate sessions for the entire period
                sessions_created += generate_sessions_from_timetable(
                    period, period.period_start, period.period_end
                )
            
            self.message_user(
                request,
                f"Generated {sessions_created} attendance sessions for {periods.count()} academic periods.",
                level=messages.SUCCESS
            )
            return HttpResponseRedirect(request.get_full_path())
        
        # Show confirmation page
        context = {
            'title': 'Generate Attendance Sessions',
            'queryset': queryset,
            'action_name': 'generate_attendance_sessions',
        }
        return render(request, 'admin/attendance/academicperiod/generate_sessions.html', context)
    generate_attendance_sessions.short_description = "Generate attendance sessions"


# =============================================================================
# TIMETABLE SLOT ADMIN
# =============================================================================

class TimetableSlotForm(forms.ModelForm):
    """Custom form for Timetable Slot with smart defaults"""
    
    class Meta:
        model = TimetableSlot
        fields = '__all__'
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default academic period to current if not set
        if not self.instance.pk and not self.initial.get('academic_period'):
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                self.initial['academic_period'] = current_period.id
        
        # Filter course sections based on selected academic period
        if 'academic_period' in self.data:
            try:
                academic_period_id = self.data.get('academic_period')
                if academic_period_id:
                    academic_period = AcademicPeriod.objects.get(id=academic_period_id)
                    # Filter course sections for this academic period
                    self.fields['course_section'].queryset = CourseSection.objects.filter(
                        student_batch__academic_year=academic_period.academic_year
                    )
            except (ValueError, AcademicPeriod.DoesNotExist):
                pass
        elif self.instance.pk:
            # For existing instances, filter based on current academic period
            self.fields['course_section'].queryset = CourseSection.objects.filter(
                student_batch__academic_year=self.instance.academic_period.academic_year
            )


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    form = TimetableSlotForm
    list_display = [
        'course_section', 'faculty', 'academic_period', 'day_of_week', 
        'start_time', 'end_time', 'room', 'slot_type', 'is_active', 'enrolled_count'
    ]
    list_filter = [
        'academic_period', 'slot_type', 'day_of_week', 'is_active',
        'faculty', 'course_section__course__department'
    ]
    search_fields = [
        'course_section__course__code', 'faculty__first_name', 
        'faculty__last_name', 'room'
    ]
    ordering = ['academic_period', 'day_of_week', 'start_time']
    readonly_fields = ['created_at', 'updated_at', 'duration_minutes', 'enrolled_count']
    
    fieldsets = (
        ('Academic Period & Course', {
            'fields': ('academic_period', 'course_section', 'faculty')
        }),
        ('Schedule Details', {
            'fields': (
                'day_of_week', 'start_time', 'end_time', 'room', 'slot_type'
            )
        }),
        ('Configuration', {
            'fields': ('max_students', 'is_active', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'duration_minutes', 'enrolled_count'),
            'classes': ('collapse',)
        }),
    )
    
    def enrolled_count(self, obj):
        """Display enrolled students count"""
        if obj.pk:
            count = obj.get_enrolled_students_count()
            return format_html(
                '<a href="{}?course_section__id__exact={}">{} students</a>',
                reverse('admin:students_student_changelist'),
                obj.course_section.id,
                count
            )
        return '0 students'
    enrolled_count.short_description = 'Enrolled Students'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['activate_slots', 'deactivate_slots', 'generate_attendance_sessions']
    
    def activate_slots(self, request, queryset):
        """Activate selected timetable slots"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f"{updated} timetable slots have been activated.",
            level=messages.SUCCESS
        )
    activate_slots.short_description = "Activate selected slots"
    
    def deactivate_slots(self, request, queryset):
        """Deactivate selected timetable slots"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f"{updated} timetable slots have been deactivated.",
            level=messages.SUCCESS
        )
    deactivate_slots.short_description = "Deactivate selected slots"
    
    def generate_attendance_sessions(self, request, queryset):
        """Generate attendance sessions for selected timetable slots"""
        if request.POST.get('post'):
            slots = queryset.filter(is_active=True)
            sessions_created = 0
            
            for slot in slots:
                # Generate sessions for the academic period
                sessions_created += generate_sessions_from_timetable(
                    slot.academic_period,
                    slot.academic_period.period_start,
                    slot.academic_period.period_end
                )
            
            self.message_user(
                request,
                f"Generated {sessions_created} attendance sessions for {slots.count()} timetable slots.",
                level=messages.SUCCESS
            )
            return HttpResponseRedirect(request.get_full_path())
        
        # Show confirmation page
        context = {
            'title': 'Generate Attendance Sessions',
            'queryset': queryset,
            'action_name': 'generate_attendance_sessions',
        }
        return render(request, 'admin/attendance/timetableslot/generate_sessions.html', context)
    generate_attendance_sessions.short_description = "Generate attendance sessions"


# =============================================================================
# ATTENDANCE SESSION ADMIN
# =============================================================================

class AttendanceSessionForm(forms.ModelForm):
    """Custom form for Attendance Session with smart defaults"""
    
    class Meta:
        model = AttendanceSession
        fields = '__all__'
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'qr_expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default academic period to current if not set
        if not self.instance.pk and not self.initial.get('academic_period'):
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                self.initial['academic_period'] = current_period.id


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    form = AttendanceSessionForm
    list_display = [
        'course_section', 'academic_period', 'scheduled_date', 'start_datetime', 
        'end_datetime', 'room', 'status', 'faculty', 'attendance_count', 'attendance_percentage'
    ]
    list_filter = [
        'academic_period', 'status', 'scheduled_date', 'faculty',
        'course_section__course__department', 'auto_opened', 'auto_closed', 'makeup'
    ]
    search_fields = [
        'course_section__course__code', 'room', 'notes', 
        'faculty__first_name', 'faculty__last_name'
    ]
    ordering = ['-scheduled_date', 'start_datetime']
    readonly_fields = [
        'auto_opened', 'auto_closed', 'qr_token', 'qr_expires_at',
        'qr_generated_at', 'offline_sync_token', 'last_sync_at',
        'attendance_count', 'attendance_percentage', 'duration_minutes'
    ]
    
    fieldsets = (
        ('Academic Period & Course', {
            'fields': ('academic_period', 'timetable_slot', 'course_section', 'faculty')
        }),
        ('Session Information', {
            'fields': (
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
        ('Statistics', {
            'fields': ('attendance_count', 'attendance_percentage', 'duration_minutes'),
            'classes': ('collapse',)
        }),
    )
    
    def attendance_count(self, obj):
        """Display attendance records count with link"""
        if obj.pk:
            count = obj.get_attendance_count()
            return format_html(
                '<a href="{}?session__id__exact={}">{} records</a>',
                reverse('admin:attendance_attendancerecord_changelist'),
                obj.pk,
                count
            )
        return '0 records'
    attendance_count.short_description = 'Attendance Records'
    
    def attendance_percentage(self, obj):
        """Display attendance percentage"""
        if obj.pk:
            percentage = obj.get_attendance_percentage()
            color = 'green' if percentage >= 75 else 'orange' if percentage >= 50 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, percentage
            )
        return '0.0%'
    attendance_percentage.short_description = 'Attendance %'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['open_sessions', 'close_sessions', 'generate_qr_codes', 'lock_sessions']
    
    def open_sessions(self, request, queryset):
        """Open selected sessions for attendance"""
        updated = queryset.filter(status='SCHEDULED').update(status='OPEN')
        self.message_user(
            request,
            f"{updated} sessions have been opened for attendance.",
            level=messages.SUCCESS
        )
    open_sessions.short_description = "Open sessions for attendance"
    
    def close_sessions(self, request, queryset):
        """Close selected sessions"""
        updated = queryset.filter(status='OPEN').update(status='CLOSED')
        self.message_user(
            request,
            f"{updated} sessions have been closed.",
            level=messages.SUCCESS
        )
    close_sessions.short_description = "Close sessions"
    
    def generate_qr_codes(self, request, queryset):
        """Generate QR codes for selected sessions"""
        sessions = queryset.filter(status__in=['SCHEDULED', 'OPEN'])
        qr_generated = 0
        
        for session in sessions:
            if not session.qr_token or session.qr_expires_at < timezone.now():
                session.generate_qr_token()
                qr_generated += 1
        
        self.message_user(
            request,
            f"Generated QR codes for {qr_generated} sessions.",
            level=messages.SUCCESS
        )
    generate_qr_codes.short_description = "Generate QR codes"
    
    def lock_sessions(self, request, queryset):
        """Lock selected sessions"""
        updated = queryset.filter(status='CLOSED').update(status='LOCKED')
        self.message_user(
            request,
            f"{updated} sessions have been locked.",
            level=messages.SUCCESS
        )
    lock_sessions.short_description = "Lock sessions"


# =============================================================================
# ATTENDANCE RECORD ADMIN
# =============================================================================

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = [
        'session', 'student', 'mark', 'marked_at', 'source', 
        'device_type', 'sync_status', 'academic_period'
    ]
    list_filter = [
        'academic_period', 'mark', 'source', 'device_type', 'sync_status',
        'session__scheduled_date', 'marked_at'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'session__course_section__course__code', 'client_uuid'
    ]
    ordering = ['session__scheduled_date', 'student__roll_number']
    readonly_fields = [
        'marked_at', 'marked_by', 'last_modified_by', 'ip_address', 
        'user_agent', 'client_uuid', 'vendor_event_id', 'academic_period'
    ]
    
    fieldsets = (
        ('Academic Period & Session', {
            'fields': ('academic_period', 'session', 'student', 'mark', 'marked_at', 'notes')
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
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set marked_by on creation
            obj.marked_by = request.user
        else:  # Set last_modified_by on update
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# CUSTOM ADMIN SITE
# =============================================================================

class IntegratedAttendanceAdminSite(admin.AdminSite):
    """Custom admin site for integrated attendance management"""
    site_header = "CampsHub360 Integrated Academic System"
    site_title = "Academic Admin"
    index_title = "Integrated Academic & Attendance Management"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('academic-dashboard/', self.admin_view(self.academic_dashboard), name='academic_dashboard'),
            path('bulk-timetable-creation/', self.admin_view(self.bulk_timetable_creation), name='bulk_timetable_creation'),
        ]
        return custom_urls + urls

    def academic_dashboard(self, request):
        """Custom academic dashboard view"""
        from django.shortcuts import render
        
        # Get current academic period
        current_period = AcademicPeriod.get_current_period()
        
        # Get statistics
        stats = {
            'current_period': current_period,
            'total_periods': AcademicPeriod.objects.count(),
            'active_periods': AcademicPeriod.objects.filter(is_active=True).count(),
            'total_slots': TimetableSlot.objects.count(),
            'active_slots': TimetableSlot.objects.filter(is_active=True).count(),
            'total_sessions': AttendanceSession.objects.count(),
            'open_sessions': AttendanceSession.objects.filter(status='OPEN').count(),
            'today_sessions': AttendanceSession.objects.filter(scheduled_date=date.today()).count(),
        }
        
        context = {
            'title': 'Academic Dashboard',
            'stats': stats,
        }
        return render(request, 'admin/attendance/dashboard.html', context)

    def bulk_timetable_creation(self, request):
        """Bulk timetable creation interface"""
        from django.shortcuts import render
        
        if request.method == 'POST':
            # Process bulk creation
            academic_period_id = request.POST.get('academic_period')
            course_section_ids = request.POST.getlist('course_sections')
            
            if academic_period_id and course_section_ids:
                academic_period = AcademicPeriod.objects.get(id=academic_period_id)
                course_sections = CourseSection.objects.filter(id__in=course_section_ids)
                
                slots_created = 0
                for section in course_sections:
                    # Create basic timetable slots
                    for day in range(5):  # Monday to Friday
                        TimetableSlot.objects.get_or_create(
                            academic_period=academic_period,
                            course_section=section,
                            faculty=section.faculty,
                            day_of_week=day,
                            start_time='09:00:00',
                            end_time='10:00:00',
                            defaults={
                                'slot_type': 'LECTURE',
                                'room': 'A101',
                                'is_active': True,
                                'created_by': request.user
                            }
                        )
                        slots_created += 1
                
                messages.success(request, f"Created {slots_created} timetable slots.")
                return redirect('admin:bulk_timetable_creation')
        
        # Get available academic periods and course sections
        academic_periods = AcademicPeriod.objects.filter(is_active=True)
        course_sections = CourseSection.objects.filter(is_active=True)
        
        context = {
            'title': 'Bulk Timetable Creation',
            'academic_periods': academic_periods,
            'course_sections': course_sections,
        }
        return render(request, 'admin/attendance/bulk_timetable_creation.html', context)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_sessions_from_timetable(academic_period, start_date, end_date):
    """Generate attendance sessions from timetable slots for a given period"""
    from .models_integrated import generate_sessions_from_timetable
    return generate_sessions_from_timetable(academic_period, start_date, end_date)
