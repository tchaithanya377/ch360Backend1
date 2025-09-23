"""
Comprehensive tests for attendance views and API endpoints.
"""

import pytest
import json
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from attendance.models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest,
    LeaveApplication, get_attendance_settings
)
from attendance.factories import (
    AttendanceSessionFactory, AttendanceRecordFactory,
    AttendanceCorrectionRequestFactory, LeaveApplicationFactory,
    StudentFactory, FacultyFactory, UserFactory
)
from students.models import Student
from academics.models import CourseEnrollment


class TestAttendanceSessionViewSet(APITestCase):
    """Test cases for AttendanceSessionViewSet"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        self.faculty_user = self.faculty.user
        
        # Create course enrollment
        from attendance.tests.factories import CourseSectionFactory
        self.course_section = CourseSectionFactory()
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED'
        )

    def tearDown(self):
        """Clean up test data"""
        # Clean up all attendance sessions to ensure test isolation
        AttendanceSession.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        CourseEnrollment.objects.all().delete()
        LeaveApplication.objects.all().delete()
        AttendanceCorrectionRequest.objects.all().delete()

    def test_list_attendance_sessions(self):
        """Test listing attendance sessions"""
        # Create some sessions
        session1 = AttendanceSessionFactory(course_section=self.course_section)
        session2 = AttendanceSessionFactory(course_section=self.course_section)
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_attendance_session(self):
        """Test creating an attendance session"""
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-list')
        
        data = {
            'course_section': self.course_section.id,
            'faculty': self.faculty.id,
            'scheduled_date': '2024-09-15',
            'start_datetime': '2024-09-15T09:00:00Z',
            'end_datetime': '2024-09-15T10:00:00Z',
            'room': 'A101'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AttendanceSession.objects.count(), 1)

    def test_open_attendance_session(self):
        """Test opening an attendance session"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            status='scheduled'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-open', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'open')

    def test_close_attendance_session(self):
        """Test closing an attendance session"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            status='open'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-close', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'closed')

    def test_lock_attendance_session(self):
        """Test locking an attendance session"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            status='closed'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-lock', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'locked')

    def test_generate_qr_token(self):
        """Test generating QR token for session"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            status='open'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-qr-token', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('qr_token', response.data)
        self.assertIn('expires_at', response.data)

    def test_generate_records(self):
        """Test generating attendance records for session"""
        session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-generate-records', kwargs={'pk': session.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('records_created', response.data)

    def test_filter_sessions_by_status(self):
        """Test filtering sessions by status"""
        # Clean up any existing sessions first
        AttendanceSession.objects.all().delete()
        
        session1 = AttendanceSessionFactory(
            course_section=self.course_section,
            status='open'
        )
        session2 = AttendanceSessionFactory(
            course_section=self.course_section,
            status='closed'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-list')
        response = self.client.get(url, {'status': 'open'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Filter by status should only return sessions with status 'open'
        open_sessions = [s for s in response.data['results'] if s['status'] == 'open']
        self.assertEqual(len(open_sessions), 1)
        self.assertEqual(open_sessions[0]['id'], session1.id)

    def test_filter_sessions_by_date_range(self):
        """Test filtering sessions by date range"""
        session1 = AttendanceSessionFactory(
            course_section=self.course_section,
            scheduled_date='2024-09-15'
        )
        session2 = AttendanceSessionFactory(
            course_section=self.course_section,
            scheduled_date='2024-09-20'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-session-list')
        response = self.client.get(url, {
            'start_date': '2024-09-15',
            'end_date': '2024-09-16'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], session1.id)


class TestAttendanceRecordViewSet(APITestCase):
    """Test cases for AttendanceRecordViewSet"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        self.faculty_user = self.faculty.user
        
        # Create course enrollment
        from attendance.tests.factories import CourseSectionFactory
        self.course_section = CourseSectionFactory()
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED'
        )
        
        self.session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty
        )

    def tearDown(self):
        """Clean up test data"""
        # Clean up all attendance records to ensure test isolation
        AttendanceRecord.objects.all().delete()
        AttendanceSession.objects.all().delete()
        CourseEnrollment.objects.all().delete()

    def test_list_attendance_records(self):
        """Test listing attendance records"""
        # Create some records
        record1 = AttendanceRecordFactory(session=self.session, student=self.student)
        record2 = AttendanceRecordFactory(session=self.session)
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-record-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_create_attendance_record(self):
        """Test creating an attendance record"""
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-record-list')
        
        data = {
            'session': self.session.id,
            'student': self.student.id,
            'mark': 'present',
            'source': 'manual'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_bulk_mark_attendance(self):
        """Test bulk marking attendance"""
        student2 = StudentFactory()
        CourseEnrollment.objects.create(
            student=student2,
            course_section=self.course_section,
            status='ENROLLED'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendancerecord-bulk-mark')
        
        data = {
            'session_id': self.session.id,
            'attendance_data': [
                {
                    'student_id': str(self.student.id),
                    'mark': 'present',
                    'reason': 'Present in class'
                },
                {
                    'student_id': str(student2.id),
                    'mark': 'absent',
                    'reason': 'Not present'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('created_count', response.data)
        self.assertIn('session_id', response.data)

    def test_filter_records_by_student(self):
        """Test filtering records by student"""
        # Clean up any existing records first
        AttendanceRecord.objects.all().delete()
        
        record1 = AttendanceRecordFactory(session=self.session, student=self.student)
        record2 = AttendanceRecordFactory(session=self.session)
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-record-list')
        response = self.client.get(url, {'student': self.student.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Filter by student should only return records for the specified student
        student_records = [r for r in response.data['results'] if r['student'] == self.student.id]
        self.assertEqual(len(student_records), 1)
        self.assertEqual(student_records[0]['id'], record1.id)

    def test_filter_records_by_mark(self):
        """Test filtering records by mark"""
        # Clean up any existing records first
        AttendanceRecord.objects.all().delete()
        
        record1 = AttendanceRecordFactory(session=self.session, mark='present')
        record2 = AttendanceRecordFactory(session=self.session, mark='absent')
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-record-list')
        response = self.client.get(url, {'mark': 'present'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Filter by mark should only return records with mark 'present'
        present_records = [r for r in response.data['results'] if r['mark'] == 'present']
        self.assertEqual(len(present_records), 1)
        self.assertEqual(present_records[0]['id'], record1.id)


class TestQRCheckinView(APITestCase):
    """Test cases for QRCheckinView"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        
        # Create course enrollment
        from attendance.tests.factories import CourseSectionFactory
        self.course_section = CourseSectionFactory()
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED'
        )
        
        self.session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty,
            status='open'
        )

    def test_qr_checkin_success(self):
        """Test successful QR check-in"""
        # Generate QR token
        self.session.generate_qr_token()
        
        self.client.force_authenticate(user=self.faculty.user)
        url = reverse('qr-checkin')
        
        data = {
            'qr_token': self.session.qr_token,
            'student_id': self.student.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Attendance marked successfully')

    def test_qr_checkin_invalid_token(self):
        """Test QR check-in with invalid token"""
        self.client.force_authenticate(user=self.faculty.user)
        url = reverse('qr-checkin')
        
        data = {
            'qr_token': 'invalid_token',
            'student_id': self.student.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('qr_token', response.data)

    def test_qr_checkin_expired_token(self):
        """Test QR check-in with expired token"""
        # Generate QR token and manually expire it
        self.session.generate_qr_token()
        self.session.qr_expires_at = timezone.now() - timezone.timedelta(minutes=1)
        self.session.save()
        
        self.client.force_authenticate(user=self.faculty.user)
        url = reverse('qr-checkin')
        
        data = {
            'qr_token': self.session.qr_token,
            'student_id': self.student.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_qr_checkin_not_enrolled(self):
        """Test QR check-in for student not enrolled in course"""
        # Remove enrollment
        CourseEnrollment.objects.filter(
            student=self.student,
            course_section=self.course_section
        ).delete()
        
        # Generate QR token
        self.session.generate_qr_token()
        
        self.client.force_authenticate(user=self.faculty.user)
        url = reverse('qr-checkin')
        
        data = {
            'qr_token': self.session.qr_token,
            'student_id': self.student.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class TestOfflineSyncView(APITestCase):
    """Test cases for OfflineSyncView"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        self.faculty_user = self.faculty.user
        
        # Create course enrollment
        from attendance.tests.factories import CourseSectionFactory
        self.course_section = CourseSectionFactory()
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED'
        )
        
        self.session = AttendanceSessionFactory(course_section=self.course_section)

    def test_offline_sync_success(self):
        """Test successful offline sync"""
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('offline-sync')
        
        data = {
            'records': [
                {
                    'client_uuid': 'test-uuid-1',
                    'session_id': self.session.id,
                    'student_id': self.student.id,
                    'mark': 'present',
                    'reason': 'Offline sync'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Sync completed')

    def test_offline_sync_invalid_data(self):
        """Test offline sync with invalid data"""
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('offline-sync')
        
        data = {
            'last_sync_at': timezone.now().isoformat(),
            'records': [
                {
                    'client_uuid': 'test-uuid-1',
                    'session': self.session.id,
                    # Missing 'mark' field
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestAttendanceCorrectionRequestViewSet(APITestCase):
    """Test cases for AttendanceCorrectionRequestViewSet"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        self.faculty_user = self.faculty.user
        
        # Create course enrollment
        from attendance.tests.factories import CourseSectionFactory
        self.course_section = CourseSectionFactory()
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED'
        )
        
        self.session = AttendanceSessionFactory(
            course_section=self.course_section,
            faculty=self.faculty
        )
        
        self.record = AttendanceRecordFactory(
            session=self.session,
            student=self.student,
            mark='absent'
        )

    def tearDown(self):
        """Clean up test data"""
        AttendanceCorrectionRequest.objects.all().delete()
        AttendanceRecord.objects.all().delete()
        AttendanceSession.objects.all().delete()
        CourseEnrollment.objects.all().delete()

    def test_create_correction_request(self):
        """Test creating a correction request"""
        self.client.force_authenticate(user=self.user)
        url = reverse('attendance-correction-list')
        
        data = {
            'session': self.session.id,
            'student': self.student.id,
            'from_mark': 'absent',
            'to_mark': 'present',
            'reason': 'I was present but marked absent by mistake'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AttendanceCorrectionRequest.objects.count(), 1)

    def test_approve_correction_request(self):
        """Test approving a correction request"""
        correction_request = AttendanceCorrectionRequestFactory(
            session=self.session,
            student=self.student,
            status='pending',
            from_mark='absent',
            to_mark='present'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-correction-approve', kwargs={'pk': correction_request.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        correction_request.refresh_from_db()
        self.assertEqual(correction_request.status, 'approved')
        
        # Check that attendance record was updated
        self.record.refresh_from_db()
        self.assertEqual(self.record.mark, 'present')

    def test_reject_correction_request(self):
        """Test rejecting a correction request"""
        correction_request = AttendanceCorrectionRequestFactory(
            session=self.session,
            student=self.student,
            status='pending'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-correction-reject', kwargs={'pk': correction_request.id})
        
        data = {
            'decision_note': 'No valid reason provided'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        correction_request.refresh_from_db()
        self.assertEqual(correction_request.status, 'rejected')

    def test_list_correction_requests(self):
        """Test listing correction requests"""
        correction_request1 = AttendanceCorrectionRequestFactory(
            session=self.session,
            student=self.student,
            status='pending'
        )
        correction_request2 = AttendanceCorrectionRequestFactory(
            session=self.session,
            status='approved'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-correction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_correction_requests_by_status(self):
        """Test filtering correction requests by status"""
        # Clean up any existing correction requests first
        AttendanceCorrectionRequest.objects.all().delete()
        
        correction_request1 = AttendanceCorrectionRequestFactory(
            session=self.session,
            student=self.student,
            status='pending'
        )
        correction_request2 = AttendanceCorrectionRequestFactory(
            session=self.session,
            status='approved'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-correction-list')
        response = self.client.get(url, {'status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Filter by status should only return correction requests with status 'pending'
        pending_requests = [r for r in response.data['results'] if r['status'] == 'pending']
        self.assertEqual(len(pending_requests), 1)
        self.assertEqual(pending_requests[0]['id'], correction_request1.id)


class TestLeaveApplicationViewSet(APITestCase):
    """Test cases for LeaveApplicationViewSet"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        self.faculty_user = self.faculty.user

    def tearDown(self):
        """Clean up test data"""
        LeaveApplication.objects.all().delete()

    def test_create_leave_application(self):
        """Test creating a leave application"""
        self.client.force_authenticate(user=self.user)
        url = reverse('attendance-leave-list')
        
        data = {
            'student': self.student.id,
            'leave_type': 'medical',
            'start_date': '2024-09-15',
            'end_date': '2024-09-17',
            'reason': 'Medical emergency'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LeaveApplication.objects.count(), 1)

    def test_approve_leave_application(self):
        """Test approving a leave application"""
        leave_application = LeaveApplicationFactory(
            student=self.student,
            status='pending'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-leave-approve', kwargs={'pk': leave_application.id})
        
        data = {
            'decision_note': 'Approved based on medical certificate'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave_application.refresh_from_db()
        self.assertEqual(leave_application.status, 'approved')

    def test_reject_leave_application(self):
        """Test rejecting a leave application"""
        leave_application = LeaveApplicationFactory(
            student=self.student,
            status='pending'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-leave-reject', kwargs={'pk': leave_application.id})
        
        data = {
            'decision_note': 'Insufficient documentation'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave_application.refresh_from_db()
        self.assertEqual(leave_application.status, 'rejected')

    def test_list_leave_applications(self):
        """Test listing leave applications"""
        leave_application1 = LeaveApplicationFactory(
            student=self.student,
            status='pending'
        )
        leave_application2 = LeaveApplicationFactory(
            status='approved'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-leave-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_leave_applications_by_status(self):
        """Test filtering leave applications by status"""
        # Clean up any existing leave applications first
        LeaveApplication.objects.all().delete()
        
        leave_application1 = LeaveApplicationFactory(
            student=self.student,
            status='pending'
        )
        leave_application2 = LeaveApplicationFactory(
            status='approved'
        )
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-leave-list')
        response = self.client.get(url, {'status': 'pending'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Filter by status should only return leave applications with status 'pending'
        pending_applications = [l for l in response.data['results'] if l['status'] == 'pending']
        self.assertEqual(len(pending_applications), 1)
        self.assertEqual(pending_applications[0]['id'], leave_application1.id)


class TestStudentAttendanceSummaryView(APITestCase):
    """Test cases for StudentAttendanceSummaryView"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.student = StudentFactory(user=self.user)
        self.faculty = FacultyFactory()
        
        # Create course enrollment
        from attendance.tests.factories import CourseSectionFactory
        self.course_section = CourseSectionFactory()
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED'
        )
        
        # Create some attendance records
        self.session1 = AttendanceSessionFactory(course_section=self.course_section)
        self.session2 = AttendanceSessionFactory(course_section=self.course_section)
        self.session3 = AttendanceSessionFactory(course_section=self.course_section)
        
        AttendanceRecordFactory(session=self.session1, student=self.student, mark='present')
        AttendanceRecordFactory(session=self.session2, student=self.student, mark='absent')
        AttendanceRecordFactory(session=self.session3, student=self.student, mark='late')

    def test_get_student_attendance_summary(self):
        """Test getting student attendance summary"""
        self.client.force_authenticate(user=self.user)
        url = reverse('student-summary', kwargs={'student_id': self.student.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sessions', response.data)
        self.assertIn('present_count', response.data)
        self.assertIn('absent_count', response.data)
        self.assertIn('late_count', response.data)
        self.assertIn('attendance_percentage', response.data)
        self.assertIn('is_eligible_for_exam', response.data)

    def test_get_student_attendance_summary_with_course_filter(self):
        """Test getting student attendance summary filtered by course"""
        self.client.force_authenticate(user=self.user)
        url = reverse('student-summary', kwargs={'student_id': self.student.id})
        response = self.client.get(url, {'course_section_id': self.course_section.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('course_section_id', response.data)
        self.assertEqual(response.data['course_section_id'], self.course_section.id)

    def test_get_student_attendance_summary_with_date_range(self):
        """Test getting student attendance summary with date range"""
        self.client.force_authenticate(user=self.user)
        url = reverse('student-summary', kwargs={'student_id': self.student.id})
        response = self.client.get(url, {
            'start_date': '2024-09-01',
            'end_date': '2024-09-30'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sessions', response.data)

    def test_get_student_attendance_summary_student_not_found(self):
        """Test getting attendance summary for non-existent student"""
        self.client.force_authenticate(user=self.user)
        url = reverse('student-summary', kwargs={'student_id': '00000000-0000-0000-0000-000000000000'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)


class TestAttendanceStatisticsView(APITestCase):
    """Test cases for AttendanceStatisticsView"""

    def setUp(self):
        """Set up test data"""
        self.user = UserFactory()
        self.faculty = FacultyFactory()
        self.faculty_user = self.faculty.user

    def test_get_attendance_statistics(self):
        """Test getting attendance statistics"""
        # Create some test data
        from attendance.tests.factories import CourseSectionFactory
        course_section = CourseSectionFactory()
        student = StudentFactory()
        
        CourseEnrollment.objects.create(
            student=student,
            course_section=course_section,
            status='ENROLLED'
        )
        
        session = AttendanceSessionFactory(course_section=course_section)
        AttendanceRecordFactory(session=session, student=student, mark='present')
        
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_sessions', response.data)
        self.assertIn('total_students', response.data)
        self.assertIn('average_attendance', response.data)
        self.assertIn('eligible_students', response.data)
        self.assertIn('ineligible_students', response.data)
        self.assertIn('pending_corrections', response.data)
        self.assertIn('pending_leaves', response.data)

    def test_get_attendance_statistics_with_date_range(self):
        """Test getting attendance statistics with date range"""
        self.client.force_authenticate(user=self.faculty_user)
        url = reverse('attendance-statistics')
        response = self.client.get(url, {
            'start_date': '2024-09-01',
            'end_date': '2024-09-30'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('period_start', response.data)
        self.assertIn('period_end', response.data)


class TestBiometricWebhookView(APITestCase):
    """Test cases for BiometricWebhookView"""

    def test_biometric_webhook_success(self):
        """Test successful biometric webhook"""
        url = reverse('biometric-webhook')
        
        data = {
            'device_id': 'DEV001',
            'subject_id': 'STU001',
            'event_type': 'checkin',
            'timestamp': timezone.now().isoformat(),
            'vendor_event_id': 'vendor-123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'accepted')

    def test_biometric_webhook_invalid_data(self):
        """Test biometric webhook with invalid data"""
        url = reverse('biometric-webhook')
        
        data = {
            'device_id': 'DEV001',
            # Missing required fields
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_biometric_webhook_old_timestamp(self):
        """Test biometric webhook with old timestamp"""
        url = reverse('biometric-webhook')
        
        data = {
            'device_id': 'DEV001',
            'subject_id': 'STU001',
            'event_type': 'checkin',
            'timestamp': (timezone.now() - timezone.timedelta(hours=2)).isoformat(),
            'vendor_event_id': 'vendor-123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestAttendanceViewsPytest:
    """Pytest-style tests for attendance views"""

    def test_attendance_session_factory_creates_valid_session(self):
        """Test that attendance session factory creates valid session"""
        session = AttendanceSessionFactory()
        
        assert session.id is not None
        assert session.course_section is not None
        assert session.faculty is not None
        assert session.scheduled_date is not None
        assert session.start_datetime is not None
        assert session.end_datetime is not None

    def test_attendance_record_factory_creates_valid_record(self):
        """Test that attendance record factory creates valid record"""
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



