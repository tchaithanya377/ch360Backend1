"""
Tests for attendance utility functions.
"""

from decimal import Decimal
from django.test import TestCase
from attendance.models import compute_attendance_percentage, get_attendance_settings
from attendance.tests.factories import (
    StudentFactory, AttendanceSessionFactory, AttendanceConfigurationFactory,
    PresentAttendanceRecordFactory, AbsentAttendanceRecordFactory, CourseSectionFactory
)


class TestComputeAttendancePercentage(TestCase):
    """Test cases for compute_attendance_percentage utility function"""

    def setUp(self):
        self.student = StudentFactory()
        self.course_section = CourseSectionFactory()
        self.session1 = AttendanceSessionFactory(status='closed', course_section=self.course_section)
        self.session2 = AttendanceSessionFactory(status='closed', course_section=self.course_section)

    def test_compute_attendance_percentage_all_present(self):
        """Test attendance percentage calculation with all present records"""
        PresentAttendanceRecordFactory(student=self.student, session=self.session1)
        PresentAttendanceRecordFactory(student=self.student, session=self.session2)
        
        percentage = compute_attendance_percentage(2, 2, 0)  # 2 present out of 2 total
        self.assertEqual(percentage, Decimal('100.00'))

    def test_compute_attendance_percentage_all_absent(self):
        """Test attendance percentage calculation with all absent records"""
        AbsentAttendanceRecordFactory(student=self.student, session=self.session1)
        AbsentAttendanceRecordFactory(student=self.student, session=self.session2)
        
        percentage = compute_attendance_percentage(0, 2, 0)  # 0 present out of 2 total
        self.assertEqual(percentage, Decimal('0.00'))

    def test_compute_attendance_percentage_no_records(self):
        """Test attendance percentage calculation with no records"""
        percentage = compute_attendance_percentage(0, 0, 0)  # No records
        self.assertEqual(percentage, Decimal('0.00'))


class TestGetAttendanceSettings(TestCase):
    """Test cases for get_attendance_settings utility function"""

    def setUp(self):
        self.config = AttendanceConfigurationFactory()

    def test_get_attendance_settings_success(self):
        """Test successful retrieval of attendance settings"""
        settings = get_attendance_settings()
        self.assertIsNotNone(settings)
        self.assertIsInstance(settings, dict)
        self.assertIn('GRACE_PERIOD_MINUTES', settings)

    def test_get_attendance_settings_no_config(self):
        """Test get_attendance_settings when no configuration exists"""
        from attendance.models import AttendanceConfiguration
        AttendanceConfiguration.objects.all().delete()

        settings = get_attendance_settings()
        self.assertIsInstance(settings, dict)
        self.assertIn('GRACE_PERIOD_MINUTES', settings)
        self.assertEqual(settings['GRACE_PERIOD_MINUTES'], 5)