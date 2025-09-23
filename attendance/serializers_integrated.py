"""
Enhanced Serializers for Integrated Academic System
Provides comprehensive API serialization for Academic Periods, Timetable, and Attendance
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import date, timedelta

from .models_integrated import (
    AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord
)
from students.models import AcademicYear, Semester
from academics.models import CourseSection
from faculty.models import Faculty
from students.models import Student


# =============================================================================
# ACADEMIC PERIOD SERIALIZERS
# =============================================================================

class AcademicYearSerializer(serializers.ModelSerializer):
    """Serializer for Academic Year"""
    
    class Meta:
        model = AcademicYear
        fields = ['id', 'year', 'start_date', 'end_date', 'is_current', 'is_active']


class SemesterSerializer(serializers.ModelSerializer):
    """Serializer for Semester"""
    
    class Meta:
        model = Semester
        fields = ['id', 'name', 'semester_type', 'start_date', 'end_date', 'is_current', 'is_active']


class AcademicPeriodListSerializer(serializers.ModelSerializer):
    """List serializer for Academic Period"""
    academic_year = AcademicYearSerializer(read_only=True)
    semester = SemesterSerializer(read_only=True)
    duration_days = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    
    class Meta:
        model = AcademicPeriod
        fields = [
            'id', 'academic_year', 'semester', 'display_name',
            'period_start', 'period_end', 'duration_days',
            'is_current', 'is_active', 'is_ongoing', 'description'
        ]


class AcademicPeriodDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for Academic Period"""
    academic_year = AcademicYearSerializer(read_only=True)
    semester = SemesterSerializer(read_only=True)
    duration_days = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    
    # Statistics
    timetable_slots_count = serializers.SerializerMethodField()
    attendance_sessions_count = serializers.SerializerMethodField()
    attendance_records_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AcademicPeriod
        fields = [
            'id', 'academic_year', 'semester', 'display_name',
            'period_start', 'period_end', 'duration_days',
            'is_current', 'is_active', 'is_ongoing', 'description',
            'timetable_slots_count', 'attendance_sessions_count', 'attendance_records_count',
            'created_at', 'updated_at'
        ]
    
    def get_timetable_slots_count(self, obj):
        return obj.timetable_slots.count()
    
    def get_attendance_sessions_count(self, obj):
        return obj.attendance_sessions.count()
    
    def get_attendance_records_count(self, obj):
        return obj.attendance_records.count()


class AcademicPeriodCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Academic Period"""
    academic_year_id = serializers.IntegerField(write_only=True)
    semester_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AcademicPeriod
        fields = [
            'academic_year_id', 'semester_id', 'period_start', 'period_end',
            'is_current', 'is_active', 'description'
        ]
    
    def validate(self, data):
        """Validate academic period data"""
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        is_current = data.get('is_current', False)
        
        if period_start and period_end:
            if period_start >= period_end:
                raise serializers.ValidationError("Period start date must be before end date")
        
        if is_current:
            # Check if another period is already current
            existing_current = AcademicPeriod.objects.filter(is_current=True)
            if self.instance:
                existing_current = existing_current.exclude(id=self.instance.id)
            if existing_current.exists():
                raise serializers.ValidationError("Only one academic period can be current")
        
        return data
    
    def create(self, validated_data):
        """Create academic period with proper relationships"""
        academic_year_id = validated_data.pop('academic_year_id')
        semester_id = validated_data.pop('semester_id')
        
        academic_year = AcademicYear.objects.get(id=academic_year_id)
        semester = Semester.objects.get(id=semester_id)
        
        return AcademicPeriod.objects.create(
            academic_year=academic_year,
            semester=semester,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        """Update academic period with proper relationships"""
        if 'academic_year_id' in validated_data:
            academic_year_id = validated_data.pop('academic_year_id')
            instance.academic_year = AcademicYear.objects.get(id=academic_year_id)
        
        if 'semester_id' in validated_data:
            semester_id = validated_data.pop('semester_id')
            instance.semester = Semester.objects.get(id=semester_id)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# =============================================================================
# TIMETABLE SLOT SERIALIZERS
# =============================================================================

class CourseSectionSerializer(serializers.ModelSerializer):
    """Serializer for Course Section"""
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    department_name = serializers.CharField(source='course.department.name', read_only=True)
    faculty_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseSection
        fields = [
            'id', 'course_code', 'course_name', 'department_name',
            'section_type', 'faculty_name', 'max_students', 'current_enrollment'
        ]
    
    def get_faculty_name(self, obj):
        return f"{obj.faculty.first_name} {obj.faculty.last_name}"


class FacultySerializer(serializers.ModelSerializer):
    """Serializer for Faculty"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Faculty
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email', 'phone']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class TimetableSlotListSerializer(serializers.ModelSerializer):
    """List serializer for Timetable Slot"""
    academic_period = AcademicPeriodListSerializer(read_only=True)
    course_section = CourseSectionSerializer(read_only=True)
    faculty = FacultySerializer(read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    enrolled_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TimetableSlot
        fields = [
            'id', 'academic_period', 'course_section', 'faculty',
            'day_of_week', 'day_name', 'start_time', 'end_time',
            'room', 'slot_type', 'max_students', 'is_active',
            'duration_minutes', 'enrolled_count'
        ]
    
    def get_enrolled_count(self, obj):
        return obj.get_enrolled_students_count()


class TimetableSlotDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for Timetable Slot"""
    academic_period = AcademicPeriodDetailSerializer(read_only=True)
    course_section = CourseSectionSerializer(read_only=True)
    faculty = FacultySerializer(read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    enrolled_count = serializers.SerializerMethodField()
    can_generate_sessions = serializers.ReadOnlyField()
    
    # Related sessions
    attendance_sessions = serializers.SerializerMethodField()
    
    class Meta:
        model = TimetableSlot
        fields = [
            'id', 'academic_period', 'course_section', 'faculty',
            'day_of_week', 'day_name', 'start_time', 'end_time',
            'room', 'slot_type', 'max_students', 'is_active',
            'duration_minutes', 'enrolled_count', 'can_generate_sessions',
            'attendance_sessions', 'notes', 'created_at', 'updated_at'
        ]
    
    def get_enrolled_count(self, obj):
        return obj.get_enrolled_students_count()
    
    def get_attendance_sessions(self, obj):
        sessions = obj.attendance_sessions.all()[:10]  # Limit to recent sessions
        return AttendanceSessionListSerializer(sessions, many=True).data


class TimetableSlotCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Timetable Slot"""
    academic_period_id = serializers.IntegerField(write_only=True)
    course_section_id = serializers.IntegerField(write_only=True)
    faculty_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TimetableSlot
        fields = [
            'academic_period_id', 'course_section_id', 'faculty_id',
            'day_of_week', 'start_time', 'end_time', 'room',
            'slot_type', 'max_students', 'is_active', 'notes'
        ]
    
    def validate(self, data):
        """Validate timetable slot data"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        faculty_id = data.get('faculty_id')
        day_of_week = data.get('day_of_week')
        academic_period_id = data.get('academic_period_id')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError("Start time must be before end time")
        
        # Check for overlapping slots for the same faculty
        if faculty_id and day_of_week and academic_period_id:
            overlapping = TimetableSlot.objects.filter(
                academic_period_id=academic_period_id,
                faculty_id=faculty_id,
                day_of_week=day_of_week,
                is_active=True
            )
            if self.instance:
                overlapping = overlapping.exclude(id=self.instance.id)
            
            for slot in overlapping:
                if (start_time < slot.end_time and end_time > slot.start_time):
                    raise serializers.ValidationError(f"Faculty has overlapping slot: {slot}")
        
        return data
    
    def create(self, validated_data):
        """Create timetable slot with proper relationships"""
        academic_period_id = validated_data.pop('academic_period_id')
        course_section_id = validated_data.pop('course_section_id')
        faculty_id = validated_data.pop('faculty_id')
        
        academic_period = AcademicPeriod.objects.get(id=academic_period_id)
        course_section = CourseSection.objects.get(id=course_section_id)
        faculty = Faculty.objects.get(id=faculty_id)
        
        return TimetableSlot.objects.create(
            academic_period=academic_period,
            course_section=course_section,
            faculty=faculty,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        """Update timetable slot with proper relationships"""
        if 'academic_period_id' in validated_data:
            academic_period_id = validated_data.pop('academic_period_id')
            instance.academic_period = AcademicPeriod.objects.get(id=academic_period_id)
        
        if 'course_section_id' in validated_data:
            course_section_id = validated_data.pop('course_section_id')
            instance.course_section = CourseSection.objects.get(id=course_section_id)
        
        if 'faculty_id' in validated_data:
            faculty_id = validated_data.pop('faculty_id')
            instance.faculty = Faculty.objects.get(id=faculty_id)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# =============================================================================
# ATTENDANCE SESSION SERIALIZERS
# =============================================================================

class AttendanceSessionListSerializer(serializers.ModelSerializer):
    """List serializer for Attendance Session"""
    academic_period = AcademicPeriodListSerializer(read_only=True)
    course_section = CourseSectionSerializer(read_only=True)
    faculty = FacultySerializer(read_only=True)
    attendance_count = serializers.SerializerMethodField()
    attendance_percentage = serializers.SerializerMethodField()
    duration_minutes = serializers.ReadOnlyField()
    can_mark_attendance = serializers.ReadOnlyField()
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'academic_period', 'course_section', 'faculty',
            'scheduled_date', 'start_datetime', 'end_datetime',
            'room', 'status', 'attendance_count', 'attendance_percentage',
            'duration_minutes', 'can_mark_attendance', 'makeup'
        ]
    
    def get_attendance_count(self, obj):
        return obj.get_attendance_count()
    
    def get_attendance_percentage(self, obj):
        return obj.get_attendance_percentage()


class AttendanceSessionDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for Attendance Session"""
    academic_period = AcademicPeriodDetailSerializer(read_only=True)
    course_section = CourseSectionSerializer(read_only=True)
    faculty = FacultySerializer(read_only=True)
    attendance_count = serializers.SerializerMethodField()
    attendance_percentage = serializers.SerializerMethodField()
    duration_minutes = serializers.ReadOnlyField()
    can_mark_attendance = serializers.ReadOnlyField()
    
    # QR Code information
    qr_token = serializers.CharField(read_only=True)
    qr_expires_at = serializers.DateTimeField(read_only=True)
    qr_generated_at = serializers.DateTimeField(read_only=True)
    
    # Related records
    attendance_records = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'academic_period', 'timetable_slot', 'course_section', 'faculty',
            'scheduled_date', 'start_datetime', 'end_datetime', 'room', 'status',
            'attendance_count', 'attendance_percentage', 'duration_minutes',
            'can_mark_attendance', 'makeup', 'notes',
            'qr_token', 'qr_expires_at', 'qr_generated_at',
            'biometric_enabled', 'biometric_device_id',
            'attendance_records', 'created_at', 'updated_at'
        ]
    
    def get_attendance_count(self, obj):
        return obj.get_attendance_count()
    
    def get_attendance_percentage(self, obj):
        return obj.get_attendance_percentage()
    
    def get_attendance_records(self, obj):
        records = obj.attendance_records.all()
        return AttendanceRecordListSerializer(records, many=True).data


class AttendanceSessionCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Attendance Session"""
    academic_period_id = serializers.IntegerField(write_only=True, required=False)
    timetable_slot_id = serializers.IntegerField(write_only=True, required=False)
    course_section_id = serializers.IntegerField(write_only=True, required=False)
    faculty_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = AttendanceSession
        fields = [
            'academic_period_id', 'timetable_slot_id', 'course_section_id', 'faculty_id',
            'scheduled_date', 'start_datetime', 'end_datetime', 'room', 'status',
            'makeup', 'notes', 'biometric_enabled', 'biometric_device_id'
        ]
    
    def validate(self, data):
        """Validate attendance session data"""
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if start_datetime >= end_datetime:
                raise serializers.ValidationError("Start datetime must be before end datetime")
        
        return data
    
    def create(self, validated_data):
        """Create attendance session with proper relationships"""
        academic_period_id = validated_data.pop('academic_period_id', None)
        timetable_slot_id = validated_data.pop('timetable_slot_id', None)
        course_section_id = validated_data.pop('course_section_id', None)
        faculty_id = validated_data.pop('faculty_id', None)
        
        # Auto-populate from timetable slot if provided
        if timetable_slot_id:
            timetable_slot = TimetableSlot.objects.get(id=timetable_slot_id)
            validated_data['academic_period'] = timetable_slot.academic_period
            validated_data['course_section'] = timetable_slot.course_section
            validated_data['faculty'] = timetable_slot.faculty
            if not validated_data.get('room'):
                validated_data['room'] = timetable_slot.room
        else:
            # Manual assignment
            if academic_period_id:
                validated_data['academic_period'] = AcademicPeriod.objects.get(id=academic_period_id)
            if course_section_id:
                validated_data['course_section'] = CourseSection.objects.get(id=course_section_id)
            if faculty_id:
                validated_data['faculty'] = Faculty.objects.get(id=faculty_id)
        
        return AttendanceSession.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update attendance session with proper relationships"""
        # Handle relationship updates
        for field in ['academic_period_id', 'timetable_slot_id', 'course_section_id', 'faculty_id']:
            if field in validated_data:
                field_id = validated_data.pop(field)
                if field_id:
                    if field == 'academic_period_id':
                        instance.academic_period = AcademicPeriod.objects.get(id=field_id)
                    elif field == 'timetable_slot_id':
                        instance.timetable_slot = TimetableSlot.objects.get(id=field_id)
                    elif field == 'course_section_id':
                        instance.course_section = CourseSection.objects.get(id=field_id)
                    elif field == 'faculty_id':
                        instance.faculty = Faculty.objects.get(id=field_id)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# =============================================================================
