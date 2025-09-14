from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Assignment, AssignmentSubmission


@receiver(pre_save, sender=Assignment)
def assignment_pre_save(sender, instance, **kwargs):
    """Handle assignment pre-save logic"""
    # Auto-generate title if not provided
    if not instance.title:
        instance.title = f"Assignment - {instance.faculty.name} - {timezone.now().strftime('%Y-%m-%d')}"
    
    # Validate due date for published assignments
    if instance.status == 'PUBLISHED' and instance.due_date <= timezone.now():
        # Don't allow publishing assignments with past due dates
        instance.status = 'DRAFT'


@receiver(post_save, sender=AssignmentSubmission)
def submission_post_save(sender, instance, created, **kwargs):
    """Handle submission post-save logic"""
    if created:
        # Check if submission is late
        if timezone.now() > instance.assignment.due_date:
            instance.is_late = True
            if instance.status == 'SUBMITTED':
                instance.status = 'LATE'
            instance.save(update_fields=['is_late', 'status'])
        
        # Send notification to faculty (if notification system exists)
        # This would integrate with your notification system
        pass


@receiver(post_save, sender=Assignment)
def assignment_post_save(sender, instance, created, **kwargs):
    """Handle assignment post-save logic"""
    if created:
        # Send notification to assigned students (if notification system exists)
        # This would integrate with your notification system
        pass
