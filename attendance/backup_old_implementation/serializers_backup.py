from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from attendance.models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest, 
    LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
    AttendanceConfiguration, get_attendance_settings, get_student_attendance_summary
)
from students.models import Student
from academics.models import CourseSection
from faculty.models import Faculty

User = get_user_model()


class AcademicCalendarHolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicCalendarHoliday
        fields = ['id', 'name', 'date', 'is_full_day', 'academic_year', 'description']


class TimetableSlotSerializer(serializers.ModelSerializer):
    course_section_name = serializers.CharField(source='course_section.__str__', read_only=True)
    faculty_name = serializers.CharField(source='faculty.get_full_name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = TimetableSlot
        fields = [
            'id', 'course_section', 'course_section_name', 'faculty', 'faculty_name',
            'day_of_week', 'day_name', 'start_time', 'end_time', 'room', 
            'is_active', 'academic_year', 'semester'
        ]


class AttendanceSessionSerializer(serializers.ModelSerializer):
    course_section_name = serializers.CharField(source='course_section.__str__', read_only=True)
    faculty_name = serializers.CharField(source='faculty.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_qr_valid = serializers.BooleanField(read_only=True)
    total_students = serializers.SerializerMethodField()
    present_count = serializers.SerializerMethodField()
    absent_count = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course_section', 'course_section_name', 'faculty', 'faculty_name',
            'timetable_slot', 'scheduled_date', 'start_datetime', 'end_datetime',
            'room', 'status', 'status_display', 'auto_opened', 'auto_closed',
            'makeup', 'notes', 'is_qr_valid', 'total_students', 'present_count', 'absent_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['auto_opened', 'auto_closed', 'created_at', 'updated_at']

    def get_total_students(self, obj):
        return obj.snapshots.count()

    def get_present_count(self, obj):
        return obj.records.filter(mark__in=['present', 'late']).count()

    def get_absent_count(self, obj):
        return obj.records.filter(mark='absent').count()


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    mark_display = serializers.CharField(source='get_mark_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.email', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'session', 'student', 'student_name', 'student_roll_number',
            'mark', 'mark_display', 'marked_at', 'source', 'source_display',
            'reason', 'vendor_event_id', 'client_uuid', 'marked_by', 'marked_by_name',
            'ip_address', 'user_agent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['marked_at', 'marked_by', 'ip_address', 'user_agent', 'created_at', 'updated_at']

    def validate(self, attrs):
        session = attrs.get('session')
        if session and session.status not in ('open', 'closed'):
            raise serializers.ValidationError("Session must be open or closed for marking attendance.")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['marked_by'] = request.user
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        return super().create(validated_data)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    session_info = serializers.CharField(source='session.__str__', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.email', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    from_mark_display = serializers.CharField(source='get_from_mark_display', read_only=True)
    to_mark_display = serializers.CharField(source='get_to_mark_display', read_only=True)

    class Meta:
        model = AttendanceCorrectionRequest
        fields = [
            'id', 'session', 'session_info', 'student', 'student_name', 'student_roll_number',
            'requested_by', 'requested_by_name', 'from_mark', 'from_mark_display',
            'to_mark', 'to_mark_display', 'reason', 'status', 'status_display',
            'decided_by', 'decided_by_name', 'decided_at', 'decision_note',
            'supporting_document', 'created_at', 'updated_at'
        ]
        read_only_fields = ['requested_by', 'status', 'decided_by', 'decided_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['requested_by'] = request.user
        return super().create(validated_data)


class LeaveApplicationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.email', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'student', 'student_name', 'student_roll_number', 'leave_type',
            'leave_type_display', 'start_date', 'end_date', 'reason', 'document',
            'status', 'status_display', 'decided_by', 'decided_by_name',
            'decided_at', 'decision_note', 'affects_attendance', 'duration_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'decided_by', 'decided_at', 'created_at', 'updated_at']


class AttendanceConfigurationSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.email', read_only=True)

    class Meta:
        model = AttendanceConfiguration
        fields = [
            'id', 'key', 'value', 'description', 'data_type', 'is_active',
            'updated_by', 'updated_by_name', 'updated_at'
        ]
        read_only_fields = ['updated_by', 'updated_at']


class StudentAttendanceSummarySerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    student_roll_number = serializers.CharField()
    course_section_id = serializers.IntegerField(required=False)
    course_section_name = serializers.CharField(required=False)
    total_sessions = serializers.IntegerField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    excused = serializers.IntegerField()
    percentage = serializers.FloatField()
    leave_days = serializers.IntegerField()
    is_eligible = serializers.BooleanField()
    threshold_percent = serializers.FloatField()


class BulkAttendanceMarkSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    marks = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )

    def validate_marks(self, value):
        """Validate the marks list"""
        for mark_data in value:
            if 'student_id' not in mark_data:
                raise serializers.ValidationError("Each mark must have a student_id")
            if 'mark' not in mark_data:
                raise serializers.ValidationError("Each mark must have a mark value")
            if mark_data['mark'] not in [choice[0] for choice in AttendanceRecord.MARK]:
                raise serializers.ValidationError(f"Invalid mark value: {mark_data['mark']}")
        return value


class QRCheckinSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        """Validate the QR token"""
        import jwt
        from django.conf import settings
        
        try:
            payload = jwt.decode(value, settings.SECRET_KEY, algorithms=["HS256"])
            session_id = payload.get('session_id')
            if not session_id:
                raise serializers.ValidationError("Invalid token: missing session_id")
            
            # Check if session exists and is open
            try:
                session = AttendanceSession.objects.get(id=session_id)
                if session.status not in ['open', 'closed']:
                    raise serializers.ValidationError("Session is not open for check-in")
                if not session.is_qr_valid:
                    raise serializers.ValidationError("QR token has expired")
            except AttendanceSession.DoesNotExist:
                raise serializers.ValidationError("Invalid session")
                
        except jwt.PyJWTError:
            raise serializers.ValidationError("Invalid token")
        
        return value


class OfflineSyncSerializer(serializers.Serializer):
    last_sync_at = serializers.DateTimeField()
    records = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )

    def validate_records(self, value):
        """Validate the offline records"""
        for record in value:
            required_fields = ['client_uuid', 'session', 'mark']
            for field in required_fields:
                if field not in record:
                    raise serializers.ValidationError(f"Each record must have {field}")
            
            if record['mark'] not in [choice[0] for choice in AttendanceRecord.MARK]:
                raise serializers.ValidationError(f"Invalid mark value: {record['mark']}")
        return value


class SessionGenerationSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    course_section_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Specific course sections to generate sessions for"
    )
    academic_year = serializers.CharField(required=False)
    semester = serializers.CharField(required=False)

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date cannot be after end date")
        
        return attrs


class AttendanceReportSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=[
        ('eligibility', 'Exam Eligibility Report'),
        ('summary', 'Attendance Summary Report'),
        ('defaulters', 'Defaulters Report'),
        ('detailed', 'Detailed Attendance Report'),
    ])
    course_section_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    student_batch_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    threshold_percent = serializers.FloatField(required=False, min_value=0, max_value=100)
    format = serializers.ChoiceField(choices=['json', 'csv', 'xlsx'], default='json')


class BiometricWebhookSerializer(serializers.Serializer):
    """Serializer for biometric device webhook data"""
    device_id = serializers.CharField()
    subject_id = serializers.CharField()
    event_type = serializers.ChoiceField(choices=['checkin', 'checkout'])
    timestamp = serializers.DateTimeField()
    vendor_event_id = serializers.CharField()
    location = serializers.CharField(required=False)
    additional_data = serializers.JSONField(required=False)

    def validate_timestamp(self, value):
        """Validate timestamp is not too old"""
        now = timezone.now()
        if (now - value).total_seconds() > 3600:  # 1 hour
            raise serializers.ValidationError("Timestamp is too old")
        return value


class AttendanceStatisticsSerializer(serializers.Serializer):
    """Serializer for attendance statistics"""
    total_sessions = serializers.IntegerField()
    total_students = serializers.IntegerField()
    average_attendance = serializers.FloatField()
    eligible_students = serializers.IntegerField()
    ineligible_students = serializers.IntegerField()
    pending_corrections = serializers.IntegerField()
    pending_leaves = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class NotificationSerializer(serializers.Serializer):
    """Serializer for attendance notifications"""
    notification_type = serializers.ChoiceField(choices=[
        ('low_attendance', 'Low Attendance Alert'),
        ('missed_session', 'Missed Session Alert'),
        ('correction_approved', 'Correction Approved'),
        ('correction_rejected', 'Correction Rejected'),
        ('leave_approved', 'Leave Approved'),
        ('leave_rejected', 'Leave Rejected'),
        ('exam_eligibility', 'Exam Eligibility Status'),
    ])
    recipient_id = serializers.UUIDField()
    recipient_type = serializers.ChoiceField(choices=['student', 'faculty', 'hod', 'admin'])
    title = serializers.CharField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False)
    send_email = serializers.BooleanField(default=True)
    send_sms = serializers.BooleanField(default=False)
    send_push = serializers.BooleanField(default=True)