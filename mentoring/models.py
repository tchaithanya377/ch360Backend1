from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Mentorship(TimeStampedUUIDModel):
    mentor = models.ForeignKey('faculty.Faculty', on_delete=models.CASCADE, related_name='mentorships')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='mentorships')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    objective = models.CharField(max_length=255, blank=True, null=True)
    # Cohort context
    department_ref = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='mentorships')
    academic_year = models.CharField(max_length=9, blank=True, null=True, help_text="e.g., 2024-2025")
    grade_level = models.CharField(max_length=2, blank=True, null=True)
    section = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        unique_together = ('mentor', 'student', 'start_date')
        ordering = ['-created_at']


class Project(TimeStampedUUIDModel):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, default='PLANNED')  # PLANNED, IN_PROGRESS, COMPLETED, ON_HOLD
    start_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']


class Meeting(TimeStampedUUIDModel):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='meetings')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    agenda = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_meetings')

    class Meta:
        ordering = ['-scheduled_at']


class Feedback(TimeStampedUUIDModel):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='feedback')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback')
    given_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentoring_feedback_given')
    rating = models.PositiveSmallIntegerField(default=0)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

# Create your models here.
