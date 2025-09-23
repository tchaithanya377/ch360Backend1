"""
Tests for attendance Django admin.
"""

from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from attendance.admin import (
    AcademicPeriodAdmin, AttendanceSessionAdmin, AttendanceRecordAdmin,
    LeaveApplicationAdmin, AttendanceCorrectionRequestAdmin
)
from attendance.models import (
    AcademicPeriod, AttendanceSession, AttendanceRecord,
    LeaveApplication, AttendanceCorrectionRequest
)
from attendance.tests.factories import (
    AcademicPeriodFactory, AttendanceSessionFactory, AttendanceRecordFactory,
    LeaveApplicationFactory, AttendanceCorrectionRequestFactory,
    AdminUserFactory
)

User = get_user_model()


class MockRequest:
    def __init__(self, user):
        self.user = user


class TestAcademicPeriodAdmin(TestCase):
    """Test cases for AcademicPeriodAdmin"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AcademicPeriodAdmin(AcademicPeriod, self.site)
        self.user = AdminUserFactory()
        self.request = MockRequest(self.user)
        self.period = AcademicPeriodFactory()

    def test_admin_registration(self):
        """Test that AcademicPeriod is registered in admin"""
        from django.contrib import admin
        self.assertIn(AcademicPeriod, admin.site._registry)

    def test_list_display(self):
        """Test admin list display fields"""
        expected_fields = ['display_name', 'academic_year', 'semester', 'period_start', 'period_end', 'is_current', 'is_active']
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_search_fields(self):
        """Test admin search fields"""
        expected_fields = ['academic_year__year', 'semester__name', 'description']
        for field in expected_fields:
            self.assertIn(field, self.admin.search_fields)


class TestAttendanceSessionAdmin(TestCase):
    """Test cases for AttendanceSessionAdmin"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AttendanceSessionAdmin(AttendanceSession, self.site)
        self.user = AdminUserFactory()
        self.request = MockRequest(self.user)
        self.session = AttendanceSessionFactory()

    def test_admin_registration(self):
        """Test that AttendanceSession is registered in admin"""
        from django.contrib import admin
        self.assertIn(AttendanceSession, admin.site._registry)

    def test_list_display(self):
        """Test admin list display fields"""
        expected_fields = ['course_section', 'academic_period', 'scheduled_date', 'start_datetime', 'end_datetime', 'room', 'status', 'faculty']
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        """Test admin list filter fields"""
        self.assertIn('status', self.admin.list_filter)

    def test_date_hierarchy(self):
        """Test admin date hierarchy"""
        self.assertEqual(self.admin.date_hierarchy, 'scheduled_date')


class TestAttendanceRecordAdmin(TestCase):
    """Test cases for AttendanceRecordAdmin"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AttendanceRecordAdmin(AttendanceRecord, self.site)
        self.user = AdminUserFactory()
        self.request = MockRequest(self.user)
        self.record = AttendanceRecordFactory()

    def test_admin_registration(self):
        """Test that AttendanceRecord is registered in admin"""
        from django.contrib import admin
        self.assertIn(AttendanceRecord, admin.site._registry)

    def test_list_display(self):
        """Test admin list display fields"""
        expected_fields = ['session', 'student', 'academic_period', 'mark', 'marked_at', 'source', 'device_type', 'sync_status']
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        """Test admin list filter fields"""
        expected_fields = ['academic_period', 'mark', 'source', 'device_type', 'sync_status', 'session__scheduled_date', 'marked_at']
        for field in expected_fields:
            self.assertIn(field, self.admin.list_filter)


class TestLeaveApplicationAdmin(TestCase):
    """Test cases for LeaveApplicationAdmin"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = LeaveApplicationAdmin(LeaveApplication, self.site)
        self.user = AdminUserFactory()
        self.request = MockRequest(self.user)
        self.leave = LeaveApplicationFactory()

    def test_admin_registration(self):
        """Test that LeaveApplication is registered in admin"""
        from django.contrib import admin
        self.assertIn(LeaveApplication, admin.site._registry)

    def test_list_display(self):
        """Test admin list display fields"""
        expected_fields = ['student', 'start_date', 'end_date', 'status']
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        """Test admin list filter fields"""
        self.assertIn('status', self.admin.list_filter)


class TestAttendanceCorrectionRequestAdmin(TestCase):
    """Test cases for AttendanceCorrectionRequestAdmin"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AttendanceCorrectionRequestAdmin(AttendanceCorrectionRequest, self.site)
        self.user = AdminUserFactory()
        self.request = MockRequest(self.user)
        self.correction = AttendanceCorrectionRequestFactory()

    def test_admin_registration(self):
        """Test that AttendanceCorrectionRequest is registered in admin"""
        from django.contrib import admin
        self.assertIn(AttendanceCorrectionRequest, admin.site._registry)

    def test_list_display(self):
        """Test admin list display fields"""
        expected_fields = ['student', 'session', 'status']
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter(self):
        """Test admin list filter fields"""
        self.assertIn('status', self.admin.list_filter)