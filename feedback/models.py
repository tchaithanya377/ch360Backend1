from django.db import models
from django.conf import settings
from departments.models import Department
from academics.models import Course, CourseSection, Syllabus
from faculty.models import Faculty


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class FeedbackCategory(TimeStampedModel):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)

	def __str__(self) -> str:
		return self.name


class FeedbackTag(TimeStampedModel):
	name = models.CharField(max_length=50, unique=True)

	def __str__(self) -> str:
		return self.name


class Feedback(TimeStampedModel):
	class Status(models.TextChoices):
		OPEN = 'open', 'Open'
		IN_REVIEW = 'in_review', 'In Review'
		RESOLVED = 'resolved', 'Resolved'
		CLOSED = 'closed', 'Closed'

	class Priority(models.TextChoices):
		LOW = 'low', 'Low'
		MEDIUM = 'medium', 'Medium'
		HIGH = 'high', 'High'
		CRITICAL = 'critical', 'Critical'

	title = models.CharField(max_length=200)
	description = models.TextField()
	category = models.ForeignKey(FeedbackCategory, on_delete=models.SET_NULL, null=True, related_name='feedbacks')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback_created')
	is_anonymous = models.BooleanField(default=False)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
	priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
	rating = models.PositiveSmallIntegerField(null=True, blank=True)
	sentiment = models.CharField(max_length=20, blank=True)
	# First-class academic relations
	department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
	course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
	section = models.ForeignKey(CourseSection, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
	faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
	syllabus = models.ForeignKey(Syllabus, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
	# Optional generic targeting for future extensibility
	target_type = models.CharField(max_length=100, blank=True)
	target_id = models.CharField(max_length=64, blank=True)
	tags = models.ManyToManyField(FeedbackTag, blank=True, related_name='feedbacks')

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return self.title


class FeedbackComment(TimeStampedModel):
	feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='comments')
	commented_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback_comments')
	content = models.TextField()
	is_internal = models.BooleanField(default=False)

	def __str__(self) -> str:
		return f"Comment by {self.commented_by}"


class FeedbackAttachment(TimeStampedModel):
	feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='attachments')
	uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback_attachments')
	file_url = models.URLField(max_length=500)
	description = models.CharField(max_length=255, blank=True)

	def __str__(self) -> str:
		return self.file_url


class FeedbackVote(TimeStampedModel):
	feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='votes')
	voted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='feedback_votes')
	is_upvote = models.BooleanField(default=True)

	class Meta:
		unique_together = ('feedback', 'voted_by')

	def __str__(self) -> str:
		return f"{'+' if self.is_upvote else '-'} {self.voted_by_id} on {self.feedback_id}"
