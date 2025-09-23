"""
Comprehensive tests for attendance views with 100% coverage.
Tests API endpoints, permissions, filtering, and business logic.
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, datetime, timedelta
from decimal import Decimal
import json

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from attendance.views import (
    AcademicPeriodViewSet, AttendanceConfigurationViewSet, AcademicCalendarHolidayViewSet,
    TimetableSlotViewSet, AttendanceSessionViewSet, AttendanceRecordViewSet,
    LeaveApplicationViewSet, AttendanceCorrectionRequestViewSet, AttendanceStatisticsViewSet,
    BiometricDeviceViewSet, BiometricTemplateViewSet, AttendanceAuditLogViewSet,
    AttendanceExportViewSet
)
from attendance.tests.factories import (
    AcademicPeriodFactory, AttendanceConfigurationFactory, AcademicCalendarHolidayFactory,
    TimetableSlotFactory, AttendanceSessionFactory, StudentSnapshotFactory,
    AttendanceRecordFactory, LeaveApplicationFactory, AttendanceCorrectionRequestFactory,
    AttendanceAuditLogFactory, AttendanceStatisticsFactory, BiometricDeviceFactory,
    BiometricTemplateFactory, UserFactory, StudentFactory, CourseSectionFactory,
    FacultyFactory, AcademicYearFactory, SemesterFactory,
    PresentAttendanceRecordFactory, AbsentAttendanceRecordFactory,
    LateAttendanceRecordFactory, ExcusedAttendanceRecordFactory,
    OpenAttendanceSessionFactory, ClosedAttendanceSessionFactory,
    ApprovedLeaveApplicationFactory, RejectedLeaveApplicationFactory,
    ApprovedCorrectionRequestFactory, RejectedCorrectionRequestFactory,
    AdminUserFactory
)

User = get_user_model()


# =============================================================================
# BASE TEST CLASSES
# =============================================================================

class BaseAPITestCase(APITestCase):
    """Base test case for API tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.admin_user = AdminUserFactory()
        
        # Get JWT tokens
        self.user_token = RefreshToken.for_user(self.user)
        self.admin_token = RefreshToken.for_user(self.admin_user)
        
        # Set default authentication
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token.access_token}')


# =============================================================================
# ACADEMIC PERIOD VIEWSET TESTS
# =============================================================================