# ATTENDANCE RECORD SERIALIZERS
# =============================================================================

class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = ['id', 'roll_number', 'first_name', 'last_name', 'full_name', 'email']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class AttendanceRecordListSerializer(serializers.ModelSerializer):
    """List serializer for Attendance Record"""
    academic_period = AcademicPeriodListSerializer(read_only=True)
    student = StudentSerializer(read_only=True)
    session_info = serializers.SerializerMethodField()
    is_present = serializers.ReadOnlyField()
    is_absent = serializers.ReadOnlyField()
    is_excused = serializers.ReadOnlyField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'academic_period', 'student', 'session_info',
            'mark', 'marked_at', 'source', 'device_type',
            'is_present', 'is_absent', 'is_excused', 'sync_status'
        ]
    
    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'course_section': str(obj.session.course_section),
            'scheduled_date': obj.session.scheduled_date,
            'start_datetime': obj.session.start_datetime,
            'room': obj.session.room
        }


class AttendanceRecordDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for Attendance Record"""
    academic_period = AcademicPeriodDetailSerializer(read_only=True)
    student = StudentSerializer(read_only=True)
    session = AttendanceSessionListSerializer(read_only=True)
    is_present = serializers.ReadOnlyField()
    is_absent = serializers.ReadOnlyField()
    is_excused = serializers.ReadOnlyField()
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'academic_period', 'session', 'student',
            'mark', 'marked_at', 'source', 'device_id', 'device_type',
            'ip_address', 'location_lat', 'location_lng',
            'is_present', 'is_absent', 'is_excused',
            'client_uuid', 'sync_status', 'vendor_event_id',
            'marked_by', 'last_modified_by', 'notes',
            'created_at', 'updated_at'
        ]


class AttendanceRecordCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update serializer for Attendance Record"""
    session_id = serializers.IntegerField(write_only=True)
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'session_id', 'student_id', 'mark', 'source',
            'device_id', 'device_type', 'ip_address',
            'location_lat', 'location_lng', 'notes'
        ]
    
    def validate(self, data):
        """Validate attendance record data"""
        session_id = data.get('session_id')
        student_id = data.get('student_id')
        
        if session_id and student_id:
            # Check if student is enrolled in the course section
            session = AttendanceSession.objects.get(id=session_id)
            if not session.course_section.enrollments.filter(student_id=student_id, status='ENROLLED').exists():
                raise serializers.ValidationError("Student is not enrolled in this course section")
        
        return data
    
    def create(self, validated_data):
        """Create attendance record with proper relationships"""
        session_id = validated_data.pop('session_id')
        student_id = validated_data.pop('student_id')
        
        session = AttendanceSession.objects.get(id=session_id)
        student = Student.objects.get(id=student_id)
        
        return AttendanceRecord.objects.create(
            session=session,
            student=student,
            academic_period=session.academic_period,
            **validated_data
        )
    
    def update(self, instance, validated_data):
        """Update attendance record with proper relationships"""
        if 'session_id' in validated_data:
            session_id = validated_data.pop('session_id')
            instance.session = AttendanceSession.objects.get(id=session_id)
            instance.academic_period = instance.session.academic_period
        
        if 'student_id' in validated_data:
            student_id = validated_data.pop('student_id')
            instance.student = Student.objects.get(id=student_id)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# =============================================================================
