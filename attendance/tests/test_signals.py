"""
Tests for attendance signals.
"""

from django.test import TestCase
from attendance.models import AttendanceRecord, AttendanceAuditLog
from attendance.tests.factories import (
    AttendanceSessionFactory, StudentFactory, AttendanceRecordFactory,
    LeaveApplicationFactory, AttendanceCorrectionRequestFactory,
    CourseSectionFactory
)


class TestAttendanceSignals(TestCase):
    """Test cases for attendance signals"""

    def test_create_attendance_records_for_session(self):
        """Test that attendance records are created when session is created"""
        course_section = CourseSectionFactory()
        students = [StudentFactory(student_batch=course_section.student_batch) for _ in range(3)]
        
        session = AttendanceSessionFactory(course_section=course_section)
        
        records = AttendanceRecord.objects.filter(session=session)
        self.assertEqual(records.count(), 3)
        
        for record in records:
            self.assertEqual(record.mark, 'absent')
            self.assertIn(record.student, students)

    def test_log_attendance_record_change(self):
        """Test that attendance record changes are logged"""
        record = AttendanceRecordFactory(mark='absent')
        
        record.mark = 'present'
        record.save()
        
        audit_logs = AttendanceAuditLog.objects.filter(
            entity_type='AttendanceRecord',
            entity_id=str(record.id)
        )
        self.assertEqual(audit_logs.count(), 1)
        
        audit_log = audit_logs.first()
        self.assertEqual(audit_log.action, 'update')

    def test_log_leave_application_change(self):
        """Test that leave application changes are logged"""
        leave = LeaveApplicationFactory(status='pending')
        
        leave.status = 'approved'
        leave.save()
        
        audit_logs = AttendanceAuditLog.objects.filter(
            entity_type='LeaveApplication',
            entity_id=str(leave.id)
        )
        self.assertEqual(audit_logs.count(), 1)

    def test_log_correction_request_change(self):
        """Test that correction request changes are logged"""
        correction = AttendanceCorrectionRequestFactory(status='pending')
        
        correction.status = 'approved'
        correction.save()
        
        audit_logs = AttendanceAuditLog.objects.filter(
            entity_type='AttendanceCorrectionRequest',
            entity_id=str(correction.id)
        )
        self.assertEqual(audit_logs.count(), 1)

    def test_attendance_record_deletion_logging(self):
        """Test that attendance record deletion is logged"""
        record = AttendanceRecordFactory()
        record_id = record.id
        
        record.delete()
        
        audit_logs = AttendanceAuditLog.objects.filter(
            entity_type='AttendanceRecord',
            entity_id=str(record_id),
            action='delete'
        )
        self.assertEqual(audit_logs.count(), 1)

    def test_session_status_change_logging(self):
        """Test that session status changes are logged"""
        session = AttendanceSessionFactory(status='scheduled')
        
        session.status = 'open'
        session.save()
        
        audit_logs = AttendanceAuditLog.objects.filter(
            entity_type='AttendanceSession',
            entity_id=str(session.id)
        )
        self.assertGreater(audit_logs.count(), 0)