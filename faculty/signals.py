from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Faculty, FacultyLeave, FacultyPerformance

User = get_user_model()


@receiver(post_save, sender=Faculty)
def create_faculty_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when faculty is created/updated"""
    if created:
        # Faculty is already created with user, so we don't need to create user here
        # This signal can be used for additional setup if needed
        pass


@receiver(pre_save, sender=FacultyLeave)
def set_leave_approval_timestamp(sender, instance, **kwargs):
    """Set approval timestamp when leave status changes to approved"""
    if instance.pk:  # Only for existing instances
        try:
            old_instance = FacultyLeave.objects.get(pk=instance.pk)
            if old_instance.status != 'APPROVED' and instance.status == 'APPROVED':
                instance.approved_at = timezone.now()
        except FacultyLeave.DoesNotExist:
            pass


@receiver(pre_save, sender=FacultyPerformance)
def calculate_overall_score(sender, instance, **kwargs):
    """Calculate overall performance score before saving"""
    if not instance.overall_score:
        scores = [
            instance.teaching_effectiveness,
            instance.student_satisfaction,
            instance.research_contribution,
            instance.administrative_work,
            instance.professional_development
        ]
        # Calculate average score
        instance.overall_score = sum(scores) / len(scores)


@receiver(post_save, sender=Faculty)
def update_user_permissions(sender, instance, created, **kwargs):
    """Update user permissions based on faculty role"""
    if created and instance.user:
        user = instance.user
        
        # Set staff status based on faculty status
        if instance.status == 'ACTIVE':
            user.is_staff = True
            user.save(update_fields=['is_staff'])
        
        # Additional permission logic can be added here
        # For example, assigning specific roles based on designation
        if instance.is_head_of_department:
            # Assign department head role
            pass
