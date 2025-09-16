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
    # Risk & wellness
    risk_score = models.PositiveSmallIntegerField(default=0, help_text="0 (low) to 100 (high)")
    risk_factors = models.JSONField(default=dict, blank=True)
    last_risk_evaluated_at = models.DateTimeField(blank=True, null=True)

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

class ActionItem(TimeStampedUUIDModel):
    mentorship = models.ForeignKey(Mentorship, on_delete=models.CASCADE, related_name='action_items')
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, blank=True, related_name='action_items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('BLOCKED', 'Blocked'),
        ('DONE', 'Done'),
        ('CANCELLED', 'Cancelled'),
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='OPEN')
    assigned_to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_action_items')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_action_items')

    class Meta:
        ordering = ['status', 'due_date', '-created_at']

