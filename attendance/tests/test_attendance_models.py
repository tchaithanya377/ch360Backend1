"""
Comprehensive tests for the new attendance models.
Tests model creation, constraints, methods, and business logic.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import date, time, datetime, timedelta

from attendance.models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest,
    LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
    AttendanceConfiguration, get_attendance_settings, get_student_attendance_summary,
    StudentSnapshot, compute_attendance_percentage
)
from attendance.factories import (
    AttendanceSessionFactory, AttendanceRecordFactory,
    PresentAttendanceRecordFactory, AbsentAttendanceRecordFactory,
    QRAttendanceRecordFactory, BiometricAttendanceRecordFactory,
    OpenAttendanceSessionFactory, ClosedAttendanceSessionFactory,
    LockedAttendanceSessionFactory, StudentFactory, CourseSectionFactory,
    TimetableSlotFactory, FacultyFactory, AttendanceCorrectionRequestFactory,
    LeaveApplicationFactory, AcademicCalendarHolidayFactory,
    AttendanceConfigurationFactory, StudentSnapshotFactory
)


class TestAttendanceSessionModel(TestCase):
    """Test cases for AttendanceSession model"""

    def setUp(self):
        """Set up test data"""
        self.course_section = CourseSectionFactory()
        self.faculty = FacultyFactory()
        self.timetable_slot = TimetableSlotFactory(
            course_section=self.course_section,
            faculty=self.faculty
        )

    def test_attendance_session_creation(self):
        """Test basic attendance session creation"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            timetable_slot=self.timetable_slot
        )
        
        self.assertIsNotNone(session.id)
        self.assertEqual(session.course_section, self.course_section)
        self.assertEqual(session.faculty, self.faculty)
        self.assertEqual(session.timetable_slot, self.timetable_slot)
        self.assertIsNotNone(session.scheduled_date)
        self.assertIsNotNone(session.start_datetime)
        self.assertIsNotNone(session.end_datetime)
        self.assertEqual(session.status, 'scheduled')
        self.assertFalse(session.auto_opened)
        self.assertFalse(session.auto_closed)
        self.assertFalse(session.makeup)

    def test_attendance_session_str_representation(self):
        """Test string representation of attendance session"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 15),
            start_datetime=timezone.datetime(2024, 9, 15, 9, 0, tzinfo=timezone.get_current_timezone())
        )
        
        expected_str = f"{self.course_section} - 2024-09-15 09:00:00"
        self.assertEqual(str(session), expected_str)

    def test_attendance_session_status_choices(self):
        """Test all valid status choices"""
        valid_statuses = ['scheduled', 'open', 'closed', 'locked', 'cancelled']
        
        for status in valid_statuses:
            session = AttendanceSessionFactory(
                course_section=self.course_section,
                faculty=self.faculty,
                status=status
            )
            self.assertEqual(session.status, status)

    def test_attendance_session_unique_constraint(self):
        """Test unique constraint on timetable_slot and scheduled_date"""
        session1 = AttendanceSessionFactory(
            timetable_slot=self.timetable_slot,
            scheduled_date=date(2024, 9, 15)
        )
        
        # Creating another session with same timetable_slot and scheduled_date should fail
        with self.assertRaises(IntegrityError):
            AttendanceSession.objects.create(
                course_section=self.course_section,
                faculty=self.faculty,
                timetable_slot=self.timetable_slot,
                scheduled_date=date(2024, 9, 15),
                start_datetime=timezone.now(),
                end_datetime=timezone.now() + timedelta(hours=1)
            )

    def test_attendance_session_qr_token_generation(self):
        """Test QR token generation"""
        session = OpenAttendanceSessionFactory(course_section=self.course_section)
        
        # Generate QR token
        session.generate_qr_token()
        
        self.assertIsNotNone(session.qr_token)
        self.assertIsNotNone(session.qr_expires_at)
        self.assertTrue(session.is_qr_valid)

    def test_attendance_session_qr_token_expiry(self):
        """Test QR token expiry"""
        session = OpenAttendanceSessionFactory(course_section=self.course_section)
        
        # Generate QR token
        session.generate_qr_token()
        
        # Manually set expiry to past
        session.qr_expires_at = timezone.now() - timedelta(minutes=1)
        session.save()
        
        self.assertFalse(session.is_qr_valid)


class TestAttendanceRecordModel(TestCase):
    """Test cases for AttendanceRecord model"""

    def setUp(self):
        """Set up test data"""
        self.session = AttendanceSessionFactory()
        self.student = StudentFactory()

    def test_attendance_record_creation(self):
        """Test basic attendance record creation"""
        record = AttendanceRecordFactory(
            session=self.session,
            student=self.student
        )
        
        self.assertIsNotNone(record.id)
        self.assertEqual(record.session, self.session)
        self.assertEqual(record.student, self.student)
        self.assertIsNotNone(record.mark)
        self.assertIsNotNone(record.marked_at)
        self.assertEqual(record.source, 'manual')

    def test_attendance_record_str_representation(self):
        """Test string representation of attendance record"""
        record = AttendanceRecordFactory(
            session=self.session,
            student=self.student,
            mark='present'
        )
        
        expected_str = f"{self.student.roll_number} - {self.session} - present"
        self.assertEqual(str(record), expected_str)

    def test_attendance_record_mark_choices(self):
        """Test all valid mark choices"""
        valid_marks = ['present', 'absent', 'late', 'excused']
        
        for mark in valid_marks:
            student = StudentFactory()  # Create a new student for each record
            record = AttendanceRecordFactory(
                session=self.session,
                student=student,
                mark=mark
            )
            self.assertEqual(record.mark, mark)

    def test_attendance_record_source_choices(self):
        """Test all valid source choices"""
        valid_sources = ['manual', 'qr', 'biometric', 'rfid', 'offline', 'import', 'system']
        
        for source in valid_sources:
            student = StudentFactory()  # Create a new student for each record
            record = AttendanceRecordFactory(
                session=self.session,
                student=student,
                source=source
            )
            self.assertEqual(record.source, source)

    def test_attendance_record_unique_constraint(self):
        """Test unique constraint on session and student"""
        record1 = AttendanceRecordFactory(
            session=self.session,
            student=self.student
        )
        
        # Creating another record with same session and student should fail
        with self.assertRaises(IntegrityError):
            AttendanceRecord.objects.create(
                session=self.session,
                student=self.student,
                mark='absent'
            )

    def test_attendance_record_is_present_property(self):
        """Test is_present property"""
        # Test present record
        present_record = PresentAttendanceRecordFactory(
            session=self.session,
            student=self.student
        )
        self.assertTrue(present_record.is_present)
        
        # Test late record (should be considered present)
        late_student = StudentFactory()  # Create a new student for the late record
        late_record = AttendanceRecordFactory(
            session=self.session,
            student=late_student,
            mark='late'
        )
        self.assertTrue(late_record.is_present)
        
        # Test absent record
        absent_student = StudentFactory()  # Create a new student for the absent record
        absent_record = AbsentAttendanceRecordFactory(
            session=self.session,
            student=absent_student
        )
        self.assertFalse(absent_record.is_present)


class TestAttendanceCorrectionRequestModel(TestCase):
    """Test cases for AttendanceCorrectionRequest model"""

    def setUp(self):
        """Set up test data"""
        self.session = AttendanceSessionFactory()
        self.student = StudentFactory()
        self.user = self.student.user

    def test_correction_request_creation(self):
        """Test basic correction request creation"""
        correction_request = AttendanceCorrectionRequestFactory(
            session=self.session,
            student=self.student,
            requested_by=self.user
        )
        
        self.assertIsNotNone(correction_request.id)
        self.assertEqual(correction_request.session, self.session)
        self.assertEqual(correction_request.student, self.student)
        self.assertEqual(correction_request.requested_by, self.user)
        self.assertEqual(correction_request.status, 'pending')

    def test_correction_request_str_representation(self):
        """Test string representation of correction request"""
        correction_request = AttendanceCorrectionRequestFactory(
            session=self.session,
            student=self.student,
            from_mark='absent',
            to_mark='present'
        )
        
        expected_str = f"{self.student.roll_number} - absent to present"
        self.assertEqual(str(correction_request), expected_str)

    def test_correction_request_status_choices(self):
        """Test all valid status choices"""
        valid_statuses = ['pending', 'approved', 'rejected', 'cancelled']
        
        for status in valid_statuses:
            correction_request = AttendanceCorrectionRequestFactory(
                session=self.session,
                student=self.student,
                status=status
            )
            self.assertEqual(correction_request.status, status)


class TestLeaveApplicationModel(TestCase):
    """Test cases for LeaveApplication model"""

    def setUp(self):
        """Set up test data"""
        self.student = StudentFactory()

    def test_leave_application_creation(self):
        """Test basic leave application creation"""
        leave_application = LeaveApplicationFactory(student=self.student)
        
        self.assertIsNotNone(leave_application.id)
        self.assertEqual(leave_application.student, self.student)
        self.assertEqual(leave_application.status, 'pending')
        self.assertTrue(leave_application.affects_attendance)

    def test_leave_application_str_representation(self):
        """Test string representation of leave application"""
        leave_application = LeaveApplicationFactory(
            student=self.student,
            leave_type='medical',
            start_date=date(2024, 9, 15),
            end_date=date(2024, 9, 17)
        )
        
        expected_str = f"{self.student.roll_number} - medical (2024-09-15 to 2024-09-17)"
        self.assertEqual(str(leave_application), expected_str)

    def test_leave_application_duration_days(self):
        """Test duration_days property"""
        leave_application = LeaveApplicationFactory(
            student=self.student,
            start_date=date(2024, 9, 15),
            end_date=date(2024, 9, 17)
        )
        
        # Should be 3 days (15th, 16th, 17th)
        self.assertEqual(leave_application.duration_days, 3)

    def test_leave_application_type_choices(self):
        """Test all valid leave type choices"""
        valid_types = ['medical', 'maternity', 'on_duty', 'sport', 'personal', 'other']
        
        for leave_type in valid_types:
            leave_application = LeaveApplicationFactory(
                student=self.student,
                leave_type=leave_type
            )
            self.assertEqual(leave_application.leave_type, leave_type)


class TestTimetableSlotModel(TestCase):
    """Test cases for TimetableSlot model"""

    def setUp(self):
        """Set up test data"""
        self.course_section = CourseSectionFactory()
        self.faculty = FacultyFactory()

    def test_timetable_slot_creation(self):
        """Test basic timetable slot creation"""
        slot = TimetableSlotFactory(
            course_section=self.course_section,
            faculty=self.faculty
        )
        
        self.assertIsNotNone(slot.id)
        self.assertEqual(slot.course_section, self.course_section)
        self.assertEqual(slot.faculty, self.faculty)
        self.assertIsNotNone(slot.day_of_week)
        self.assertIsNotNone(slot.start_time)
        self.assertIsNotNone(slot.end_time)
        self.assertTrue(slot.is_active)

    def test_timetable_slot_str_representation(self):
        """Test string representation of timetable slot"""
        slot = TimetableSlotFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            day_of_week=0,  # Monday
            start_time=time(9, 0),
            end_time=time(10, 0)
        )
        
        expected_str = f"{self.course_section} - Monday 09:00:00-10:00:00"
        self.assertEqual(str(slot), expected_str)

    def test_timetable_slot_day_choices(self):
        """Test all valid day of week choices"""
        valid_days = [0, 1, 2, 3, 4, 5, 6]  # Monday to Sunday
        
        for day in valid_days:
            slot = TimetableSlotFactory(
                course_section=self.course_section,
                faculty=self.faculty,
                day_of_week=day
            )
            self.assertEqual(slot.day_of_week, day)


class TestAcademicCalendarHolidayModel(TestCase):
    """Test cases for AcademicCalendarHoliday model"""

    def test_holiday_creation(self):
        """Test basic holiday creation"""
        holiday = AcademicCalendarHolidayFactory()
        
        self.assertIsNotNone(holiday.id)
        self.assertIsNotNone(holiday.name)
        self.assertIsNotNone(holiday.date)
        self.assertTrue(holiday.is_full_day)

    def test_holiday_str_representation(self):
        """Test string representation of holiday"""
        holiday = AcademicCalendarHolidayFactory(
            name="Independence Day",
            date=date(2024, 8, 15)
        )
        
        expected_str = "Independence Day - 2024-08-15"
        self.assertEqual(str(holiday), expected_str)

    def test_holiday_unique_constraint(self):
        """Test unique constraint on name and date"""
        holiday1 = AcademicCalendarHolidayFactory(
            name="Test Holiday",
            date=date(2024, 8, 15)
        )
        
        # Creating another holiday with same name and date should fail
        with self.assertRaises(IntegrityError):
            AcademicCalendarHoliday.objects.create(
                name="Test Holiday",
                date=date(2024, 8, 15),
                is_full_day=True
            )


class TestAttendanceConfigurationModel(TestCase):
    """Test cases for AttendanceConfiguration model"""

    def test_configuration_creation(self):
        """Test basic configuration creation"""
        config = AttendanceConfigurationFactory()
        
        self.assertIsNotNone(config.id)
        self.assertIsNotNone(config.key)
        self.assertIsNotNone(config.value)
        self.assertEqual(config.data_type, 'string')
        self.assertTrue(config.is_active)

    def test_configuration_str_representation(self):
        """Test string representation of configuration"""
        config = AttendanceConfigurationFactory(
            key="TEST_KEY",
            value="test_value"
        )
        
        expected_str = "TEST_KEY = test_value"
        self.assertEqual(str(config), expected_str)

    def test_configuration_get_typed_value(self):
        """Test get_typed_value method"""
        # Test string type
        string_config = AttendanceConfigurationFactory(
            key="string_key",
            value="test",
            data_type="string"
        )
        self.assertEqual(string_config.get_typed_value(), "test")
        
        # Test integer type
        int_config = AttendanceConfigurationFactory(
            key="int_key",
            value="123",
            data_type="integer"
        )
        self.assertEqual(int_config.get_typed_value(), 123)
        
        # Test float type
        float_config = AttendanceConfigurationFactory(
            key="float_key",
            value="123.45",
            data_type="float"
        )
        self.assertEqual(float_config.get_typed_value(), 123.45)
        
        # Test boolean type
        bool_config = AttendanceConfigurationFactory(
            key="bool_key",
            value="true",
            data_type="boolean"
        )
        self.assertTrue(bool_config.get_typed_value())


class TestStudentSnapshotModel(TestCase):
    """Test cases for StudentSnapshot model"""

    def setUp(self):
        """Set up test data"""
        self.session = AttendanceSessionFactory()
        self.student = StudentFactory()

    def test_student_snapshot_creation(self):
        """Test basic student snapshot creation"""
        snapshot = StudentSnapshotFactory(
            session=self.session,
            student=self.student
        )
        
        self.assertIsNotNone(snapshot.id)
        self.assertEqual(snapshot.session, self.session)
        self.assertEqual(snapshot.student, self.student)
        self.assertEqual(snapshot.course_section, self.session.course_section)
        self.assertEqual(snapshot.roll_number, self.student.roll_number)
        self.assertEqual(snapshot.full_name, self.student.full_name)

    def test_student_snapshot_str_representation(self):
        """Test string representation of student snapshot"""
        snapshot = StudentSnapshotFactory(
            session=self.session,
            student=self.student
        )
        
        expected_str = f"{self.student.roll_number} - {self.session}"
        self.assertEqual(str(snapshot), expected_str)

    def test_student_snapshot_unique_constraint(self):
        """Test unique constraint on session and student"""
        snapshot1 = StudentSnapshotFactory(
            session=self.session,
            student=self.student
        )
        
        # Creating another snapshot with same session and student should fail
        with self.assertRaises(IntegrityError):
            StudentSnapshot.objects.create(
                session=self.session,
                student=self.student,
                course_section=self.session.course_section,
                roll_number=self.student.roll_number,
                full_name=self.student.full_name
            )


class TestAttendanceHelperFunctions(TestCase):
    """Test cases for attendance helper functions"""

    def test_compute_attendance_percentage(self):
        """Test attendance percentage calculation"""
        # Test basic calculation
        percentage = compute_attendance_percentage(75, 100)
        self.assertEqual(percentage, 75.0)
        
        # Test with excused absences
        percentage = compute_attendance_percentage(75, 100, excused_count=10)
        self.assertEqual(percentage, 83.33)  # 75/90 * 100
        
        # Test with zero total sessions
        percentage = compute_attendance_percentage(0, 0)
        self.assertEqual(percentage, 0.0)
        
        # Test with excused not excluded from denominator
        percentage = compute_attendance_percentage(75, 100, excused_count=10, exclude_excused_from_denominator=False)
        self.assertEqual(percentage, 75.0)

    def test_get_attendance_settings(self):
        """Test getting attendance settings"""
        settings = get_attendance_settings()
        
        # Check that default settings are returned
        self.assertIn('GRACE_PERIOD_MINUTES', settings)
        self.assertIn('THRESHOLD_PERCENT', settings)
        self.assertIn('ALLOW_QR_SELF_MARK', settings)
        
        # Check default values
        self.assertEqual(settings['GRACE_PERIOD_MINUTES'], 5)
        self.assertEqual(settings['THRESHOLD_PERCENT'], 75)
        self.assertTrue(settings['ALLOW_QR_SELF_MARK'])

    def test_get_student_attendance_summary(self):
        """Test student attendance summary calculation"""
        student = StudentFactory()
        
        # Create some attendance records
        session1 = AttendanceSessionFactory()
        session2 = AttendanceSessionFactory()
        session3 = AttendanceSessionFactory()
        
        # Create records
        PresentAttendanceRecordFactory(session=session1, student=student)
        AbsentAttendanceRecordFactory(session=session2, student=student)
        AttendanceRecordFactory(session=session3, student=student, mark='late')
        
        # Get summary
        summary = get_student_attendance_summary(student)
        
        self.assertEqual(summary['total_sessions'], 3)
        self.assertEqual(summary['present'], 2)  # present + late
        self.assertEqual(summary['absent'], 1)
        self.assertEqual(summary['late'], 1)
        self.assertEqual(summary['excused'], 0)
        self.assertEqual(summary['percentage'], 66.67)  # 2/3 * 100
        self.assertFalse(summary['is_eligible_for_exam'])  # Below 75% threshold


@pytest.mark.django_db
class TestAttendanceModelPytest:
    """Pytest-style tests for attendance models"""

    def test_attendance_session_factory_creation(self):
        """Test attendance session factory creates valid instance"""
        session = AttendanceSessionFactory()
        
        assert session.id is not None
        assert session.course_section is not None
        assert session.faculty is not None
        assert session.scheduled_date is not None
        assert session.start_datetime is not None
        assert session.end_datetime is not None
        assert session.status in ['scheduled', 'open', 'closed', 'locked', 'cancelled']

    def test_attendance_record_factory_creation(self):
        """Test attendance record factory creates valid instance"""
        record = AttendanceRecordFactory()
        
        assert record.id is not None
        assert record.session is not None
        assert record.student is not None
        assert record.mark in ['present', 'absent', 'late', 'excused']
        assert record.source in ['manual', 'qr', 'biometric', 'rfid', 'offline', 'import', 'system']

    @pytest.mark.parametrize("mark", ['present', 'absent', 'late', 'excused'])
    def test_attendance_record_mark_choices(self, mark):
        """Test all valid attendance record mark choices"""
        record = AttendanceRecordFactory(mark=mark)
        assert record.mark == mark

    @pytest.mark.parametrize("source", ['manual', 'qr', 'biometric', 'rfid', 'offline', 'import', 'system'])
    def test_attendance_record_source_choices(self, source):
        """Test all valid attendance record source choices"""
        record = AttendanceRecordFactory(source=source)
        assert record.source == source

    def test_attendance_session_unique_constraint_pytest(self):
        """Test unique constraint using pytest"""
        session1 = AttendanceSessionFactory()
        
        with pytest.raises(IntegrityError):
            AttendanceSession.objects.create(
                course_section=session1.course_section,
                faculty=session1.faculty,
                timetable_slot=session1.timetable_slot,
                scheduled_date=session1.scheduled_date,
                start_datetime=timezone.now(),
                end_datetime=timezone.now() + timedelta(hours=1)
            )

    def test_attendance_record_unique_constraint_pytest(self):
        """Test unique constraint using pytest"""
        record1 = AttendanceRecordFactory()
        
        with pytest.raises(IntegrityError):
            AttendanceRecord.objects.create(
                session=record1.session,
                student=record1.student,
                mark='absent'
            )

    def test_qr_attendance_record(self):
        """Test QR attendance record factory"""
        record = QRAttendanceRecordFactory()
        
        assert record.mark == 'present'
        assert record.source == 'qr'

    def test_biometric_attendance_record(self):
        """Test biometric attendance record factory"""
        record = BiometricAttendanceRecordFactory()
        
        assert record.mark == 'present'
        assert record.source == 'biometric'
        assert record.vendor_event_id is not None

    def test_open_attendance_session(self):
        """Test open attendance session factory"""
        session = OpenAttendanceSessionFactory()
        
        assert session.status == 'open'
        assert session.auto_opened is True

    def test_closed_attendance_session(self):
        """Test closed attendance session factory"""
        session = ClosedAttendanceSessionFactory()
        
        assert session.status == 'closed'
        assert session.auto_closed is True

    def test_locked_attendance_session(self):
        """Test locked attendance session factory"""
        session = LockedAttendanceSessionFactory()
        
        assert session.status == 'locked'





