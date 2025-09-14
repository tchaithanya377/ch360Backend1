from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Department

User = get_user_model()


@receiver(post_save, sender=User)
def update_department_counts_on_faculty_change(sender, instance, created, **kwargs):
    """
    Update department counts when faculty is created or updated
    """
    if hasattr(instance, 'faculty_profile'):
        faculty = instance.faculty_profile
        if faculty.department_ref:
            faculty.department_ref.update_counts()


@receiver(post_delete, sender=User)
def update_department_counts_on_faculty_delete(sender, instance, **kwargs):
    """
    Update department counts when faculty is deleted
    """
    if hasattr(instance, 'faculty_profile'):
        faculty = instance.faculty_profile
        if faculty.department_ref:
            faculty.department_ref.update_counts()


@receiver(post_save, sender='students.Student')
def update_department_counts_on_student_change(sender, instance, created, **kwargs):
    """
    Update department counts when student is created or updated
    """
    if instance.department:
        instance.department.update_counts()


@receiver(post_delete, sender='students.Student')
def update_department_counts_on_student_delete(sender, instance, **kwargs):
    """
    Update department counts when student is deleted
    """
    if instance.department:
        instance.department.update_counts()


@receiver(post_save, sender='faculty.Faculty')
def update_department_counts_on_faculty_profile_change(sender, instance, created, **kwargs):
    """
    Update department counts when faculty profile is created or updated
    """
    if instance.department_ref:
        instance.department_ref.update_counts()


@receiver(post_delete, sender='faculty.Faculty')
def update_department_counts_on_faculty_profile_delete(sender, instance, **kwargs):
    """
    Update department counts when faculty profile is deleted
    """
    if instance.department_ref:
        instance.department_ref.update_counts()
