"""
Enhanced Attendance Tests for CampsHub360
Comprehensive test suite for attendance system
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from .models_enhanced import (
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
    generate_sessions_from_timetable,
)

from .factories_enhanced import (
    UserFactory,
    DepartmentFactory,
    AcademicYearFactory,
    AcademicProgramFactory,
    StudentBatchFactory,
    StudentFactory,
    FacultyFactory,
    CourseFactory,
    CourseSectionFactory,
    AttendanceConfigurationFactory,
    AcademicCalendarHolidayFactory,
    TimetableSlotFactory,
    AttendanceSessionFactory,
    StudentSnapshotFactory,
    AttendanceRecordFactory,
    LeaveApplicationFactory,
    AttendanceCorrectionRequestFactory,
    AttendanceAuditLogFactory,
    AttendanceStatisticsFactory,
    BiometricDeviceFactory,
    BiometricTemplateFactory,
    PresentAttendanceRecordFactory,
    AbsentAttendanceRecordFactory,
    LateAttendanceRecordFactory,
    ExcusedAttendanceRecordFactory,
    OpenAttendanceSessionFactory,
    ClosedAttendanceSessionFactory,
    ApprovedLeaveApplicationFactory,
    PendingLeaveApplicationFactory,
    ApprovedCorrectionRequestFactory,
    PendingCorrectionRequestFactory,
    EligibleStudentStatisticsFactory,
    IneligibleStudentStatisticsFactory,
)

User = get_user_model()


class AttendanceConfigurationModelTest(TestCase):
    """Test cases for AttendanceConfiguration model"""
    
    def setUp(self):
        self.config = AttendanceConfigurationFactory(
            key='TEST_CONFIG',
            value='test_value',
            data_type='string'
        )
    
    def test_string_value(self):
        """Test string value retrieval"""
        self.assertEqual(self.config.get_typed_value(), 'test_value')
    
    def test_integer_value(self):
        """Test integer value retrieval"""
        config = AttendanceConfigurationFactory(
            key='TEST_INT',
            value='42',
            data_type='integer'
        )
        self.assertEqual(config.get_typed_value(), 42)
    
    def test_float_value(self):
        """Test float value retrieval"""
        config = AttendanceConfigurationFactory(
            key='TEST_FLOAT',
            value='3.14',
            data_type='float'
        )
        self.assertEqual(config.get_typed_value(), 3.14)
    
    def test_boolean_value(self):
        """Test boolean value retrieval"""
        config = AttendanceConfigurationFactory(
            key='TEST_BOOL',
            value='true',
            data_type='boolean'
        )
        self.assertTrue(config.get_typed_value())
    
    def test_json_value(self):
        """Test JSON value retrieval"""
        config = AttendanceConfigurationFactory(
            key='TEST_JSON',
            value='{"key": "value"}',
            data_type='json'
        )
        self.assertEqual(config.get_typed_value(), {"key": "value"})
    
    def test_get_setting_with_default(self):
        """Test getting setting with default value"""
        value = AttendanceConfiguration.get_setting('NON_EXISTENT', 'default')
        self.assertEqual(value, 'default')
    
    def test_get_setting_existing(self):
        """Test getting existing setting"""
        value = AttendanceConfiguration.get_setting('TEST_CONFIG', 'default')
        self.assertEqual(value, 'test_value')


class TimetableSlotModelTest(TestCase):
    """Test cases for TimetableSlot model"""
    
    def setUp(self):
        self.slot = TimetableSlotFactory()
    
    def test_duration_calculation(self):
        """Test duration calculation in minutes"""
        # 9:00 to 9:50 should be 50 minutes
        self.slot.start_time = datetime.strptime('09:00:00', '%H:%M:%S').time()
        self.slot.end_time = datetime.strptime('09:50:00', '%H:%M:%S').time()
        self.assertEqual(self.slot.duration_minutes, 50)
    
    def test_str_representation(self):
        """Test string representation"""
        expected = f"{self.slot.course_section} - {self.slot.get_day_of_week_display()} {self.slot.start_time}-{self.slot.end_time}"
        self.assertEqual(str(self.slot), expected)


class AttendanceSessionModelTest(TestCase):
    """Test cases for AttendanceSession model"""
    
    def setUp(self):
        self.session = AttendanceSessionFactory()
    
    def test_qr_token_validation(self):
        """Test QR token validation"""
        # Initially no QR token
        self.assertFalse(self.session.is_qr_valid)
        
        # Generate QR token
        self.session.generate_qr_token()
        self.assertTrue(self.session.is_qr_valid)
        
        # Expire the token
        self.session.qr_expires_at = timezone.now() - timedelta(minutes=1)
        self.assertFalse(self.session.is_qr_valid)
    
    def test_session_status_transitions(self):
        """Test session status transitions"""
        # Start as scheduled
        self.assertEqual(self.session.status, 'scheduled')
        
        # Open session
        self.session.open_session()
        self.assertEqual(self.session.status, 'open')
        self.assertIsNotNone(self.session.actual_start_datetime)
        
        # Close session
        self.session.close_session()
        self.assertEqual(self.session.status, 'closed')
        self.assertIsNotNone(self.session.actual_end_datetime)
    
    def test_attendance_summary(self):
        """Test attendance summary calculation"""
        # Create some attendance records
        PresentAttendanceRecordFactory(session=self.session)
        PresentAttendanceRecordFactory(session=self.session)
        AbsentAttendanceRecordFactory(session=self.session)
        LateAttendanceRecordFactory(session=self.session)
        
        summary = self.session.get_attendance_summary()
        
        self.assertEqual(summary['total_students'], 4)
        self.assertEqual(summary['present'], 2)
        self.assertEqual(summary['absent'], 1)
        self.assertEqual(summary['late'], 1)
        self.assertEqual(summary['attendance_percentage'], 75.0)  # 3 present out of 4 total
    
    def test_duration_calculation(self):
        """Test session duration calculation"""
        # Set actual start and end times
        start_time = timezone.now()
        end_time = start_time + timedelta(minutes=50)
        
        self.session.actual_start_datetime = start_time
        self.session.actual_end_datetime = end_time
        
        self.assertEqual(self.session.duration_minutes, 50)


class StudentSnapshotModelTest(TestCase):
    """Test cases for StudentSnapshot model"""
    
    def setUp(self):
        self.session = AttendanceSessionFactory()
        self.student = StudentFactory()
    
    def test_create_snapshot(self):
        """Test creating student snapshot"""
        snapshot = StudentSnapshot.create_snapshot(self.session, self.student)
        
        self.assertEqual(snapshot.session, self.session)
        self.assertEqual(snapshot.student, self.student)
        self.assertEqual(snapshot.roll_number, self.student.roll_number)
        self.assertEqual(snapshot.full_name, self.student.full_name)


class AttendanceRecordModelTest(TestCase):
    """Test cases for AttendanceRecord model"""
    
    def setUp(self):
        self.record = AttendanceRecordFactory()
    
    def test_present_property(self):
        """Test is_present property"""
        self.record.mark = 'present'
        self.assertTrue(self.record.is_present)
        
        self.record.mark = 'late'
        self.assertTrue(self.record.is_present)
        
        self.record.mark = 'absent'
        self.assertFalse(self.record.is_present)
    
    def test_late_property(self):
        """Test is_late property"""
        self.record.mark = 'late'
        self.assertTrue(self.record.is_late)
        
        self.record.mark = 'present'
        self.assertFalse(self.record.is_late)
    
    def test_absent_property(self):
        """Test is_absent property"""
        self.record.mark = 'absent'
        self.assertTrue(self.record.is_absent)
        
        self.record.mark = 'present'
        self.assertFalse(self.record.is_absent)
    
    def test_excused_property(self):
        """Test is_excused property"""
        self.record.mark = 'excused'
        self.assertTrue(self.record.is_excused)
        
        self.record.mark = 'present'
        self.assertFalse(self.record.is_excused)
    
    @patch('attendance.models_enhanced.AttendanceConfiguration.get_setting')
    def test_mark_late_if_appropriate(self, mock_get_setting):
        """Test automatic late marking"""
        mock_get_setting.return_value = 5  # 5 minutes grace period
        
        # Create session that started 10 minutes ago
        session = AttendanceSessionFactory()
        session.start_datetime = timezone.now() - timedelta(minutes=10)
        session.save()
        
        # Create record marked as present
        record = AttendanceRecordFactory(session=session, mark='present')
        record.marked_at = timezone.now()
        
        # Should be marked as late
        record.mark_late_if_appropriate()
        self.assertEqual(record.mark, 'late')


class LeaveApplicationModelTest(TestCase):
    """Test cases for LeaveApplication model"""
    
    def setUp(self):
        self.leave = LeaveApplicationFactory()
    
    def test_duration_calculation(self):
        """Test leave duration calculation"""
        self.leave.start_date = date(2024, 1, 1)
        self.leave.end_date = date(2024, 1, 3)
        
        self.assertEqual(self.leave.duration_days, 3)
    
    def test_approve_leave(self):
        """Test leave approval"""
        user = UserFactory()
        
        self.leave.approve(user, "Approved for medical reasons")
        
        self.assertEqual(self.leave.status, 'approved')
        self.assertEqual(self.leave.decided_by, user)
        self.assertIsNotNone(self.leave.decided_at)
        self.assertEqual(self.leave.decision_note, "Approved for medical reasons")
    
    def test_reject_leave(self):
        """Test leave rejection"""
        user = UserFactory()
        
        self.leave.reject(user, "Insufficient documentation")
        
        self.assertEqual(self.leave.status, 'rejected')
        self.assertEqual(self.leave.decided_by, user)
        self.assertIsNotNone(self.leave.decided_at)
        self.assertEqual(self.leave.decision_note, "Insufficient documentation")


class AttendanceCorrectionRequestModelTest(TestCase):
    """Test cases for AttendanceCorrectionRequest model"""
    
    def setUp(self):
        self.correction = AttendanceCorrectionRequestFactory()
    
    def test_approve_correction(self):
        """Test correction request approval"""
        user = UserFactory()
        
        # Create an attendance record to correct
        record = AttendanceRecordFactory(
            session=self.correction.session,
            student=self.correction.student,
            mark=self.correction.from_mark
        )
        
        self.correction.approve(user, "Correction approved")
        
        self.assertEqual(self.correction.status, 'approved')
        self.assertEqual(self.correction.decided_by, user)
        self.assertIsNotNone(self.correction.decided_at)
        
        # Check that the attendance record was updated
        record.refresh_from_db()
        self.assertEqual(record.mark, self.correction.to_mark)
    
    def test_reject_correction(self):
        """Test correction request rejection"""
        user = UserFactory()
        
        self.correction.reject(user, "Insufficient evidence")
        
        self.assertEqual(self.correction.status, 'rejected')
        self.assertEqual(self.correction.decided_by, user)
        self.assertIsNotNone(self.correction.decided_at)
        self.assertEqual(self.correction.decision_note, "Insufficient evidence")


class AttendanceStatisticsModelTest(TestCase):
    """Test cases for AttendanceStatistics model"""
    
    def setUp(self):
        self.stats = AttendanceStatisticsFactory()
    
    def test_percentage_calculation(self):
        """Test attendance percentage calculation"""
        # 20 present out of 25 total sessions (excluding 2 excused)
        self.stats.total_sessions = 25
        self.stats.present_count = 20
        self.stats.excused_count = 2
        
        self.stats.calculate_percentage()
        
        # Should be 20/23 = 86.96%
        expected_percentage = round((20 / 23) * 100, 2)
        self.assertEqual(self.stats.attendance_percentage, expected_percentage)
    
    def test_exam_eligibility(self):
        """Test exam eligibility calculation"""
        # Test eligible student
        self.stats.attendance_percentage = 80.0
        self.stats.calculate_percentage()
        self.assertTrue(self.stats.is_eligible_for_exam)
        
        # Test ineligible student
        self.stats.attendance_percentage = 70.0
        self.stats.calculate_percentage()
        self.assertFalse(self.stats.is_eligible_for_exam)


class UtilityFunctionsTest(TestCase):
    """Test cases for utility functions"""
    
    def test_compute_attendance_percentage(self):
        """Test attendance percentage computation"""
        # Basic calculation
        percentage = compute_attendance_percentage(15, 20)
        self.assertEqual(percentage, 75.0)
        
        # With excused absences
        percentage = compute_attendance_percentage(15, 20, excused_count=2)
        self.assertEqual(percentage, 83.33)  # 15/18 = 83.33%
        
        # Zero sessions
        percentage = compute_attendance_percentage(0, 0)
        self.assertEqual(percentage, 0.0)
    
    def test_get_student_attendance_summary(self):
        """Test student attendance summary"""
        student = StudentFactory()
        course_section = CourseSectionFactory()
        
        # Create some attendance records
        session1 = AttendanceSessionFactory(course_section=course_section)
        session2 = AttendanceSessionFactory(course_section=course_section)
        session3 = AttendanceSessionFactory(course_section=course_section)
        
        PresentAttendanceRecordFactory(session=session1, student=student)
        PresentAttendanceRecordFactory(session=session2, student=student)
        AbsentAttendanceRecordFactory(session=session3, student=student)
        
        summary = get_student_attendance_summary(student, course_section)
        
        self.assertEqual(summary['total_sessions'], 3)
        self.assertEqual(summary['present'], 2)
        self.assertEqual(summary['absent'], 1)
        self.assertEqual(summary['attendance_percentage'], 66.67)  # 2/3 = 66.67%
    
    def test_generate_sessions_from_timetable(self):
        """Test session generation from timetable"""
        # Create timetable slot for Monday (day 0)
        slot = TimetableSlotFactory(day_of_week=0)
        
        # Generate sessions for a week that includes Monday
        start_date = date(2024, 1, 1)  # Monday
        end_date = date(2024, 1, 7)    # Sunday
        
        sessions_created = generate_sessions_from_timetable(start_date, end_date)
        
        self.assertEqual(sessions_created, 1)
        
        # Verify session was created
        session = AttendanceSession.objects.filter(
            timetable_slot=slot,
            scheduled_date=start_date
        ).first()
        
        self.assertIsNotNone(session)
        self.assertEqual(session.course_section, slot.course_section)
        self.assertEqual(session.faculty, slot.faculty)


class BiometricDeviceModelTest(TestCase):
    """Test cases for BiometricDevice model"""
    
    def setUp(self):
        self.device = BiometricDeviceFactory()
    
    def test_str_representation(self):
        """Test string representation"""
        expected = f"{self.device.device_name} ({self.device.device_id})"
        self.assertEqual(str(self.device), expected)


class BiometricTemplateModelTest(TestCase):
    """Test cases for BiometricTemplate model"""
    
    def setUp(self):
        self.template = BiometricTemplateFactory()
    
    def test_str_representation(self):
        """Test string representation"""
        expected = f"{self.template.student.roll_number} - {self.template.device.device_name}"
        self.assertEqual(str(self.template), expected)


class AttendanceAuditLogModelTest(TestCase):
    """Test cases for AttendanceAuditLog model"""
    
    def setUp(self):
        self.audit_log = AttendanceAuditLogFactory()
    
    def test_str_representation(self):
        """Test string representation"""
        expected = f"{self.audit_log.action} on {self.audit_log.entity_type} by {self.audit_log.performed_by}"
        self.assertEqual(str(self.audit_log), expected)


class IntegrationTest(TestCase):
    """Integration tests for the attendance system"""
    
    def setUp(self):
        # Create test data
        self.department = DepartmentFactory()
        self.academic_year = AcademicYearFactory()
        self.program = AcademicProgramFactory(department=self.department)
        self.batch = StudentBatchFactory(
            department=self.department,
            academic_program=self.program,
            academic_year=self.academic_year
        )
        self.student = StudentFactory(student_batch=self.batch)
        self.faculty = FacultyFactory()
        self.course = CourseFactory()
        self.course_section = CourseSectionFactory(
            course=self.course,
            student_batch=self.batch,
            faculty=self.faculty
        )
        self.timetable_slot = TimetableSlotFactory(
            course_section=self.course_section,
            faculty=self.faculty
        )
    
    def test_complete_attendance_workflow(self):
        """Test complete attendance workflow"""
        # 1. Generate session from timetable
        session_date = date.today()
        sessions_created = generate_sessions_from_timetable(
            session_date, session_date,
            course_sections=[self.course_section]
        )
        self.assertEqual(sessions_created, 1)
        
        # 2. Get the created session
        session = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=session_date
        ).first()
        self.assertIsNotNone(session)
        
        # 3. Open the session
        session.open_session()
        self.assertEqual(session.status, 'open')
        
        # 4. Mark attendance
        record = AttendanceRecord.objects.create(
            session=session,
            student=self.student,
            mark='present',
            source='manual'
        )
        
        # 5. Close the session
        session.close_session()
        self.assertEqual(session.status, 'closed')
        
        # 6. Verify attendance summary
        summary = session.get_attendance_summary()
        self.assertEqual(summary['total_students'], 1)
        self.assertEqual(summary['present'], 1)
        self.assertEqual(summary['attendance_percentage'], 100.0)
    
    def test_leave_application_workflow(self):
        """Test leave application workflow"""
        # 1. Create leave application
        leave = LeaveApplication.objects.create(
            student=self.student,
            leave_type='medical',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            reason='Medical emergency',
            affects_attendance=True
        )
        
        # 2. Approve leave
        user = UserFactory()
        leave.approve(user, "Medical documentation provided")
        
        self.assertEqual(leave.status, 'approved')
        self.assertEqual(leave.decided_by, user)
    
    def test_correction_request_workflow(self):
        """Test correction request workflow"""
        # 1. Create session and mark student absent
        session = AttendanceSessionFactory(course_section=self.course_section)
        record = AttendanceRecord.objects.create(
            session=session,
            student=self.student,
            mark='absent',
            source='manual'
        )
        
        # 2. Create correction request
        user = UserFactory()
        correction = AttendanceCorrectionRequest.objects.create(
            session=session,
            student=self.student,
            from_mark='absent',
            to_mark='present',
            reason='Student was present but not marked',
            requested_by=user
        )
        
        # 3. Approve correction
        admin_user = UserFactory()
        correction.approve(admin_user, "Verified with faculty")
        
        # 4. Verify record was updated
        record.refresh_from_db()
        self.assertEqual(record.mark, 'present')
        self.assertEqual(correction.status, 'approved')


@pytest.mark.django_db
class PytestAttendanceTests:
    """Pytest-based tests for attendance system"""
    
    def test_attendance_configuration_creation(self):
        """Test attendance configuration creation"""
        config = AttendanceConfigurationFactory()
        assert config.key is not None
        assert config.value is not None
        assert config.is_active is True
    
    def test_timetable_slot_creation(self):
        """Test timetable slot creation"""
        slot = TimetableSlotFactory()
        assert slot.course_section is not None
        assert slot.faculty is not None
        assert slot.day_of_week in range(7)
        assert slot.duration_minutes > 0
    
    def test_attendance_session_creation(self):
        """Test attendance session creation"""
        session = AttendanceSessionFactory()
        assert session.course_section is not None
        assert session.faculty is not None
        assert session.status == 'scheduled'
        assert session.scheduled_date is not None
    
    def test_attendance_record_creation(self):
        """Test attendance record creation"""
        record = AttendanceRecordFactory()
        assert record.session is not None
        assert record.student is not None
        assert record.mark in ['present', 'absent', 'late', 'excused']
        assert record.source in ['manual', 'qr', 'biometric', 'rfid']
    
    def test_leave_application_creation(self):
        """Test leave application creation"""
        leave = LeaveApplicationFactory()
        assert leave.student is not None
        assert leave.leave_type in ['medical', 'personal', 'on_duty', 'emergency']
        assert leave.start_date <= leave.end_date
        assert leave.duration_days > 0
    
    def test_biometric_device_creation(self):
        """Test biometric device creation"""
        device = BiometricDeviceFactory()
        assert device.device_id is not None
        assert device.device_name is not None
        assert device.device_type in ['fingerprint', 'face', 'iris', 'palm']
        assert device.status in ['active', 'inactive', 'maintenance', 'error']
    
    def test_attendance_statistics_creation(self):
        """Test attendance statistics creation"""
        stats = AttendanceStatisticsFactory()
        assert stats.student is not None
        assert stats.course_section is not None
        assert stats.total_sessions >= 0
        assert stats.present_count >= 0
        assert stats.attendance_percentage >= 0.0
        assert isinstance(stats.is_eligible_for_exam, bool)
