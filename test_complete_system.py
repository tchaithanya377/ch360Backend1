#!/usr/bin/env python
"""
Complete System Test for Integrated Academic System
Tests all components: models, admin, serializers, views, permissions, and URLs
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import Group, Permission

from attendance.models import (
    AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord,
    AttendanceConfiguration, AcademicCalendarHoliday
)
from students.models import AcademicYear, Semester
from academics.models import CourseSection
from faculty.models import Faculty
from accounts.models import User

User = get_user_model()


class IntegratedSystemTest(APITestCase):
    """Test the complete integrated academic system"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date='2024-09-01',
            end_date='2025-05-31',
            is_current=True,
            is_active=True
        )
        
        # Create semester
        self.semester = Semester.objects.create(
            academic_year=self.academic_year,
            semester_type='ODD',
            name='Fall 2024',
            start_date='2024-09-01',
            end_date='2024-12-31',
            is_current=True,
            is_active=True
        )
        
        # Create academic period
        self.academic_period = AcademicPeriod.objects.create(
            academic_year=self.academic_year,
            semester=self.semester,
            period_start='2024-09-01',
            period_end='2024-12-31',
            is_current=True,
            is_active=True,
            description='Fall 2024 Academic Period',
            created_by=self.admin_user
        )
        
        # Create faculty
        self.faculty = Faculty.objects.create(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            employee_id='FAC001'
        )
        
        # Create course section (simplified for testing)
        self.course_section = CourseSection.objects.create(
            course_id=1,  # Assuming course exists
            faculty=self.faculty,
            section_type='LECTURE',
            max_students=50
        )
        
        # Create timetable slot
        self.timetable_slot = TimetableSlot.objects.create(
            academic_period=self.academic_period,
            course_section=self.course_section,
            faculty=self.faculty,
            day_of_week=0,  # Monday
            start_time='09:00:00',
            end_time='10:00:00',
            room='A101',
            slot_type='LECTURE',
            is_active=True
        )
        
        # Create attendance session
        from datetime import date, time
        from django.utils import timezone
        
        self.attendance_session = AttendanceSession.objects.create(
            academic_period=self.academic_period,
            course_section=self.course_section,
            faculty=self.faculty,
            timetable_slot=self.timetable_slot,
            scheduled_date=date.today(),
            start_datetime=timezone.datetime.combine(date.today(), time(9, 0)),
            end_datetime=timezone.datetime.combine(date.today(), time(10, 0)),
            room='A101',
            status='scheduled'
        )
        
        # Create student (simplified for testing)
        from students.models import Student
        self.student = Student.objects.create(
            roll_number='STU001',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com'
        )
        
        # Create attendance record
        self.attendance_record = AttendanceRecord.objects.create(
            academic_period=self.academic_period,
            session=self.attendance_session,
            student=self.student,
            mark='present',
            source='manual',
            marked_by=self.user
        )
    
    def test_academic_period_model(self):
        """Test AcademicPeriod model functionality"""
        print("Testing AcademicPeriod Model...")
        
        # Test properties
        self.assertEqual(self.academic_period.display_name, "Fall 2024 2024-2025")
        self.assertTrue(self.academic_period.is_ongoing)
        self.assertEqual(self.academic_period.get_duration_days(), 122)
        
        # Test class methods
        current_period = AcademicPeriod.get_current_period()
        self.assertEqual(current_period, self.academic_period)
        
        from datetime import date
        period_by_date = AcademicPeriod.get_period_by_date(date(2024, 10, 15))
        self.assertEqual(period_by_date, self.academic_period)
        
        print("✅ AcademicPeriod model tests passed")
    
    def test_timetable_slot_model(self):
        """Test TimetableSlot model functionality"""
        print("Testing TimetableSlot Model...")
        
        # Test properties
        self.assertEqual(self.timetable_slot.academic_year_display, "2024-2025")
        self.assertEqual(self.timetable_slot.semester_display, "Fall 2024")
        self.assertEqual(self.timetable_slot.duration_minutes, 60)
        self.assertTrue(self.timetable_slot.can_generate_sessions())
        
        print("✅ TimetableSlot model tests passed")
    
    def test_attendance_session_model(self):
        """Test AttendanceSession model functionality"""
        print("Testing AttendanceSession Model...")
        
        # Test properties
        self.assertEqual(self.attendance_session.academic_year_display, "2024-2025")
        self.assertEqual(self.attendance_session.semester_display, "Fall 2024")
        self.assertEqual(self.attendance_session.duration_minutes, 60)
        
        print("✅ AttendanceSession model tests passed")
    
    def test_attendance_record_model(self):
        """Test AttendanceRecord model functionality"""
        print("Testing AttendanceRecord Model...")
        
        # Test properties
        self.assertEqual(self.attendance_record.academic_year_display, "2024-2025")
        self.assertEqual(self.attendance_record.semester_display, "Fall 2024")
        self.assertTrue(self.attendance_record.is_present)
        self.assertFalse(self.attendance_record.is_late)
        
        print("✅ AttendanceRecord model tests passed")
    
    def test_academic_period_api(self):
        """Test AcademicPeriod API endpoints"""
        print("Testing AcademicPeriod API...")
        
        # Test list endpoint
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/attendance/api/academic-periods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test current endpoint
        response = self.client.get('/api/v1/attendance/api/academic-periods/current/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.academic_period.id))
        
        # Test by-date endpoint
        response = self.client.get('/api/v1/attendance/api/academic-periods/by-date/?date=2024-10-15')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.academic_period.id))
        
        print("✅ AcademicPeriod API tests passed")
    
    def test_timetable_slot_api(self):
        """Test TimetableSlot API endpoints"""
        print("Testing TimetableSlot API...")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/attendance/api/timetable-slots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filtering by academic period
        response = self.client.get(f'/api/v1/attendance/api/timetable-slots/?academic_period={self.academic_period.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        print("✅ TimetableSlot API tests passed")
    
    def test_attendance_session_api(self):
        """Test AttendanceSession API endpoints"""
        print("Testing AttendanceSession API...")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/attendance/api/sessions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filtering by academic period
        response = self.client.get(f'/api/v1/attendance/api/sessions/?academic_period={self.academic_period.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        print("✅ AttendanceSession API tests passed")
    
    def test_attendance_record_api(self):
        """Test AttendanceRecord API endpoints"""
        print("Testing AttendanceRecord API...")
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/attendance/api/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test filtering by academic period
        response = self.client.get(f'/api/v1/attendance/api/records/?academic_period={self.academic_period.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        print("✅ AttendanceRecord API tests passed")
    
    def test_permissions(self):
        """Test role-based permissions"""
        print("Testing Permissions...")
        
        # Test unauthenticated access
        response = self.client.get('/api/v1/attendance/api/academic-periods/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test authenticated access
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/attendance/api/academic-periods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test admin access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/attendance/api/academic-periods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        print("✅ Permissions tests passed")
    
    def test_serializers(self):
        """Test serializers functionality"""
        print("Testing Serializers...")
        
        from attendance.serializers import (
            AcademicPeriodSerializer, TimetableSlotSerializer,
            AttendanceSessionListSerializer, AttendanceRecordSerializer
        )
        
        # Test AcademicPeriod serializer
        serializer = AcademicPeriodSerializer(self.academic_period)
        data = serializer.data
        self.assertEqual(data['academic_year_display'], '2024-2025')
        self.assertEqual(data['semester_display'], 'Fall 2024')
        self.assertEqual(data['duration_days'], 122)
        self.assertTrue(data['is_ongoing'])
        
        # Test TimetableSlot serializer
        serializer = TimetableSlotSerializer(self.timetable_slot)
        data = serializer.data
        self.assertEqual(data['academic_period_display'], 'Fall 2024 2024-2025')
        self.assertEqual(data['academic_year_display'], '2024-2025')
        self.assertEqual(data['semester_display'], 'Fall 2024')
        self.assertTrue(data['can_generate_sessions'])
        
        # Test AttendanceSession serializer
        serializer = AttendanceSessionListSerializer(self.attendance_session)
        data = serializer.data
        self.assertEqual(data['academic_period_display'], 'Fall 2024 2024-2025')
        self.assertEqual(data['academic_year_display'], '2024-2025')
        self.assertEqual(data['semester_display'], 'Fall 2024')
        
        # Test AttendanceRecord serializer
        serializer = AttendanceRecordSerializer(self.attendance_record)
        data = serializer.data
        self.assertEqual(data['academic_period_display'], 'Fall 2024 2024-2025')
        self.assertEqual(data['academic_year_display'], '2024-2025')
        self.assertEqual(data['semester_display'], 'Fall 2024')
        self.assertTrue(data['is_present'])
        
        print("✅ Serializers tests passed")
    
    def test_admin_interface(self):
        """Test Django admin interface"""
        print("Testing Admin Interface...")
        
        # Test admin login
        admin_client = Client()
        admin_client.force_login(self.admin_user)
        
        # Test AcademicPeriod admin
        response = admin_client.get('/admin/attendance/academicperiod/')
        self.assertEqual(response.status_code, 200)
        
        # Test TimetableSlot admin
        response = admin_client.get('/admin/attendance/timetableslot/')
        self.assertEqual(response.status_code, 200)
        
        # Test AttendanceSession admin
        response = admin_client.get('/admin/attendance/attendancesession/')
        self.assertEqual(response.status_code, 200)
        
        # Test AttendanceRecord admin
        response = admin_client.get('/admin/attendance/attendancerecord/')
        self.assertEqual(response.status_code, 200)
        
        print("✅ Admin interface tests passed")
    
    def test_data_consistency(self):
        """Test data consistency across models"""
        print("Testing Data Consistency...")
        
        # Test that academic period is consistent across all models
        self.assertEqual(self.timetable_slot.academic_period, self.academic_period)
        self.assertEqual(self.attendance_session.academic_period, self.academic_period)
        self.assertEqual(self.attendance_record.academic_period, self.academic_period)
        
        # Test that academic year and semester are consistent
        self.assertEqual(self.timetable_slot.academic_year_display, "2024-2025")
        self.assertEqual(self.attendance_session.academic_year_display, "2024-2025")
        self.assertEqual(self.attendance_record.academic_year_display, "2024-2025")
        
        self.assertEqual(self.timetable_slot.semester_display, "Fall 2024")
        self.assertEqual(self.attendance_session.semester_display, "Fall 2024")
        self.assertEqual(self.attendance_record.semester_display, "Fall 2024")
        
        print("✅ Data consistency tests passed")
    
    def test_auto_population(self):
        """Test auto-population of academic period"""
        print("Testing Auto-Population...")
        
        # Create new attendance session without academic_period
        from datetime import date, time
        from django.utils import timezone
        
        new_session = AttendanceSession.objects.create(
            timetable_slot=self.timetable_slot,
            scheduled_date=date.today(),
            start_datetime=timezone.datetime.combine(date.today(), time(11, 0)),
            end_datetime=timezone.datetime.combine(date.today(), time(12, 0)),
            room='A102',
            status='scheduled'
        )
        
        # Academic period should be auto-populated
        self.assertEqual(new_session.academic_period, self.academic_period)
        
        # Create new attendance record without academic_period
        new_record = AttendanceRecord.objects.create(
            session=new_session,
            student=self.student,
            mark='absent',
            source='manual',
            marked_by=self.user
        )
        
        # Academic period should be auto-populated
        self.assertEqual(new_record.academic_period, self.academic_period)
        
        print("✅ Auto-population tests passed")
    
    def run_all_tests(self):
        """Run all tests"""
        print("="*60)
        print("🧪 RUNNING COMPLETE INTEGRATED SYSTEM TESTS")
        print("="*60)
        
        try:
            self.test_academic_period_model()
            self.test_timetable_slot_model()
            self.test_attendance_session_model()
            self.test_attendance_record_model()
            self.test_academic_period_api()
            self.test_timetable_slot_api()
            self.test_attendance_session_api()
            self.test_attendance_record_api()
            self.test_permissions()
            self.test_serializers()
            self.test_admin_interface()
            self.test_data_consistency()
            self.test_auto_population()
            
            print("\n" + "="*60)
            print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
            print("="*60)
            print("\n✅ Integrated Academic System is working perfectly!")
            print("✅ All models, APIs, permissions, and admin interfaces are functional")
            print("✅ Data consistency and auto-population are working correctly")
            print("✅ The system is ready for production use!")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()


def test_system_manually():
    """Manual test function for quick verification"""
    print("🔍 Manual System Verification...")
    
    # Test model imports
    try:
        from attendance.models import AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord
        print("✅ Model imports successful")
    except ImportError as e:
        print(f"❌ Model import failed: {e}")
        return
    
    # Test serializer imports
    try:
        from attendance.serializers import AcademicPeriodSerializer, TimetableSlotSerializer
        print("✅ Serializer imports successful")
    except ImportError as e:
        print(f"❌ Serializer import failed: {e}")
        return
    
    # Test view imports
    try:
        from attendance.views import AcademicPeriodViewSet, TimetableSlotViewSet
        print("✅ View imports successful")
    except ImportError as e:
        print(f"❌ View import failed: {e}")
        return
    
    # Test permission imports
    try:
        from attendance.permissions import AcademicPeriodPermissions, TimetableSlotPermissions
        print("✅ Permission imports successful")
    except ImportError as e:
        print(f"❌ Permission import failed: {e}")
        return
    
    # Test URL imports
    try:
        from attendance.urls import urlpatterns
        print("✅ URL imports successful")
    except ImportError as e:
        print(f"❌ URL import failed: {e}")
        return
    
    print("✅ All imports successful - System is ready!")


if __name__ == '__main__':
    print("🚀 Starting Integrated Academic System Tests...")
    
    # Run manual verification first
    test_system_manually()
    
    print("\n" + "="*60)
    print("🧪 Running Comprehensive Test Suite...")
    print("="*60)
    
    # Run comprehensive tests
    test_suite = IntegratedSystemTest()
    test_suite.setUp()
    test_suite.run_all_tests()