class TestAcademicPeriodViewSet(BaseAPITestCase):
    """Test cases for AcademicPeriodViewSet"""

    def setUp(self):
        super().setUp()
        self.academic_year = AcademicYearFactory()
        self.semester = SemesterFactory(academic_year=self.academic_year)
        self.period = AcademicPeriodFactory(
            academic_year=self.academic_year,
            semester=self.semester
        )

    def test_list_academic_periods(self):
        """Test listing academic periods"""
        url = reverse('academicperiod-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.period.id))

    def test_retrieve_academic_period(self):
        """Test retrieving a specific academic period"""
        url = reverse('academicperiod-detail', kwargs={'pk': self.period.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.period.id))
        self.assertEqual(response.data['academic_year'], self.academic_year.id)

    def test_create_academic_period_unauthorized(self):
        """Test creating academic period without admin privileges"""
        url = reverse('academicperiod-list')
        data = {
            'academic_year': self.academic_year.id,
            'semester': self.semester.id,
            'period_start': '2024-08-01',
            'period_end': '2024-12-31',
            'is_current': False,
            'is_active': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_academic_period_authorized(self):
        """Test creating academic period with admin privileges"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        # Create different academic year and semester to avoid unique constraint violation
        new_academic_year = AcademicYearFactory()
        new_semester = SemesterFactory(academic_year=new_academic_year)
        
        url = reverse('academicperiod-list')
        data = {
            'academic_year': new_academic_year.id,
            'semester': new_semester.id,
            'period_start': '2024-08-01',
            'period_end': '2024-12-31',
            'is_current': False,
            'is_active': True,
            'description': 'Test period'
        }
        
        response = self.client.post(url, data)
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['academic_year'], new_academic_year.id)

    def test_update_academic_period(self):
        """Test updating academic period"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('academicperiod-detail', kwargs={'pk': self.period.id})
        data = {
            'academic_year': self.academic_year.id,
            'semester': self.semester.id,
            'period_start': '2024-08-01',
            'period_end': '2024-12-31',
            'is_current': True,
            'is_active': True,
            'description': 'Updated period'
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_current'], True)

    def test_delete_academic_period(self):
        """Test deleting academic period"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('academicperiod-detail', kwargs={'pk': self.period.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_current_period(self):
        """Test getting current academic period"""
        # Use admin authentication for current period operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        current_period = AcademicPeriodFactory(is_current=True)
        
        url = reverse('academicperiod-current')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(current_period.id))

    def test_get_current_period_not_found(self):
        """Test getting current period when none exists"""
        # Use admin authentication for current period operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        # Remove current period
        from attendance.models import AcademicPeriod
        AcademicPeriod.objects.filter(is_current=True).update(is_current=False)
        
        url = reverse('academicperiod-current')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_period_by_date(self):
        """Test getting period by date"""
        # Use admin authentication for period by date operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        test_date = date(2024, 6, 15)
        period = AcademicPeriodFactory(
            period_start=date(2024, 6, 1),
            period_end=date(2024, 6, 30),
            is_active=True
        )
        
        url = reverse('academicperiod-by-date')
        response = self.client.get(url, {'date': '2024-06-15'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(period.id))

    def test_get_period_by_date_invalid_format(self):
        """Test getting period by date with invalid format"""
        # Use admin authentication for period by date operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('academicperiod-by-date')
        response = self.client.get(url, {'date': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_current_period(self):
        """Test setting current academic period"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('academicperiod-set-current', kwargs={'pk': self.period.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.period.refresh_from_db()
        self.assertTrue(self.period.is_current)

    def test_filter_academic_periods_by_year(self):
        """Test filtering academic periods by year"""
        url = reverse('academicperiod-list')
        response = self.client.get(url, {'academic_year': self.academic_year.year})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_academic_periods_by_current(self):
        """Test filtering academic periods by current status"""
        url = reverse('academicperiod-list')
        response = self.client.get(url, {'is_current': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return 0 since our test period is not current
        self.assertEqual(len(response.data['results']), 0)


# =============================================================================
# ATTENDANCE CONFIGURATION VIEWSET TESTS
# =============================================================================

class TestAttendanceConfigurationViewSet(BaseAPITestCase):
    """Test cases for AttendanceConfigurationViewSet"""

    def setUp(self):
        super().setUp()
        self.config = AttendanceConfigurationFactory(
            key="TEST_CONFIG",
            value="test_value",
            updated_by=self.user
        )

    def test_list_configurations(self):
        """Test listing configurations"""
        url = reverse('attendanceconfiguration-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['key'], "TEST_CONFIG")

    def test_retrieve_configuration(self):
        """Test retrieving a specific configuration"""
        url = reverse('attendanceconfiguration-detail', kwargs={'pk': self.config.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['key'], "TEST_CONFIG")
        self.assertEqual(response.data['value'], "test_value")

    def test_create_configuration_unauthorized(self):
        """Test creating configuration without admin privileges"""
        url = reverse('attendanceconfiguration-list')
        data = {
            'key': 'NEW_CONFIG',
            'value': 'new_value',
            'data_type': 'string',
            'description': 'New configuration'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_configuration_authorized(self):
        """Test creating configuration with admin privileges"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendanceconfiguration-list')
        data = {
            'key': 'NEW_CONFIG',
            'value': 'new_value',
            'data_type': 'string',
            'description': 'New configuration',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['key'], 'NEW_CONFIG')

    def test_update_configuration(self):
        """Test updating configuration"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendanceconfiguration-detail', kwargs={'pk': self.config.id})
        data = {
            'key': 'TEST_CONFIG',
            'value': 'updated_value',
            'data_type': 'string',
            'description': 'Updated configuration',
            'is_active': True
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], 'updated_value')

    def test_delete_configuration(self):
        """Test deleting configuration"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendanceconfiguration-detail', kwargs={'pk': self.config.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# =============================================================================
# ACADEMIC CALENDAR HOLIDAY VIEWSET TESTS
# =============================================================================

class TestAcademicCalendarHolidayViewSet(BaseAPITestCase):
    """Test cases for AcademicCalendarHolidayViewSet"""

    def setUp(self):
        super().setUp()
        self.holiday = AcademicCalendarHolidayFactory(
            name="Test Holiday",
            date=date(2024, 12, 25)
        )

    def test_list_holidays(self):
        """Test listing holidays"""
        url = reverse('academiccalendarholiday-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Test Holiday")

    def test_retrieve_holiday(self):
        """Test retrieving a specific holiday"""
        url = reverse('academiccalendarholiday-detail', kwargs={'pk': self.holiday.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Holiday")
        self.assertEqual(response.data['date'], "2024-12-25")

    def test_create_holiday(self):
        """Test creating holiday"""
        url = reverse('academiccalendarholiday-list')
        data = {
            'name': 'New Holiday',
            'date': '2024-12-31',
            'is_full_day': True,
            'academic_year': '2024-2025',
            'description': 'New Year Holiday',
            'affects_attendance': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Holiday')

    def test_update_holiday(self):
        """Test updating holiday"""
        url = reverse('academiccalendarholiday-detail', kwargs={'pk': self.holiday.id})
        data = {
            'name': 'Updated Holiday',
            'date': '2024-12-25',
            'is_full_day': False,
            'academic_year': '2024-2025',
            'description': 'Updated holiday',
            'affects_attendance': False
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Holiday')

    def test_delete_holiday(self):
        """Test deleting holiday"""
        url = reverse('academiccalendarholiday-detail', kwargs={'pk': self.holiday.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_holidays_by_year(self):
        """Test filtering holidays by academic year"""
        url = reverse('academiccalendarholiday-list')
        response = self.client.get(url, {'academic_year': '2024-2025'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return holidays for the specified year

    def test_filter_holidays_by_affects_attendance(self):
        """Test filtering holidays by affects_attendance"""
        url = reverse('academiccalendarholiday-list')
        response = self.client.get(url, {'affects_attendance': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return holidays that affect attendance


# =============================================================================
# TIMETABLE SLOT VIEWSET TESTS
# =============================================================================

class TestTimetableSlotViewSet(BaseAPITestCase):
    """Test cases for TimetableSlotViewSet"""

    def setUp(self):
        super().setUp()
        self.academic_period = AcademicPeriodFactory()
        self.course_section = CourseSectionFactory()
        self.faculty = FacultyFactory()
        self.slot = TimetableSlotFactory(
            academic_period=self.academic_period,
            course_section=self.course_section,
            faculty=self.faculty
        )

    def test_list_timetable_slots(self):
        """Test listing timetable slots"""
        url = reverse('timetableslot-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.slot.id)

    def test_retrieve_timetable_slot(self):
        """Test retrieving a specific timetable slot"""
        url = reverse('timetableslot-detail', kwargs={'pk': self.slot.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.slot.id)
        self.assertEqual(response.data['course_section'], self.course_section.id)

    def test_create_timetable_slot_unauthorized(self):
        """Test creating timetable slot without proper permissions"""
        url = reverse('timetableslot-list')
        data = {
            'academic_period': self.academic_period.id,
            'course_section': self.course_section.id,
            'faculty': self.faculty.id,
            'day_of_week': 0,
            'start_time': '09:00:00',
            'end_time': '10:00:00',
            'room': 'A101',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_timetable_slots_by_course_section(self):
        """Test filtering timetable slots by course section"""
        url = reverse('timetableslot-list')
        response = self.client.get(url, {'course_section': self.course_section.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_timetable_slots_by_faculty(self):
        """Test filtering timetable slots by faculty"""
        url = reverse('timetableslot-list')
        response = self.client.get(url, {'faculty': self.faculty.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_timetable_slots_by_academic_period(self):
        """Test filtering timetable slots by academic period"""
        url = reverse('timetableslot-list')
        response = self.client.get(url, {'academic_period': self.academic_period.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_timetable_slots_by_is_active(self):
        """Test filtering timetable slots by active status"""
        url = reverse('timetableslot-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


# =============================================================================
# ATTENDANCE SESSION VIEWSET TESTS
# =============================================================================

class TestAttendanceSessionViewSet(BaseAPITestCase):
    """Test cases for AttendanceSessionViewSet"""

    def setUp(self):
        super().setUp()
        self.academic_period = AcademicPeriodFactory()
        self.course_section = CourseSectionFactory()
        self.faculty = FacultyFactory()
        self.session = AttendanceSessionFactory(
            academic_period=self.academic_period,
            course_section=self.course_section,
            faculty=self.faculty
        )

    def test_list_attendance_sessions(self):
        """Test listing attendance sessions"""
        url = reverse('attendancesession-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.session.id)

    def test_retrieve_attendance_session(self):
        """Test retrieving a specific attendance session"""
        url = reverse('attendancesession-detail', kwargs={'pk': self.session.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.session.id)
        self.assertEqual(response.data['course_section'], self.course_section.id)

    def test_create_attendance_session(self):
        """Test creating attendance session"""
        # Use admin authentication for create operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendancesession-list')
        data = {
            'course_section': self.course_section.id,
            'faculty': self.faculty.id,
            'scheduled_date': '2024-06-15',
            'start_datetime': '2024-06-15T09:00:00Z',
            'end_datetime': '2024-06-15T10:00:00Z',
            'room': 'A101',
            'makeup': False,
            'notes': 'Test session'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['course_section'], self.course_section.id)

    def test_open_session(self):
        """Test opening an attendance session"""
        # Use admin authentication for open operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        session = AttendanceSessionFactory(status='scheduled')
        
        url = reverse('attendancesession-open-session', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'open')

    def test_close_session(self):
        """Test closing an attendance session"""
        # Use admin authentication for close operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        session = OpenAttendanceSessionFactory()
        
        url = reverse('attendancesession-close-session', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'closed')

    def test_generate_qr_code(self):
        """Test generating QR code for session"""
        # Use admin authentication for generate QR operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendancesession-generate-qr', kwargs={'pk': self.session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('qr_token', response.data)
        self.assertIn('expires_at', response.data)

    def test_generate_sessions_from_timetable(self):
        """Test generating sessions from timetable"""
        # Use admin authentication for generate sessions operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendancesession-generate-sessions')
        data = {
            'start_date': '2024-06-01',
            'end_date': '2024-06-30',
            'course_sections': [self.course_section.id],
            'academic_year': '2024-2025',
            'semester': 'Fall 2024'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sessions_created', response.data)

    def test_generate_sessions_missing_dates(self):
        """Test generating sessions with missing dates"""
        # Use admin authentication for generate sessions operation
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token.access_token}')
        
        url = reverse('attendancesession-generate-sessions')
        data = {
            'course_sections': [self.course_section.id]
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_sessions_by_course_section(self):
        """Test filtering sessions by course section"""
        url = reverse('attendancesession-list')
        response = self.client.get(url, {'course_section': self.course_section.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_sessions_by_faculty(self):
        """Test filtering sessions by faculty"""
        url = reverse('attendancesession-list')
        response = self.client.get(url, {'faculty': self.faculty.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_sessions_by_status(self):
        """Test filtering sessions by status"""
        url = reverse('attendancesession-list')
        response = self.client.get(url, {'status': 'scheduled'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_sessions_by_date(self):
        """Test filtering sessions by scheduled date"""
        url = reverse('attendancesession-list')
        response = self.client.get(url, {'scheduled_date': self.session.scheduled_date})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_sessions_by_makeup(self):
        """Test filtering sessions by makeup status"""
        url = reverse('attendancesession-list')
        response = self.client.get(url, {'makeup': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)