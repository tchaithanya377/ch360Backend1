"""
Signal handlers for the attendance app.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import (
    AttendanceSession, AttendanceRecord, AttendanceAuditLog,
    LeaveApplication, AttendanceCorrectionRequest
)

User = get_user_model()


@receiver(post_save, sender=AttendanceSession)
def create_attendance_records_for_session(sender, instance, created, **kwargs):
    """Create attendance records for all students when a session is created"""
    if created:
        # Get all students in the course section via student_batch
        students = instance.course_section.student_batch.students.all()
        
        # Create attendance records for all students with default mark='absent'
        attendance_records = []
        for student in students:
            attendance_records.append(
                AttendanceRecord(
                    session=instance,
                    student=student,
                    mark='absent',
                    source='system',
                    academic_period=instance.academic_period
                )
            )
        
        # Bulk create the records
        AttendanceRecord.objects.bulk_create(attendance_records)


@receiver(pre_save, sender=AttendanceRecord)
def store_original_attendance_record(sender, instance, **kwargs):
    """Store original record data before saving for audit logging"""
    if instance.pk:
        try:
            instance._original = AttendanceRecord.objects.get(pk=instance.pk)
        except AttendanceRecord.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


@receiver(post_save, sender=AttendanceRecord)
def log_attendance_record_change(sender, instance, created, **kwargs):
    """Log attendance record changes to audit log"""
    if not created and hasattr(instance, '_original') and instance._original:
        # This is an update
        original = instance._original
        
        # Create audit log entry
        AttendanceAuditLog.objects.create(
            entity_type='AttendanceRecord',
            entity_id=str(instance.id),
            action='update',
            performed_by=getattr(instance, 'marked_by', None),
            before={
                'mark': original.mark,
                'source': original.source,
                'notes': original.notes,
            },
            after={
                'mark': instance.mark,
                'source': instance.source,
                'notes': instance.notes,
            },
            reason='Record updated',
            source='system'
        )


@receiver(post_delete, sender=AttendanceRecord)
def log_attendance_record_deletion(sender, instance, **kwargs):
    """Log attendance record deletion to audit log"""
    AttendanceAuditLog.objects.create(
        entity_type='AttendanceRecord',
        entity_id=str(instance.id),
        action='delete',
        performed_by=getattr(instance, 'marked_by', None),
        before={
            'mark': instance.mark,
            'source': instance.source,
            'notes': instance.notes,
        },
        after={},
        reason='Record deleted',
        source='system'
    )


@receiver(pre_save, sender=LeaveApplication)
def store_original_leave_application(sender, instance, **kwargs):
    """Store original leave application data before saving for audit logging"""
    if instance.pk:
        try:
            instance._original = LeaveApplication.objects.get(pk=instance.pk)
        except LeaveApplication.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


@receiver(post_save, sender=LeaveApplication)
def log_leave_application_change(sender, instance, created, **kwargs):
    """Log leave application changes to audit log"""
    if not created and hasattr(instance, '_original') and instance._original:
        # This is an update
        original = instance._original
        
        # Create audit log entry
        AttendanceAuditLog.objects.create(
            entity_type='LeaveApplication',
            entity_id=str(instance.id),
            action='update',
            performed_by=getattr(instance, 'approved_by', None),
            before={
                'status': original.status,
                'reason': original.reason,
            },
            after={
                'status': instance.status,
                'reason': instance.reason,
            },
            reason='Leave application updated',
            source='system'
        )


@receiver(pre_save, sender=AttendanceCorrectionRequest)
def store_original_correction_request(sender, instance, **kwargs):
    """Store original correction request data before saving for audit logging"""
    if instance.pk:
        try:
            instance._original = AttendanceCorrectionRequest.objects.get(pk=instance.pk)
        except AttendanceCorrectionRequest.DoesNotExist:
            instance._original = None
    else:
        instance._original = None


@receiver(post_save, sender=AttendanceCorrectionRequest)
def log_correction_request_change(sender, instance, created, **kwargs):
    """Log correction request changes to audit log"""
    if not created and hasattr(instance, '_original') and instance._original:
        # This is an update
        original = instance._original
        
        # Create audit log entry
        AttendanceAuditLog.objects.create(
            entity_type='AttendanceCorrectionRequest',
            entity_id=str(instance.id),
            action='update',
            performed_by=getattr(instance, 'reviewed_by', None),
            before={
                'status': original.status,
                'reason': original.reason,
            },
            after={
                'status': instance.status,
                'reason': instance.reason,
            },
            reason='Correction request updated',
            source='system'
        )


@receiver(post_save, sender=AttendanceSession)
def log_session_status_change(sender, instance, created, **kwargs):
    """Log attendance session status changes to audit log"""
    if not created:
        # This is an update - we could add more sophisticated tracking here
        faculty = getattr(instance, 'faculty', None)
        performed_by = None
        if faculty and hasattr(faculty, 'user'):
            performed_by = faculty.user
        
        AttendanceAuditLog.objects.create(
            entity_type='AttendanceSession',
            entity_id=str(instance.id),
            action='update',
            performed_by=performed_by,
            before={},
            after={
                'status': instance.status,
            },
            reason='Session updated',
            source='system'
        )