from django.contrib import admin
from django import forms
from django.db.models import Q
from .models import AttendanceSession, AttendanceRecord
from students.models import Student


class AttendanceRecordForm(forms.ModelForm):
    """Custom form for AttendanceRecord that filters students based on selected session"""
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        widgets = {
            'session': forms.Select(attrs={'onchange': 'filterStudents()'}),
            'student': forms.Select(),
            'status': forms.Select(),
            'check_in_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
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
    list_display = ['course_section', 'date', 'start_time', 'end_time', 'room', 'is_cancelled']
    list_filter = ['date', 'is_cancelled', 'course_section__course__department']
    search_fields = ['course_section__course__code', 'course_section__section_number', 'room', 'notes']
    ordering = ['-date', 'start_time']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    form = AttendanceRecordForm
    list_display = ['session', 'student', 'status', 'check_in_time']
    list_filter = ['status', 'session__date']
    search_fields = ['student__roll_number', 'student__user__first_name', 'student__user__last_name']
    ordering = ['session__date', 'student__roll_number']
    
    class Media:
        js = ('admin/js/attendance_record_filter.js',)