# BULK OPERATION SERIALIZERS
# =============================================================================

class BulkTimetableSlotCreateSerializer(serializers.Serializer):
    """Serializer for bulk timetable slot creation"""
    academic_period_id = serializers.IntegerField()
    course_section_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    slot_configs = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_academic_period_id(self, value):
        """Validate academic period exists"""
        try:
            AcademicPeriod.objects.get(id=value, is_active=True)
        except AcademicPeriod.DoesNotExist:
            raise serializers.ValidationError("Invalid academic period")
        return value
    
    def validate_course_section_ids(self, value):
        """Validate course sections exist"""
        existing_ids = CourseSection.objects.filter(
            id__in=value, is_active=True
        ).values_list('id', flat=True)
        
        if len(existing_ids) != len(value):
            raise serializers.ValidationError("Some course sections are invalid or inactive")
        return value


class BulkAttendanceSessionCreateSerializer(serializers.Serializer):
    """Serializer for bulk attendance session creation"""
    academic_period_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    timetable_slot_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    def validate_academic_period_id(self, value):
        """Validate academic period exists"""
        try:
            AcademicPeriod.objects.get(id=value, is_active=True)
        except AcademicPeriod.DoesNotExist:
            raise serializers.ValidationError("Invalid academic period")
        return value
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise serializers.ValidationError("Start date must be before end date")
        
        return data


# =============================================================================
# STATISTICS SERIALIZERS
# =============================================================================

class AcademicPeriodStatisticsSerializer(serializers.Serializer):
    """Serializer for academic period statistics"""
    academic_period = AcademicPeriodListSerializer()
    total_slots = serializers.IntegerField()
    active_slots = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    open_sessions = serializers.IntegerField()
    closed_sessions = serializers.IntegerField()
    total_records = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()


class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for student attendance summary"""
    student = StudentSerializer()
    academic_period = AcademicPeriodListSerializer()
    total_sessions = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    is_eligible_for_exam = serializers.BooleanField()


class CourseSectionAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for course section attendance summary"""
    course_section = CourseSectionSerializer()
    academic_period = AcademicPeriodListSerializer()
    total_sessions = serializers.IntegerField()
    total_records = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    enrolled_students_count = serializers.IntegerField()
