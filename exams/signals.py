from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    ExamRegistration, HallTicket, ExamAttendance, 
    ExamResult, StudentDue, ExamSchedule
)


@receiver(post_save, sender=ExamRegistration)
def create_hall_ticket_on_approval(sender, instance, created, **kwargs):
    """Automatically create hall ticket when registration is approved"""
    if not created and instance.status == 'APPROVED':
        # Check if hall ticket already exists
        if not hasattr(instance, 'hall_ticket'):
            HallTicket.objects.create(exam_registration=instance)


@receiver(post_save, sender=ExamRegistration)
def create_attendance_record(sender, instance, created, **kwargs):
    """Create attendance record when registration is approved"""
    if not created and instance.status == 'APPROVED':
        # Check if attendance record already exists
        if not hasattr(instance, 'attendance'):
            ExamAttendance.objects.create(
                exam_registration=instance,
                status='ABSENT'  # Default status, will be updated during exam
            )


@receiver(post_save, sender=ExamRegistration)
def create_result_record(sender, instance, created, **kwargs):
    """Create result record when registration is approved"""
    if not created and instance.status == 'APPROVED':
        # Check if result record already exists
        if not hasattr(instance, 'result'):
            ExamResult.objects.create(exam_registration=instance)


@receiver(pre_save, sender=StudentDue)
def update_due_status(sender, instance, **kwargs):
    """Update due status based on payment amount"""
    if instance.paid_amount >= instance.amount:
        instance.status = 'PAID'
    elif instance.paid_amount > 0:
        instance.status = 'PARTIAL'
    elif instance.due_date < timezone.now().date() and instance.status == 'PENDING':
        instance.status = 'OVERDUE'


@receiver(post_save, sender=ExamSchedule)
def update_exam_status(sender, instance, created, **kwargs):
    """Update exam status based on current date and time"""
    if not created:
        now = timezone.now()
        exam_datetime = timezone.make_aware(
            timezone.datetime.combine(instance.exam_date, instance.start_time)
        )
        end_datetime = timezone.make_aware(
            timezone.datetime.combine(instance.exam_date, instance.end_time)
        )
        
        if now < exam_datetime and instance.status == 'ONGOING':
            instance.status = 'SCHEDULED'
            instance.save(update_fields=['status'])
        elif exam_datetime <= now <= end_datetime and instance.status == 'SCHEDULED':
            instance.status = 'ONGOING'
            instance.save(update_fields=['status'])
        elif now > end_datetime and instance.status in ['SCHEDULED', 'ONGOING']:
            instance.status = 'COMPLETED'
            instance.save(update_fields=['status'])


@receiver(post_save, sender=HallTicket)
def generate_ticket_number(sender, instance, created, **kwargs):
    """Generate ticket number if not provided"""
    if created and not instance.ticket_number:
        instance.generate_ticket_number()
        instance.save(update_fields=['ticket_number'])
