from django.contrib import admin
from django import forms
from django.db.models import Q
from .models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest,
    LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
    AttendanceConfiguration, StudentSnapshot
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


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['course_section', 'scheduled_date', 'start_datetime', 'end_datetime', 'room', 'status', 'faculty']
    list_filter = ['scheduled_date', 'status', 'course_section__course__department', 'faculty']
    search_fields = ['course_section__course__code', 'room', 'notes']
    ordering = ['-scheduled_date', 'start_datetime']
    readonly_fields = ['auto_opened', 'auto_closed', 'qr_token', 'qr_expires_at']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    form = AttendanceRecordForm
    list_display = ['session', 'student', 'mark', 'marked_at', 'source']
    list_filter = ['mark', 'source', 'session__scheduled_date']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name']
    ordering = ['session__scheduled_date', 'student__roll_number']
    readonly_fields = ['marked_at', 'marked_by', 'ip_address', 'user_agent']
    
    class Media:
        js = ('admin/js/attendance_record_filter.js',)


@admin.register(AttendanceCorrectionRequest)
class AttendanceCorrectionRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'from_mark', 'to_mark', 'status', 'requested_by', 'created_at']
    list_filter = ['status', 'from_mark', 'to_mark', 'created_at']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['requested_by', 'decided_by', 'decided_at', 'created_at', 'updated_at']


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'leave_type', 'start_date', 'end_date', 'status', 'affects_attendance']
    list_filter = ['leave_type', 'status', 'affects_attendance', 'start_date']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['decided_by', 'decided_at', 'created_at', 'updated_at']


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    list_display = ['course_section', 'faculty', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'academic_year', 'semester']
    search_fields = ['course_section__course__code', 'faculty__first_name', 'faculty__last_name', 'room']
    ordering = ['day_of_week', 'start_time']


@admin.register(AcademicCalendarHoliday)
class AcademicCalendarHolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'is_full_day', 'academic_year']
    list_filter = ['is_full_day', 'academic_year', 'date']
    search_fields = ['name', 'description']
    ordering = ['-date']


@admin.register(AttendanceConfiguration)
class AttendanceConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'data_type', 'is_active', 'updated_by', 'updated_at']
    list_filter = ['data_type', 'is_active']
    search_fields = ['key', 'description']
    ordering = ['key']
    readonly_fields = ['updated_by', 'updated_at']


@admin.register(StudentSnapshot)
class StudentSnapshotAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'roll_number', 'full_name', 'course_section']
    list_filter = ['session__scheduled_date', 'course_section__course__department']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'roll_number', 'full_name']
    ordering = ['session__scheduled_date', 'roll_number']

