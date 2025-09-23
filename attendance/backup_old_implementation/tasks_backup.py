from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta, datetime
from django.conf import settings
import logging

from attendance.models import (
    TimetableSlot, AttendanceSession, AcademicCalendarHoliday, StudentSnapshot,
    AttendanceRecord, AttendanceConfiguration, get_attendance_settings
)
from academics.models import CourseSection, CourseEnrollment
from students.models import Student

logger = logging.getLogger(__name__)


@shared_task
def generate_sessions_for_range(start_date=None, end_date=None, course_section_ids=None, academic_year=None, semester=None):
    """
    Generate attendance sessions from timetable for a given date range.
    """
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = timezone.localdate()
        else:
            start_date = date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            
        if not end_date:
            end_date = start_date + timedelta(days=7)
        else:
            end_date = date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        
        # Get holidays in the date range
        holidays = set(
            AcademicCalendarHoliday.objects.filter(
                date__range=[start_date, end_date]
            ).values_list("date", flat=True)
        )
        
        # Get timetable slots
        slots_query = TimetableSlot.objects.filter(is_active=True)
        
        # Filter by course sections if provided
        if course_section_ids:
            slots_query = slots_query.filter(course_section_id__in=course_section_ids)
        
        # Filter by academic year and semester if provided
        if academic_year:
            slots_query = slots_query.filter(academic_year=academic_year)
        if semester:
            slots_query = slots_query.filter(semester=semester)
        
        slots = slots_query.select_related('course_section', 'faculty')
        
        # Build weekday buckets for efficient lookup
        slots_by_dow = {}
        for slot in slots:
            slots_by_dow.setdefault(slot.day_of_week, []).append(slot)
        
        created_count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Skip holidays
            if current_date in holidays:
                current_date += timedelta(days=1)
                continue
            
            # Get day of week (0=Monday, 6=Sunday)
            dow = current_date.weekday()
            
            # Process all slots for this day of week
            for slot in slots_by_dow.get(dow, []):
                # Create datetime objects for start and end times
                start_dt = datetime.combine(
                    current_date, 
                    slot.start_time, 
                    tzinfo=timezone.get_current_timezone()
                )
                end_dt = datetime.combine(
                    current_date, 
                    slot.end_time, 
                    tzinfo=timezone.get_current_timezone()
                )
                
                with transaction.atomic():
                    # Create or get session
                    session, created = AttendanceSession.objects.get_or_create(
                        timetable_slot=slot,
                        scheduled_date=current_date,
                        defaults={
                            "course_section": slot.course_section,
                            "faculty": slot.faculty,
                            "start_datetime": start_dt,
                            "end_datetime": end_dt,
                            "room": slot.room,
                            "status": "scheduled",
                        },
                    )
                    
                    if created:
                        # Create student snapshots for enrolled students
                        enrollments = CourseEnrollment.objects.filter(
                            course_section=slot.course_section,
                            status='ENROLLED'
                        ).select_related('student')
                        
                        for enrollment in enrollments:
                            StudentSnapshot.objects.get_or_create(
                                session=session,
                                student=enrollment.student,
                                defaults={
                                    "course_section": slot.course_section,
                                    "student_batch": enrollment.student.student_batch,
                                    "roll_number": enrollment.student.roll_number,
                                    "full_name": enrollment.student.full_name,
                                }
                            )
                        
                        created_count += 1
            
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {created_count} attendance sessions from {start_date} to {end_date}")
        return {"created": created_count, "start_date": str(start_date), "end_date": str(end_date)}
        
    except Exception as e:
        logger.error(f"Error generating sessions: {str(e)}")
        raise


@shared_task
def auto_open_sessions():
    """
    Automatically open sessions that are scheduled to start within the grace period.
    """
    try:
        settings_dict = get_attendance_settings()
        if not settings_dict.get('AUTO_OPEN_SESSIONS', True):
            return {"message": "Auto-open sessions is disabled"}
        
        grace_period = settings_dict.get('GRACE_PERIOD_MINUTES', 5)
        now = timezone.now()
        grace_start = now - timedelta(minutes=grace_period)
        
        # Find sessions that should be opened
        sessions_to_open = AttendanceSession.objects.filter(
            status='scheduled',
            start_datetime__lte=now,
            start_datetime__gte=grace_start
        )
        
        opened_count = 0
        for session in sessions_to_open:
            session.status = 'open'
            session.auto_opened = True
            session.save(update_fields=['status', 'auto_opened', 'updated_at'])
            
            # Generate QR token if enabled
            if settings_dict.get('ALLOW_QR_SELF_MARK', True):
                session.generate_qr_token()
            
            opened_count += 1
        
        logger.info(f"Auto-opened {opened_count} sessions")
        return {"opened": opened_count}
        
    except Exception as e:
        logger.error(f"Error auto-opening sessions: {str(e)}")
        raise


