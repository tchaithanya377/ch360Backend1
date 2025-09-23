"""
Enhanced Attendance Serializers for CampsHub360
DRF serializers for production-ready attendance system
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    AttendanceConfiguration,
    AcademicCalendarHoliday,
    TimetableSlot,
    AttendanceSession,
    StudentSnapshot,
    AttendanceRecord,
    LeaveApplication,
    AttendanceCorrectionRequest,
    AttendanceAuditLog,
    AttendanceStatistics,
    BiometricDevice,
    BiometricTemplate,
    get_attendance_settings,
    compute_attendance_percentage,
    get_student_attendance_summary,
)

User = get_user_model()


# =============================================================================
# CONFIGURATION SERIALIZERS
# =============================================================================

class AttendanceConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for attendance configuration settings"""
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceConfiguration
        fields = [
            'id', 'key', 'value', 'description', 'data_type', 
            'is_active', 'typed_value', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        return obj.get_typed_value()


class AcademicCalendarHolidaySerializer(serializers.ModelSerializer):
    """Serializer for academic calendar holidays"""
    
    class Meta:
        model = AcademicCalendarHoliday
        fields = [
            'id', 'name', 'date', 'is_full_day', 'academic_year',
            'description', 'affects_attendance', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# TIMETABLE SERIALIZERS
# =============================================================================

class TimetableSlotSerializer(serializers.ModelSerializer):
    """Serializer for timetable slots"""
    course_section_name = serializers.CharField(source='course_section.__str__', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    enrolled_students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TimetableSlot
        fields = [
            'id', 'course_section', 'course_section_name', 'faculty', 'faculty_name',
            'day_of_week', 'day_name', 'start_time', 'end_time', 'duration_minutes',
            'room', 'is_active', 'academic_year', 'semester', 'slot_type',
            'max_students', 'enrolled_students_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_enrolled_students_count(self, obj):
        return obj.get_enrolled_students().count()


# =============================================================================
# ATTENDANCE SESSION SERIALIZERS
# =============================================================================

class AttendanceSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for session lists"""
    course_section_name = serializers.CharField(source='course_section.__str__', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    is_qr_valid = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    attendance_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course_section', 'course_section_name', 'faculty', 'faculty_name',
            'scheduled_date', 'start_datetime', 'end_datetime', 'room', 'status',
            'is_qr_valid', 'is_active', 'duration_minutes', 'makeup', 'notes',
            'attendance_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_attendance_summary(self, obj):
        return obj.get_attendance_summary()


class AttendanceSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for attendance sessions"""
    course_section_name = serializers.CharField(source='course_section.__str__', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    is_qr_valid = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    attendance_summary = serializers.SerializerMethodField()
    qr_code_data = serializers.SerializerMethodField()
    student_snapshots = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceSession
        fields = [
            'id', 'course_section', 'course_section_name', 'faculty', 'faculty_name',
            'timetable_slot', 'scheduled_date', 'start_datetime', 'end_datetime',
            'actual_start_datetime', 'actual_end_datetime', 'room', 'status',
            'auto_opened', 'auto_closed', 'makeup', 'notes', 'qr_token', 'qr_expires_at',
            'qr_generated_at', 'is_qr_valid', 'is_active', 'duration_minutes',
            'biometric_enabled', 'biometric_device_id', 'offline_sync_token',
            'last_sync_at', 'attendance_summary', 'qr_code_data', 'student_snapshots',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_attendance_summary(self, obj):
        return obj.get_attendance_summary()
    
    def get_qr_code_data(self, obj):
        if obj.qr_token and obj.is_qr_valid:
            return {
                'token': obj.qr_token,
                'expires_at': obj.qr_expires_at,
                'session_id': obj.id,
                'course_section_id': obj.course_section_id
            }
        return None
    
    def get_student_snapshots(self, obj):
        snapshots = obj.snapshots.all()
        return StudentSnapshotSerializer(snapshots, many=True).data


class AttendanceSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance sessions"""
    
    class Meta:
        model = AttendanceSession
        fields = [
            'course_section', 'faculty', 'timetable_slot', 'scheduled_date',
            'start_datetime', 'end_datetime', 'room', 'makeup', 'notes',
            'biometric_enabled', 'biometric_device_id'
        ]
    
    def create(self, validated_data):
        with transaction.atomic():
            session = AttendanceSession.objects.create(**validated_data)
            
            # Create student snapshots
            enrolled_students = session.course_section.enrollments.filter(
                status='ENROLLED'
            ).select_related('student')
            
            for enrollment in enrolled_students:
                StudentSnapshot.create_snapshot(session, enrollment.student)
            
            return session


class AttendanceSessionActionSerializer(serializers.Serializer):
    """Serializer for session actions (open, close, generate QR)"""
    action = serializers.ChoiceField(choices=['open', 'close', 'generate_qr', 'cancel'])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_action(self, value):
        session = self.context['session']
        if value == 'open' and session.status != 'scheduled':
            raise serializers.ValidationError("Can only open scheduled sessions")
        if value == 'close' and session.status != 'open':
            raise serializers.ValidationError("Can only close open sessions")
        return value


# =============================================================================
# STUDENT SNAPSHOT SERIALIZERS
# =============================================================================

class StudentSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for student snapshots"""
    student_name = serializers.CharField(source='full_name', read_only=True)
    
    class Meta:
        model = StudentSnapshot
        fields = [
            'id', 'session', 'student', 'student_name', 'course_section',
            'student_batch', 'roll_number', 'full_name', 'email', 'phone',
            'academic_year', 'semester', 'year_of_study', 'section',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# ATTENDANCE RECORD SERIALIZERS
# =============================================================================

class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for attendance records"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    session_info = serializers.SerializerMethodField()
    is_present = serializers.BooleanField(read_only=True)
    is_late = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'id', 'session', 'session_info', 'student', 'student_name', 'student_roll_number',
            'mark', 'marked_at', 'source', 'reason', 'notes', 'device_id', 'device_type',
            'ip_address', 'user_agent', 'location_lat', 'location_lng', 'client_uuid',
            'sync_status', 'vendor_event_id', 'vendor_data', 'marked_by', 'last_modified_by',
            'is_present', 'is_late', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'course_section': str(obj.session.course_section),
            'scheduled_date': obj.session.scheduled_date,
            'start_time': obj.session.start_datetime.time(),
            'room': obj.session.room
        }


class AttendanceRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance records"""
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'session', 'student', 'mark', 'source', 'reason', 'notes',
            'device_id', 'device_type', 'ip_address', 'user_agent',
            'location_lat', 'location_lng', 'client_uuid', 'vendor_event_id',
            'vendor_data'
        ]
    
    def create(self, validated_data):
        # Set marked_by from request user
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['marked_by'] = request.user
        
        # Set IP address and user agent
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        record = AttendanceRecord.objects.create(**validated_data)
        
        # Auto-mark as late if appropriate
        record.mark_late_if_appropriate()
        
        return record
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class BulkAttendanceMarkSerializer(serializers.Serializer):
    """Serializer for bulk attendance marking"""
    session_id = serializers.UUIDField()
    attendance_data = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    source = serializers.ChoiceField(
        choices=AttendanceRecord.SOURCE_CHOICES,
        default='manual'
    )
    device_id = serializers.CharField(required=False, allow_blank=True)
    
    def validate_attendance_data(self, value):
        required_fields = ['student_id', 'mark']
        for data in value:
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError(f"Missing required field: {field}")
            
            if data['mark'] not in [choice[0] for choice in AttendanceRecord.MARK_CHOICES]:
                raise serializers.ValidationError(f"Invalid mark: {data['mark']}")
        
        return value
    
    def create(self, validated_data):
        session_id = validated_data['session_id']
        attendance_data = validated_data['attendance_data']
        source = validated_data['source']
        device_id = validated_data.get('device_id', '')
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            raise serializers.ValidationError("Session not found")
        
        # Prepare data for bulk creation
        records_data = []
        for data in attendance_data:
            record_data = {
                'session': session,
                'student_id': data['student_id'],
                'mark': data['mark'],
                'source': source,
                'reason': data.get('reason', ''),
                'device_id': device_id,
            }
            records_data.append(record_data)
        
        # Bulk create records
        records = AttendanceRecord.objects.bulk_create(
            [AttendanceRecord(**data) for data in records_data],
            ignore_conflicts=True
        )
        
        return {'created_count': len(records), 'session': session}


# =============================================================================
# LEAVE APPLICATION SERIALIZERS
# =============================================================================

class LeaveApplicationSerializer(serializers.ModelSerializer):
    """Serializer for leave applications"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)
    
    class Meta:
        model = LeaveApplication
        fields = [
            'id', 'student', 'student_name', 'student_roll_number', 'leave_type',
            'start_date', 'end_date', 'duration_days', 'reason', 'supporting_document',
            'status', 'decided_by', 'decided_by_name', 'decided_at', 'decision_note',
            'affects_attendance', 'auto_apply_to_sessions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'decided_by', 'decided_at']


class LeaveApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leave applications"""
    
    class Meta:
        model = LeaveApplication
        fields = [
            'student', 'leave_type', 'start_date', 'end_date', 'reason',
            'supporting_document', 'affects_attendance', 'auto_apply_to_sessions'
        ]
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date cannot be after end date")
        
        # Check for overlapping leave applications
        overlapping = LeaveApplication.objects.filter(
            student=data['student'],
            start_date__lte=data['end_date'],
            end_date__gte=data['start_date'],
            status__in=['pending', 'approved']
        ).exclude(id=self.instance.id if self.instance else None)
        
        if overlapping.exists():
            raise serializers.ValidationError("Overlapping leave application exists")
        
        return data


class LeaveApplicationActionSerializer(serializers.Serializer):
    """Serializer for leave application actions"""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'cancel'])
    decision_note = serializers.CharField(required=False, allow_blank=True)


# =============================================================================
# CORRECTION REQUEST SERIALIZERS
# =============================================================================

class AttendanceCorrectionRequestSerializer(serializers.ModelSerializer):
    """Serializer for attendance correction requests"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    session_info = serializers.SerializerMethodField()
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.get_full_name', read_only=True)
    
    class Meta:
        model = AttendanceCorrectionRequest
        fields = [
            'id', 'session', 'session_info', 'student', 'student_name', 'student_roll_number',
            'from_mark', 'to_mark', 'reason', 'supporting_document', 'requested_by',
            'requested_by_name', 'status', 'decided_by', 'decided_by_name', 'decided_at',
            'decision_note', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'requested_by', 'decided_by', 'decided_at']
    
    def get_session_info(self, obj):
        return {
            'id': obj.session.id,
            'course_section': str(obj.session.course_section),
            'scheduled_date': obj.session.scheduled_date,
            'start_time': obj.session.start_datetime.time(),
            'room': obj.session.room
        }


class AttendanceCorrectionRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating correction requests"""
    
    class Meta:
        model = AttendanceCorrectionRequest
        fields = [
            'session', 'student', 'from_mark', 'to_mark', 'reason', 'supporting_document'
        ]
    
    def validate(self, data):
        if data['from_mark'] == data['to_mark']:
            raise serializers.ValidationError("From mark and to mark cannot be the same")
        
        # Check if correction request already exists
        existing = AttendanceCorrectionRequest.objects.filter(
            session=data['session'],
            student=data['student'],
            status='pending'
        )
        
        if existing.exists():
            raise serializers.ValidationError("Pending correction request already exists")
        
        return data


class AttendanceCorrectionRequestActionSerializer(serializers.Serializer):
    """Serializer for correction request actions"""
    action = serializers.ChoiceField(choices=['approve', 'reject', 'cancel'])
    decision_note = serializers.CharField(required=False, allow_blank=True)


# =============================================================================
# STATISTICS AND ANALYTICS SERIALIZERS
# =============================================================================

class AttendanceStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for attendance statistics"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    course_section_name = serializers.CharField(source='course_section.__str__', read_only=True)
    
    class Meta:
        model = AttendanceStatistics
        fields = [
            'id', 'student', 'student_name', 'student_roll_number', 'course_section',
            'course_section_name', 'academic_year', 'semester', 'total_sessions',
            'present_count', 'absent_count', 'late_count', 'excused_count',
            'attendance_percentage', 'is_eligible_for_exam', 'period_start',
            'period_end', 'last_calculated', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for student attendance summary"""
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    student_roll_number = serializers.CharField()
    course_section_id = serializers.IntegerField()
    course_section_name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    leave_days = serializers.IntegerField()
    is_eligible_for_exam = serializers.BooleanField()
    threshold_percent = serializers.IntegerField()


class CourseAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for course attendance summary"""
    course_section_id = serializers.IntegerField()
    course_section_name = serializers.CharField()
    faculty_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    average_attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    eligible_students_count = serializers.IntegerField()
    ineligible_students_count = serializers.IntegerField()
    attendance_distribution = serializers.DictField()


# =============================================================================
# BIOMETRIC SERIALIZERS
# =============================================================================

class BiometricDeviceSerializer(serializers.ModelSerializer):
    """Serializer for biometric devices"""
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BiometricDevice
        fields = [
            'id', 'device_id', 'device_name', 'device_type', 'device_type_display',
            'location', 'room', 'status', 'status_display', 'last_seen',
            'firmware_version', 'is_enabled', 'auto_sync', 'sync_interval_minutes',
            'ip_address', 'port', 'api_endpoint', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_seen']


class BiometricTemplateSerializer(serializers.ModelSerializer):
    """Serializer for biometric templates"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = BiometricTemplate
        fields = [
            'id', 'student', 'student_name', 'student_roll_number', 'device',
            'device_name', 'template_hash', 'quality_score', 'is_active',
            'enrolled_at', 'last_used', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'template_hash', 'enrolled_at']


# =============================================================================
# AUDIT LOG SERIALIZERS
# =============================================================================

class AttendanceAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for attendance audit logs"""
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    
    class Meta:
        model = AttendanceAuditLog
        fields = [
            'id', 'entity_type', 'entity_id', 'action', 'performed_by',
            'performed_by_name', 'before', 'after', 'reason', 'source',
            'ip_address', 'user_agent', 'session_id', 'student_id',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =============================================================================
# QR CODE SERIALIZERS
# =============================================================================

class QRCodeScanSerializer(serializers.Serializer):
    """Serializer for QR code scanning"""
    qr_token = serializers.CharField()
    student_id = serializers.UUIDField()
    device_id = serializers.CharField(required=False, allow_blank=True)
    location_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    location_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    
    def validate_qr_token(self, value):
        import jwt
        try:
            payload = jwt.decode(value, settings.SECRET_KEY, algorithms=["HS256"])
            session_id = payload.get('session_id')
            if not session_id:
                raise serializers.ValidationError("Invalid QR token")
            
            try:
                session = AttendanceSession.objects.get(id=session_id)
                if not session.is_qr_valid:
                    raise serializers.ValidationError("QR token has expired")
                
                self.context['session'] = session
                return value
            except AttendanceSession.DoesNotExist:
                raise serializers.ValidationError("Session not found")
        except jwt.InvalidTokenError:
            raise serializers.ValidationError("Invalid QR token")


# =============================================================================
# EXPORT SERIALIZERS
# =============================================================================

class AttendanceExportSerializer(serializers.Serializer):
    """Serializer for attendance data export"""
    format = serializers.ChoiceField(choices=['csv', 'excel', 'pdf'])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    course_sections = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    students = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    include_details = serializers.BooleanField(default=True)
    include_statistics = serializers.BooleanField(default=True)
    
    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date cannot be after end date")
        return data
