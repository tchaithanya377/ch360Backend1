"""
Enhanced Attendance Celery Tasks for CampsHub360
Background tasks for attendance system automation
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Avg, F
from datetime import datetime, timedelta, date
import logging

from .models import (
    AttendanceConfiguration,
    TimetableSlot,
    AttendanceSession,
    AttendanceRecord,
    AttendanceStatistics,
    AttendanceAuditLog,
    get_attendance_settings,
    generate_sessions_from_timetable,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def auto_open_sessions(self):
    """
    Automatically open attendance sessions based on timetable.
    Runs every minute to check for sessions that should be opened.
    """
    try:
        settings_dict = get_attendance_settings()
        if not settings_dict.get('AUTO_OPEN_SESSIONS', True):
            logger.info("Auto-open sessions is disabled")
            return
        
        now = timezone.now()
        grace_minutes = settings_dict.get('GRACE_PERIOD_MINUTES', 5)
        
        # Find sessions that should be opened (scheduled and within grace period)
        sessions_to_open = AttendanceSession.objects.filter(
            status='scheduled',
            start_datetime__lte=now + timedelta(minutes=grace_minutes),
            start_datetime__gte=now - timedelta(minutes=grace_minutes)
        )
        
        opened_count = 0
        for session in sessions_to_open:
            try:
                with transaction.atomic():
                    session.open_session()
                    session.auto_opened = True
                    session.save(update_fields=['auto_opened'])
                    opened_count += 1
                    
                    # Log the action
                    AttendanceAuditLog.objects.create(
                        entity_type="AttendanceSession",
                        entity_id=str(session.id),
                        action="auto_open",
                        performed_by=None,
                        after={"status": "open", "auto_opened": True},
                        reason="Automatically opened based on schedule"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to auto-open session {session.id}: {str(e)}")
                continue
        
        logger.info(f"Auto-opened {opened_count} attendance sessions")
        return f"Opened {opened_count} sessions"
        
    except Exception as exc:
        logger.error(f"Auto-open sessions task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def auto_close_sessions(self):
    """
    Automatically close attendance sessions that have ended.
    Runs every minute to check for sessions that should be closed.
    """
    try:
        settings_dict = get_attendance_settings()
        if not settings_dict.get('AUTO_CLOSE_SESSIONS', True):
            logger.info("Auto-close sessions is disabled")
            return
        
        now = timezone.now()
        grace_minutes = settings_dict.get('GRACE_PERIOD_MINUTES', 5)
        
        # Find sessions that should be closed (open and past end time + grace period)
        sessions_to_close = AttendanceSession.objects.filter(
            status='open',
            end_datetime__lt=now - timedelta(minutes=grace_minutes)
        )
        
        closed_count = 0
        for session in sessions_to_close:
            try:
                with transaction.atomic():
                    session.close_session()
                    session.auto_closed = True
                    session.save(update_fields=['auto_closed'])
                    closed_count += 1
                    
                    # Auto-mark absent students if enabled
                    if settings_dict.get('AUTO_MARK_ABSENT', True):
                        _auto_mark_absent_students(session)
                    
                    # Log the action
                    AttendanceAuditLog.objects.create(
                        entity_type="AttendanceSession",
                        entity_id=str(session.id),
                        action="auto_close",
                        performed_by=None,
                        after={"status": "closed", "auto_closed": True},
                        reason="Automatically closed after session ended"
                    )
                    
            except Exception as e:
                logger.error(f"Failed to auto-close session {session.id}: {str(e)}")
                continue
        
        logger.info(f"Auto-closed {closed_count} attendance sessions")
        return f"Closed {closed_count} sessions"
        
    except Exception as exc:
        logger.error(f"Auto-close sessions task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


def _auto_mark_absent_students(session):
    """Helper function to auto-mark absent students"""
    # Get enrolled students who don't have attendance records
    enrolled_students = session.course_section.enrollments.filter(
        status='ENROLLED'
    ).select_related('student')
    
    existing_records = set(
        session.records.values_list('student_id', flat=True)
    )
    
    absent_records = []
    for enrollment in enrolled_students:
        if enrollment.student.id not in existing_records:
            absent_records.append(
                AttendanceRecord(
                    session=session,
                    student=enrollment.student,
                    mark='absent',
                    source='system',
                    reason='Auto-marked absent - no attendance recorded'
                )
            )
    
    if absent_records:
        AttendanceRecord.objects.bulk_create(absent_records)
        logger.info(f"Auto-marked {len(absent_records)} students as absent for session {session.id}")


@shared_task(bind=True, max_retries=3)
def generate_sessions_for_range(self, start_date=None, end_date=None, course_sections=None):
    """
    Generate attendance sessions for a date range.
    Can be called with specific parameters or use defaults.
    """
    try:
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=7)  # Generate for next week
        
        sessions_created = generate_sessions_from_timetable(
            start_date=start_date,
            end_date=end_date,
            course_sections=course_sections
        )
        
        logger.info(f"Generated {sessions_created} attendance sessions for {start_date} to {end_date}")
        return f"Generated {sessions_created} sessions"
        
    except Exception as exc:
        logger.error(f"Generate sessions task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def generate_daily_sessions(self):
    """
    Generate attendance sessions for the next day.
    Runs daily at midnight to prepare sessions for tomorrow.
    """
    try:
        tomorrow = date.today() + timedelta(days=1)
        sessions_created = generate_sessions_from_timetable(
            start_date=tomorrow,
            end_date=tomorrow
        )
        
        logger.info(f"Generated {sessions_created} attendance sessions for {tomorrow}")
        return f"Generated {sessions_created} sessions for {tomorrow}"
        
    except Exception as exc:
        logger.error(f"Generate daily sessions task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def calculate_attendance_statistics(self, student_id=None, course_section_id=None, 
                                  academic_year=None, semester=None):
    """
    Calculate and update attendance statistics for students.
    Can be run for specific students/courses or all.
    """
    try:
        settings_dict = get_attendance_settings()
        threshold_percent = settings_dict.get('THRESHOLD_PERCENT', 75)
        
        # Build query for attendance records
        records_query = AttendanceRecord.objects.select_related(
            'student', 'session', 'session__course_section'
        )
        
        if student_id:
            records_query = records_query.filter(student_id=student_id)
        if course_section_id:
            records_query = records_query.filter(session__course_section_id=course_section_id)
        if academic_year:
            records_query = records_query.filter(session__course_section__academic_year=academic_year)
        if semester:
            records_query = records_query.filter(session__course_section__semester=semester)
        
        # Group by student and course section
        stats_data = {}
        for record in records_query:
            key = (record.student.id, record.session.course_section.id)
            if key not in stats_data:
                stats_data[key] = {
                    'student': record.student,
                    'course_section': record.session.course_section,
                    'academic_year': record.session.course_section.academic_year,
                    'semester': record.session.course_section.semester,
                    'total_sessions': 0,
                    'present_count': 0,
                    'absent_count': 0,
                    'late_count': 0,
                    'excused_count': 0,
                    'period_start': None,
                    'period_end': None
                }
            
            stats = stats_data[key]
            stats['total_sessions'] += 1
            
            if record.mark == 'present':
                stats['present_count'] += 1
            elif record.mark == 'absent':
                stats['absent_count'] += 1
            elif record.mark == 'late':
                stats['late_count'] += 1
            elif record.mark == 'excused':
                stats['excused_count'] += 1
            
            # Track date range
            session_date = record.session.scheduled_date
            if stats['period_start'] is None or session_date < stats['period_start']:
                stats['period_start'] = session_date
            if stats['period_end'] is None or session_date > stats['period_end']:
                stats['period_end'] = session_date
        
        # Create or update statistics records
        updated_count = 0
        for (student_id, course_section_id), stats in stats_data.items():
            # Calculate attendance percentage
            effective_sessions = stats['total_sessions'] - stats['excused_count']
            if effective_sessions > 0:
                attendance_percentage = (stats['present_count'] / effective_sessions) * 100
            else:
                attendance_percentage = 100.0
            
            is_eligible = attendance_percentage >= threshold_percent
            
            # Create or update statistics record
            stats_obj, created = AttendanceStatistics.objects.update_or_create(
                student=stats['student'],
                course_section=stats['course_section'],
                academic_year=stats['academic_year'],
                semester=stats['semester'],
                period_start=stats['period_start'],
                period_end=stats['period_end'],
                defaults={
                    'total_sessions': stats['total_sessions'],
                    'present_count': stats['present_count'],
                    'absent_count': stats['absent_count'],
                    'late_count': stats['late_count'],
                    'excused_count': stats['excused_count'],
                    'attendance_percentage': round(attendance_percentage, 2),
                    'is_eligible_for_exam': is_eligible,
                }
            )
            updated_count += 1
        
        logger.info(f"Updated attendance statistics for {updated_count} student-course combinations")
        return f"Updated {updated_count} statistics records"
        
    except Exception as exc:
        logger.error(f"Calculate attendance statistics task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def cleanup_old_attendance_data(self):
    """
    Clean up old attendance data based on retention policy.
    Runs daily to remove data older than the retention period.
    """
    try:
        settings_dict = get_attendance_settings()
        retention_years = settings_dict.get('DATA_RETENTION_YEARS', 7)
        cutoff_date = date.today() - timedelta(days=retention_years * 365)
        
        # Clean up old audit logs (keep only 1 year)
        audit_cutoff = date.today() - timedelta(days=365)
        old_audit_logs = AttendanceAuditLog.objects.filter(
            created_at__date__lt=audit_cutoff
        )
        audit_deleted_count = old_audit_logs.count()
        old_audit_logs.delete()
        
        # Clean up old sessions and related data
        old_sessions = AttendanceSession.objects.filter(
            scheduled_date__lt=cutoff_date
        )
        session_deleted_count = old_sessions.count()
        
        # Delete related records first
        for session in old_sessions:
            session.records.all().delete()
            session.snapshots.all().delete()
            session.correction_requests.all().delete()
        
        old_sessions.delete()
        
        # Clean up old statistics
        old_stats = AttendanceStatistics.objects.filter(
            period_end__lt=cutoff_date
        )
        stats_deleted_count = old_stats.count()
        old_stats.delete()
        
        logger.info(f"Cleaned up {audit_deleted_count} audit logs, {session_deleted_count} sessions, {stats_deleted_count} statistics")
        return f"Cleaned up {audit_deleted_count} audit logs, {session_deleted_count} sessions, {stats_deleted_count} statistics"
        
    except Exception as exc:
        logger.error(f"Cleanup old attendance data task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=3600)


@shared_task(bind=True, max_retries=3)
def send_attendance_notifications(self):
    """
    Send attendance-related notifications to students and faculty.
    Runs daily to send low attendance warnings and other notifications.
    """
    try:
        settings_dict = get_attendance_settings()
        if not settings_dict.get('SEND_ATTENDANCE_NOTIFICATIONS', True):
            logger.info("Attendance notifications are disabled")
            return
        
        threshold_percent = settings_dict.get('THRESHOLD_PERCENT', 75)
        warning_threshold = threshold_percent - 10  # Send warning at 10% below threshold
        
        # Find students with low attendance
        low_attendance_students = AttendanceStatistics.objects.filter(
            attendance_percentage__lt=warning_threshold,
            attendance_percentage__gte=warning_threshold - 20,  # Only warn if not too low
            is_eligible_for_exam=False
        ).select_related('student', 'course_section')
        
        notification_count = 0
        for stats in low_attendance_students:
            try:
                # Send notification (placeholder - implement actual notification logic)
                _send_low_attendance_warning(stats.student, stats.course_section, stats.attendance_percentage)
                notification_count += 1
            except Exception as e:
                logger.error(f"Failed to send notification to student {stats.student.id}: {str(e)}")
                continue
        
        logger.info(f"Sent {notification_count} low attendance warnings")
        return f"Sent {notification_count} notifications"
        
    except Exception as exc:
        logger.error(f"Send attendance notifications task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=3600)


def _send_low_attendance_warning(student, course_section, attendance_percentage):
    """Helper function to send low attendance warning"""
    # Placeholder for actual notification implementation
    # This could send email, SMS, push notification, etc.
    logger.info(f"Low attendance warning for {student.roll_number}: {attendance_percentage}% in {course_section}")


@shared_task(bind=True, max_retries=3)
def sync_biometric_data(self, device_id=None):
    """
    Sync biometric attendance data from devices.
    Can be run for specific devices or all active devices.
    """
    try:
        from .models_enhanced import BiometricDevice
        
        if device_id:
            devices = BiometricDevice.objects.filter(id=device_id, is_enabled=True)
        else:
            devices = BiometricDevice.objects.filter(is_enabled=True, auto_sync=True)
        
        synced_count = 0
        for device in devices:
            try:
                # Placeholder for actual biometric sync logic
                # This would connect to the biometric device API and sync data
                _sync_device_data(device)
                synced_count += 1
            except Exception as e:
                logger.error(f"Failed to sync device {device.device_id}: {str(e)}")
                continue
        
        logger.info(f"Synced data from {synced_count} biometric devices")
        return f"Synced {synced_count} devices"
        
    except Exception as exc:
        logger.error(f"Sync biometric data task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


def _sync_device_data(device):
    """Helper function to sync data from a biometric device"""
    # Placeholder for actual device sync implementation
    # This would:
    # 1. Connect to device API
    # 2. Fetch attendance records
    # 3. Create AttendanceRecord objects
    # 4. Update device last_seen timestamp
    logger.info(f"Syncing data from device {device.device_id}")


@shared_task(bind=True, max_retries=3)
def generate_attendance_reports(self, report_type='daily', date_range=None):
    """
    Generate attendance reports for analysis.
    Can generate daily, weekly, monthly, or custom date range reports.
    """
    try:
        if not date_range:
            if report_type == 'daily':
                start_date = date.today()
                end_date = start_date
            elif report_type == 'weekly':
                start_date = date.today() - timedelta(days=7)
                end_date = date.today()
            elif report_type == 'monthly':
                start_date = date.today().replace(day=1)
                end_date = date.today()
            else:
                start_date = date.today() - timedelta(days=30)
                end_date = date.today()
        else:
            start_date = date_range['start_date']
            end_date = date_range['end_date']
        
        # Generate report data
        report_data = _generate_report_data(start_date, end_date)
        
        # Save report (placeholder - implement actual report generation)
        report_id = _save_report(report_data, report_type, start_date, end_date)
        
        logger.info(f"Generated {report_type} attendance report for {start_date} to {end_date}")
        return f"Generated report {report_id}"
        
    except Exception as exc:
        logger.error(f"Generate attendance reports task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


def _generate_report_data(start_date, end_date):
    """Helper function to generate report data"""
    # Placeholder for actual report generation
    # This would aggregate attendance data and create summary statistics
    return {
        'total_sessions': 0,
        'total_students': 0,
        'average_attendance': 0.0,
        'eligible_students': 0,
        'ineligible_students': 0
    }


def _save_report(report_data, report_type, start_date, end_date):
    """Helper function to save report"""
    # Placeholder for actual report saving
    # This would save the report to a file or database
    return f"report_{report_type}_{start_date}_{end_date}"


@shared_task(bind=True, max_retries=3)
def process_offline_attendance_sync(self, sync_data):
    """
    Process offline attendance data synchronization.
    Handles bulk upload of attendance data from offline devices.
    """
    try:
        synced_count = 0
        error_count = 0
        
        for record_data in sync_data:
            try:
                with transaction.atomic():
                    # Validate and create attendance record
                    record = AttendanceRecord.objects.create(
                        session_id=record_data['session_id'],
                        student_id=record_data['student_id'],
                        mark=record_data['mark'],
                        source='offline',
                        marked_at=record_data['marked_at'],
                        device_id=record_data.get('device_id', ''),
                        client_uuid=record_data.get('client_uuid', ''),
                        sync_status='synced'
                    )
                    synced_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to sync offline record: {str(e)}")
                error_count += 1
                continue
        
        logger.info(f"Synced {synced_count} offline records, {error_count} errors")
        return f"Synced {synced_count} records, {error_count} errors"
        
    except Exception as exc:
        logger.error(f"Process offline attendance sync task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3)
def validate_attendance_data_integrity(self):
    """
    Validate attendance data integrity and fix inconsistencies.
    Runs weekly to check for data integrity issues.
    """
    try:
        issues_found = 0
        issues_fixed = 0
        
        # Check for orphaned records
        orphaned_records = AttendanceRecord.objects.filter(
            session__isnull=True
        )
        orphaned_count = orphaned_records.count()
        if orphaned_count > 0:
            logger.warning(f"Found {orphaned_count} orphaned attendance records")
            issues_found += orphaned_count
        
        # Check for duplicate records
        duplicates = AttendanceRecord.objects.values('session', 'student').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        duplicate_count = duplicates.count()
        if duplicate_count > 0:
            logger.warning(f"Found {duplicate_count} duplicate attendance records")
            issues_found += duplicate_count
        
        # Check for invalid session statuses
        invalid_sessions = AttendanceSession.objects.filter(
            status='open',
            end_datetime__lt=timezone.now() - timedelta(hours=1)
        )
        invalid_count = invalid_sessions.count()
        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} sessions that should be closed")
            issues_found += invalid_count
            
            # Auto-close invalid sessions
            for session in invalid_sessions:
                try:
                    session.close_session()
                    session.auto_closed = True
                    session.save(update_fields=['auto_closed'])
                    issues_fixed += 1
                except Exception as e:
                    logger.error(f"Failed to close invalid session {session.id}: {str(e)}")
        
        logger.info(f"Data integrity check: {issues_found} issues found, {issues_fixed} fixed")
        return f"Found {issues_found} issues, fixed {issues_fixed}"
        
    except Exception as exc:
        logger.error(f"Validate attendance data integrity task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=3600)