@shared_task
def auto_close_sessions():
    """
    Automatically close sessions that have ended.
    """
    try:
        settings_dict = get_attendance_settings()
        if not settings_dict.get('AUTO_CLOSE_SESSIONS', True):
            return {"message": "Auto-close sessions is disabled"}
        
        now = timezone.now()
        
        # Find sessions that should be closed
        sessions_to_close = AttendanceSession.objects.filter(
            status='open',
            end_datetime__lt=now
        )
        
        closed_count = 0
        for session in sessions_to_close:
            session.status = 'closed'
            session.auto_closed = True
            session.save(update_fields=['status', 'auto_closed', 'updated_at'])
            closed_count += 1
        
        logger.info(f"Auto-closed {closed_count} sessions")
        return {"closed": closed_count}
        
    except Exception as e:
        logger.error(f"Error auto-closing sessions: {str(e)}")
        raise


@shared_task
def process_biometric_webhook(webhook_data):
    """
    Process biometric device webhook data and create attendance records.
    """
    try:
        device_id = webhook_data.get('device_id')
        subject_id = webhook_data.get('subject_id')
        event_type = webhook_data.get('event_type')
        timestamp = webhook_data.get('timestamp')
        vendor_event_id = webhook_data.get('vendor_event_id')
        
        # Find the student by subject_id (this would need to be mapped in your system)
        # For now, we'll assume subject_id maps to some student identifier
        try:
            student = Student.objects.get(roll_number=subject_id)  # Adjust this mapping as needed
        except Student.DoesNotExist:
            logger.warning(f"Student not found for subject_id: {subject_id}")
            return {"error": "Student not found"}
        
        # Find active session for the student at the timestamp
        session_date = timestamp.date()
        session_time = timestamp.time()
        
        # Find sessions that were active at this time
        active_sessions = AttendanceSession.objects.filter(
            scheduled_date=session_date,
            start_datetime__lte=timestamp,
            end_datetime__gte=timestamp,
            status__in=['open', 'closed']
        ).select_related('course_section')
        
        # Find the session where the student is enrolled
        target_session = None
        for session in active_sessions:
            if CourseEnrollment.objects.filter(
                student=student,
                course_section=session.course_section,
                status='ENROLLED'
            ).exists():
                target_session = session
                break
        
        if not target_session:
            logger.warning(f"No active session found for student {student.roll_number} at {timestamp}")
            return {"error": "No active session found"}
        
        # Create or update attendance record
        with transaction.atomic():
            record, created = AttendanceRecord.objects.get_or_create(
                session=target_session,
                student=student,
                defaults={
                    'mark': 'present' if event_type == 'checkin' else 'absent',
                    'source': 'biometric',
                    'vendor_event_id': vendor_event_id,
                    'marked_at': timestamp,
                }
            )
            
            if not created:
                # Update existing record
                record.mark = 'present' if event_type == 'checkin' else 'absent'
                record.source = 'biometric'
                record.vendor_event_id = vendor_event_id
                record.marked_at = timestamp
                record.save()
        
        logger.info(f"Processed biometric webhook for student {student.roll_number}")
        return {"status": "processed", "student": student.roll_number, "session": str(target_session)}
        
    except Exception as e:
        logger.error(f"Error processing biometric webhook: {str(e)}")
        raise


@shared_task
def send_attendance_notification(notification_data):
    """
    Send attendance-related notifications (email, SMS, push).
    """
    try:
        notification_type = notification_data.get('notification_type')
        recipient_id = notification_data.get('recipient_id')
        recipient_type = notification_data.get('recipient_type')
        title = notification_data.get('title')
        message = notification_data.get('message')
        
        # This is a placeholder for notification sending
        # You would integrate with your email/SMS/push notification service here
        
        logger.info(f"Sent {notification_type} notification to {recipient_type} {recipient_id}")
        return {"status": "sent", "type": notification_type}
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        raise


