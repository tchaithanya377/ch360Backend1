"""
Enhanced Forms for CampsHub360 Attendance System
Custom forms with improved dropdowns and user experience
"""

from django import forms
from django.db.models import Q
from django.utils import timezone
from datetime import date

from .models import (
    AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord,
    LeaveApplication, AttendanceCorrectionRequest
)
from students.models import AcademicYear, Semester, Student
from academics.models import CourseSection
from faculty.models import Faculty


class AcademicPeriodForm(forms.ModelForm):
    """Enhanced form for AcademicPeriod with smart dropdowns and validation"""
    
    class Meta:
        model = AcademicPeriod
        fields = '__all__'
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Academic Year',
                'onchange': 'filterSemesters()'
            }),
            'semester': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Semester',
                'id': 'id_semester'
            }),
            'period_start': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'onchange': 'validateDateRange()'
            }),
            'period_end': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'onchange': 'validateDateRange()'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Optional description for this academic period'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate academic year dropdown with active years, ordered by year
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(
            is_active=True
        ).order_by('-year')
        
        # Set up semester dropdown - will be filtered by JavaScript
        self.fields['semester'].queryset = Semester.objects.none()
        
        # If editing existing period, populate semester dropdown
        if self.instance and self.instance.pk and hasattr(self.instance, 'academic_year_id') and self.instance.academic_year_id:
            try:
                if self.instance.academic_year:
                    self.fields['semester'].queryset = Semester.objects.filter(
                        academic_year=self.instance.academic_year,
                        is_active=True
                    ).order_by('-semester_type', 'name')
            except:
                # If academic_year is not set, keep empty queryset
                pass
        
        # Add empty choice for dropdowns
        self.fields['academic_year'].empty_label = "Select Academic Year"
        self.fields['semester'].empty_label = "Select Semester"
        
        # Make fields required
        self.fields['academic_year'].required = True
        self.fields['semester'].required = True
        self.fields['period_start'].required = True
        self.fields['period_end'].required = True
        
        # Add help text
        self.fields['academic_year'].help_text = "Select the academic year for this period"
        self.fields['semester'].help_text = "Select the semester (will be filtered based on academic year)"
        self.fields['period_start'].help_text = "Start date of the academic period"
        self.fields['period_end'].help_text = "End date of the academic period"
        self.fields['is_current'].help_text = "Mark this as the current active academic period"
        self.fields['is_active'].help_text = "Whether this academic period is active"
    
    def clean(self):
        cleaned_data = super().clean()
        academic_year = cleaned_data.get('academic_year')
        semester = cleaned_data.get('semester')
        period_start = cleaned_data.get('period_start')
        period_end = cleaned_data.get('period_end')
        is_current = cleaned_data.get('is_current')
        
        # Validate date range
        if period_start and period_end:
            if period_start >= period_end:
                raise forms.ValidationError("Period start date must be before end date")
            
            # Check if period dates are within academic year range
            if academic_year:
                if period_start < academic_year.start_date or period_end > academic_year.end_date:
                    raise forms.ValidationError(
                        f"Period dates must be within academic year range "
                        f"({academic_year.start_date} to {academic_year.end_date})"
                    )
        
        # Validate semester belongs to selected academic year
        if academic_year and semester:
            if semester.academic_year != academic_year:
                raise forms.ValidationError(
                    f"Selected semester '{semester.name}' does not belong to "
                    f"academic year '{academic_year.year}'"
                )
        
        # Ensure only one current period exists
        if is_current:
            existing_current = AcademicPeriod.objects.filter(
                is_current=True
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_current.exists():
                raise forms.ValidationError(
                    "Only one academic period can be marked as current. "
                    f"Please uncheck the current period: {existing_current.first().display_name}"
                )
        
        # Check for duplicate academic period
        if academic_year and semester:
            existing_period = AcademicPeriod.objects.filter(
                academic_year=academic_year,
                semester=semester
            ).exclude(id=self.instance.id if self.instance else None)
            if existing_period.exists():
                raise forms.ValidationError(
                    f"An academic period already exists for {semester.name} {academic_year.year}"
                )
        
        return cleaned_data


class TimetableSlotForm(forms.ModelForm):
    """Enhanced form for TimetableSlot with smart dropdowns"""
    
    # Add dropdown fields for academic year and semester from students table
    academic_year = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Academic Year",
        required=True,
        help_text="Select the academic year from students table"
    )
    semester = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select Semester", 
        required=True,
        help_text="Select the semester from students table"
    )
    
    class Meta:
        model = TimetableSlot
        fields = '__all__'
        widgets = {
            'academic_year': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select Academic Year',
                'onchange': 'filterSemesters()'
            }),
            'semester': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select Semester',
                'onchange': 'filterCourseSections()'
            }),
            'academic_period': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select Academic Period',
                'onchange': 'filterCourseSections()'
            }),
            'course_section': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select Course Section',
                'id': 'id_course_section'
            }),
            'faculty': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Select Faculty'
            }),
            'day_of_week': forms.Select(attrs={
                'class': 'form-control'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'onchange': 'validateTimeRange()'
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A101, Lab-1, Online'
            }),
            'slot_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_students': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '200',
                'placeholder': 'Max Students'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Import students models
        from students.models import AcademicYear as StudentAcademicYear, Semester as StudentSemester
        
        # Populate academic year dropdown from students table
        self.fields['academic_year'].queryset = StudentAcademicYear.objects.filter(
            is_active=True
        ).order_by('-is_current', '-year')
        
        # Populate semester dropdown from students table
        self.fields['semester'].queryset = StudentSemester.objects.filter(
            is_active=True
        ).order_by('-is_current', 'semester_type')
        
        # Set initial values if editing existing slot
        if self.instance and self.instance.pk:
            if self.instance.academic_year:
                self.fields['academic_year'].initial = self.instance.academic_year
            if self.instance.semester:
                self.fields['semester'].initial = self.instance.semester
        
        # Populate academic period dropdown with active periods
        if 'academic_period' in self.fields:
            self.fields['academic_period'].queryset = AcademicPeriod.objects.filter(
                is_active=True
            ).select_related('academic_year', 'semester').order_by(
                '-academic_year__year', '-semester__semester_type'
            )
            self.fields['academic_period'].empty_label = "Select Academic Period"
            self.fields['academic_period'].required = True
            self.fields['academic_period'].help_text = "Select the academic period for this timetable slot"
        
        # Set up course section dropdown - will be filtered by JavaScript
        if 'course_section' in self.fields:
            self.fields['course_section'].queryset = CourseSection.objects.none()
            self.fields['course_section'].empty_label = "Select Course Section"
            self.fields['course_section'].required = True
            self.fields['course_section'].help_text = "Select the course section"
            
            # If editing existing slot, populate course section dropdown
            if self.instance and self.instance.pk and hasattr(self.instance, 'academic_period_id') and self.instance.academic_period_id:
                try:
                    if self.instance.academic_period:
                        self.fields['course_section'].queryset = CourseSection.objects.filter(
                            is_active=True
                        ).order_by('course__code', 'section_type')
                except:
                    # If academic_period is not set, keep empty queryset
                    pass
        
        # Populate faculty dropdown with active faculty
        if 'faculty' in self.fields:
            self.fields['faculty'].queryset = Faculty.objects.filter(
                status='ACTIVE'
            ).order_by('first_name', 'last_name')
            self.fields['faculty'].empty_label = "Select Faculty"
            self.fields['faculty'].required = True
            self.fields['faculty'].help_text = "Select the faculty member teaching this slot"
        
        # Set up other required fields
        if 'day_of_week' in self.fields:
            self.fields['day_of_week'].required = True
            self.fields['day_of_week'].help_text = "Select the day of the week"
        
        if 'start_time' in self.fields:
            self.fields['start_time'].required = True
            self.fields['start_time'].help_text = "Start time of the class"
        
        if 'end_time' in self.fields:
            self.fields['end_time'].required = True
            self.fields['end_time'].help_text = "End time of the class"
        
        if 'room' in self.fields:
            self.fields['room'].help_text = "Room or location for the class"
        
        if 'slot_type' in self.fields:
            self.fields['slot_type'].help_text = "Type of class (Lecture, Lab, Tutorial, etc.)"
        
        if 'max_students' in self.fields:
            self.fields['max_students'].help_text = "Maximum number of students allowed"
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        day_of_week = cleaned_data.get('day_of_week')
        academic_period = cleaned_data.get('academic_period')
        faculty = cleaned_data.get('faculty')
        academic_year = cleaned_data.get('academic_year')
        semester = cleaned_data.get('semester')
        
        # Validate that semester belongs to the selected academic year
        if academic_year and semester:
            if semester.academic_year != academic_year:
                raise forms.ValidationError(
                    "The selected semester does not belong to the selected academic year."
                )
        
        # Validate time range
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time")
            
            # Check for minimum duration (10 minutes)
            duration = end_time.hour * 60 + end_time.minute - (start_time.hour * 60 + start_time.minute)
            if duration < 10:
                raise forms.ValidationError("Class duration must be at least 10 minutes")
        
        # Check for faculty conflicts
        if academic_period and faculty and day_of_week and start_time and end_time:
            conflicting_slots = TimetableSlot.objects.filter(
                academic_period=academic_period,
                faculty=faculty,
                day_of_week=day_of_week,
                is_active=True
            ).exclude(id=self.instance.id if self.instance else None)
            
            for slot in conflicting_slots:
                if (start_time < slot.end_time and end_time > slot.start_time):
                    raise forms.ValidationError(
                        f"Faculty {faculty.name} has a conflicting class at the same time: "
                        f"{slot.get_day_of_week_display()} {slot.start_time}-{slot.end_time}"
                    )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save the form data"""
        instance = super().save(commit=False)
        
        # Set the academic year and semester from the dropdown selections
        if self.cleaned_data.get('academic_year'):
            instance.academic_year = self.cleaned_data['academic_year'].year
        if self.cleaned_data.get('semester'):
            instance.semester = self.cleaned_data['semester'].name
            
        if commit:
            instance.save()
            
        return instance


class AttendanceSessionForm(forms.ModelForm):
    """Enhanced form for AttendanceSession with smart dropdowns"""
    
    class Meta:
        model = AttendanceSession
        fields = '__all__'
        widgets = {
            'academic_period': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Academic Period',
                'onchange': 'filterTimetableSlots()'
            }),
            'course_section': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Course Section'
            }),
            'faculty': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Faculty'
            }),
            'timetable_slot': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Timetable Slot',
                'id': 'id_timetable_slot'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., A101, Lab-1, Online'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Optional notes for this session'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate academic period dropdown with active periods
        if 'academic_period' in self.fields:
            self.fields['academic_period'].queryset = AcademicPeriod.objects.filter(
                is_active=True
            ).select_related('academic_year', 'semester').order_by(
                '-academic_year__year', '-semester__semester_type'
            )
            self.fields['academic_period'].empty_label = "Select Academic Period"
            self.fields['academic_period'].required = True
            self.fields['academic_period'].help_text = "Select the academic period for this session"
        
        # Set up timetable slot dropdown - will be filtered by JavaScript
        if 'timetable_slot' in self.fields:
            self.fields['timetable_slot'].queryset = TimetableSlot.objects.none()
            self.fields['timetable_slot'].empty_label = "Select Timetable Slot"
            self.fields['timetable_slot'].help_text = "Select the corresponding timetable slot"
            
            # If editing existing session, populate timetable slot dropdown
            if self.instance and self.instance.pk and hasattr(self.instance, 'academic_period_id') and self.instance.academic_period_id:
                try:
                    if self.instance.academic_period:
                        self.fields['timetable_slot'].queryset = TimetableSlot.objects.filter(
                            academic_period=self.instance.academic_period,
                            is_active=True
                        ).order_by('day_of_week', 'start_time')
                except:
                    # If academic_period is not set, keep empty queryset
                    pass
        
        # Populate course section dropdown
        if 'course_section' in self.fields:
            self.fields['course_section'].queryset = CourseSection.objects.filter(
                is_active=True
            ).order_by('course__code', 'section_type')
            self.fields['course_section'].empty_label = "Select Course Section"
            self.fields['course_section'].required = True
            self.fields['course_section'].help_text = "Select the course section"
        
        # Populate faculty dropdown
        if 'faculty' in self.fields:
            self.fields['faculty'].queryset = Faculty.objects.filter(
                status='ACTIVE'
            ).order_by('first_name', 'last_name')
            self.fields['faculty'].empty_label = "Select Faculty"
            self.fields['faculty'].required = True
            self.fields['faculty'].help_text = "Select the faculty member conducting the session"
        
        # Set up other required fields
        if 'scheduled_date' in self.fields:
            self.fields['scheduled_date'].required = True
            self.fields['scheduled_date'].help_text = "Date when the session is scheduled"
        
        if 'start_datetime' in self.fields:
            self.fields['start_datetime'].required = True
            self.fields['start_datetime'].help_text = "Start date and time of the session"
        
        if 'end_datetime' in self.fields:
            self.fields['end_datetime'].required = True
            self.fields['end_datetime'].help_text = "End date and time of the session"
        
        if 'room' in self.fields:
            self.fields['room'].help_text = "Room or location for the session"
        
        if 'status' in self.fields:
            self.fields['status'].help_text = "Current status of the session"
        
        if 'notes' in self.fields:
            self.fields['notes'].help_text = "Optional notes for this session"
    
    def clean(self):
        cleaned_data = super().clean()
        start_datetime = cleaned_data.get('start_datetime')
        end_datetime = cleaned_data.get('end_datetime')
        scheduled_date = cleaned_data.get('scheduled_date')
        
        # Validate datetime range
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise forms.ValidationError("Start datetime must be before end datetime")
        
        # Validate scheduled date matches start datetime date
        if scheduled_date and start_datetime:
            if scheduled_date != start_datetime.date():
                raise forms.ValidationError(
                    "Scheduled date must match the date in start datetime"
                )
        
        return cleaned_data


class AttendanceRecordForm(forms.ModelForm):
    """Enhanced form for AttendanceRecord with smart student filtering"""
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        widgets = {
            'session': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Session',
                'onchange': 'filterStudents()'
            }),
            'student': forms.Select(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%;',
                'data-placeholder': 'Select Student',
                'id': 'id_student'
            }),
            'mark': forms.Select(attrs={
                'class': 'form-control',
                'style': 'width: 100%;'
            }),
            'marked_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Reason for absence or late arrival'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Additional notes'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate session dropdown with active sessions
        if 'session' in self.fields:
            self.fields['session'].queryset = AttendanceSession.objects.filter(
                status__in=['scheduled', 'open']
            ).select_related('course_section', 'academic_period').order_by(
                '-scheduled_date', 'start_datetime'
            )
            self.fields['session'].empty_label = "Select Session"
            self.fields['session'].required = True
            self.fields['session'].help_text = "Select the attendance session"
        
        # Set up student dropdown - will be filtered by JavaScript
        if 'student' in self.fields:
            self.fields['student'].queryset = Student.objects.none()
            self.fields['student'].empty_label = "Select Student"
            self.fields['student'].required = True
            self.fields['student'].help_text = "Select the student (filtered based on session)"
            
            # If editing existing record, populate student dropdown
            if self.instance and self.instance.pk and hasattr(self.instance, 'session_id') and self.instance.session_id:
                try:
                    if self.instance.session and self.instance.session.course_section:
                        if self.instance.session.course_section.student_batch:
                            self.fields['student'].queryset = Student.objects.filter(
                                student_batch=self.instance.session.course_section.student_batch
                            ).order_by('roll_number')
                        else:
                            self.fields['student'].queryset = Student.objects.all().order_by('roll_number')
                except:
                    # If session is not set, keep empty queryset
                    pass
        
        # Set up other fields
        if 'mark' in self.fields:
            self.fields['mark'].required = True
            self.fields['mark'].help_text = "Attendance mark (Present, Absent, Late, etc.)"
        
        if 'marked_at' in self.fields:
            self.fields['marked_at'].help_text = "When the attendance was marked"
        
        if 'reason' in self.fields:
            self.fields['reason'].help_text = "Reason for absence or late arrival"
        
        if 'notes' in self.fields:
            self.fields['notes'].help_text = "Additional notes"
    
    def clean(self):
        cleaned_data = super().clean()
        session = cleaned_data.get('session')
        student = cleaned_data.get('student')
        mark = cleaned_data.get('mark')
        
        # Check for duplicate attendance records
        if session and student:
            existing_record = AttendanceRecord.objects.filter(
                session=session,
                student=student
            ).exclude(id=self.instance.id if self.instance else None)
            
            if existing_record.exists():
                raise forms.ValidationError(
                    f"Attendance record already exists for {student.roll_number} "
                    f"in session {session.id}"
                )
        
        # Validate student belongs to session's course section
        if session and student:
            if (session.course_section and 
                session.course_section.student_batch and 
                student.student_batch != session.course_section.student_batch):
                raise forms.ValidationError(
                    f"Student {student.roll_number} does not belong to the course section "
                    f"for this session"
                )
        
        return cleaned_data