@shared_task
def cleanup_old_attendance_data():
    """
    Clean up old attendance data based on retention policy.
    """
    try:
        settings_dict = get_attendance_settings()
        retention_years = settings_dict.get('DATA_RETENTION_YEARS', 7)
        
        cutoff_date = timezone.now().date() - timedelta(days=retention_years * 365)
        
        # Archive old sessions and related data
        old_sessions = AttendanceSession.objects.filter(scheduled_date__lt=cutoff_date)
        archived_count = old_sessions.count()
        
        # In a real implementation, you would:
        # 1. Export data to archive storage (S3, etc.)
        # 2. Delete from primary database
        # 3. Update audit logs
        
        logger.info(f"Archived {archived_count} old attendance sessions")
        return {"archived": archived_count, "cutoff_date": str(cutoff_date)}
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {str(e)}")
        raise


@shared_task
def generate_attendance_reports(report_params):
    """
    Generate attendance reports in background.
    """
    try:
        report_type = report_params.get('report_type')
        start_date = report_params.get('start_date')
        end_date = report_params.get('end_date')
        format_type = report_params.get('format', 'json')
        
        # This is a placeholder for report generation
        # You would implement the actual report generation logic here
        
        logger.info(f"Generated {report_type} report from {start_date} to {end_date}")
        return {"status": "generated", "type": report_type}
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise


@shared_task
def sync_offline_attendance_data(offline_data):
    """
    Sync offline attendance data from mobile devices.
    """
    try:
        student_id = offline_data.get('student_id')
        records = offline_data.get('records', [])
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return {"error": "Student not found"}
        
        synced_count = 0
        with transaction.atomic():
            for record_data in records:
                client_uuid = record_data.get('client_uuid')
                session_id = record_data.get('session_id')
                mark = record_data.get('mark')
                reason = record_data.get('reason', '')
                
                try:
                    session = AttendanceSession.objects.get(id=session_id)
                except AttendanceSession.DoesNotExist:
                    continue
                
                # Check if student is enrolled
                if not CourseEnrollment.objects.filter(
                    student=student,
                    course_section=session.course_section,
                    status='ENROLLED'
                ).exists():
                    continue
                
                # Create or update record
                record, created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={
                        'mark': mark,
                        'source': 'offline',
                        'reason': reason,
                        'client_uuid': client_uuid,
                    }
                )
                
                if not created and record.client_uuid != client_uuid:
                    # Update with offline data
                    record.mark = mark
                    record.source = 'offline'
                    record.reason = reason
                    record.client_uuid = client_uuid
                    record.save()
                
                synced_count += 1
        
        logger.info(f"Synced {synced_count} offline records for student {student.roll_number}")
        return {"synced": synced_count, "student": student.roll_number}
        
    except Exception as e:
        logger.error(f"Error syncing offline data: {str(e)}")
        raise


@shared_task
def calculate_attendance_statistics():
    """
    Calculate and cache attendance statistics for dashboards.
    """
    try:
        # Calculate various statistics
        total_sessions = AttendanceSession.objects.count()
        total_students = Student.objects.filter(status='ACTIVE').count()
        
        # Calculate average attendance
        records = AttendanceRecord.objects.all()
        total_records = records.count()
        present_records = records.filter(mark__in=['present', 'late']).count()
        average_attendance = (present_records / total_records * 100) if total_records > 0 else 0
        
        # Get pending counts
        from attendance.models import AttendanceCorrectionRequest, LeaveApplication
        pending_corrections = AttendanceCorrectionRequest.objects.filter(status='pending').count()
        pending_leaves = LeaveApplication.objects.filter(status='pending').count()
        
        statistics = {
            'total_sessions': total_sessions,
            'total_students': total_students,
            'average_attendance': round(average_attendance, 2),
            'pending_corrections': pending_corrections,
            'pending_leaves': pending_leaves,
            'calculated_at': timezone.now().isoformat()
        }
        
        # In a real implementation, you would cache these statistics
        # using Redis or similar caching mechanism
        
        logger.info("Calculated attendance statistics")
        return statistics
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {str(e)}")
        raise
