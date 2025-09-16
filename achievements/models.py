import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class TimeStampedUUIDModel(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
	updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

	class Meta:
		abstract = True


class OwnerType(models.TextChoices):
	STUDENT = 'students.student', 'Student'
	FACULTY = 'faculty.faculty', 'Faculty'
	DEPARTMENT = 'departments.department', 'Department'


class OwnedEntity(TimeStampedUUIDModel):
	"""Abstract base with generic owner link (student, faculty, department)."""
	owner_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	owner_object_id = models.UUIDField()
	owner = GenericForeignKey('owner_content_type', 'owner_object_id')
	owner_type = models.CharField(max_length=64, choices=OwnerType.choices)
	is_public = models.BooleanField(default=True)

	class Meta:
		abstract = True


class AchievementCategory(models.TextChoices):
	AWARD = 'AWARD', 'Award'
	CERTIFICATION = 'CERTIFICATION', 'Certification'
	PUBLICATION = 'PUBLICATION', 'Publication'
	PROJECT = 'PROJECT', 'Project'
	PATENT = 'PATENT', 'Patent'
	SPORTS = 'SPORTS', 'Sports / Co-curricular'
	VOLUNTEER = 'VOLUNTEER', 'Volunteer'
	OTHER = 'OTHER', 'Other'


class Achievement(OwnedEntity):
	title = models.CharField(max_length=255)
	category = models.CharField(max_length=32, choices=AchievementCategory.choices)
	description = models.TextField(blank=True, null=True)
	issuer_or_organizer = models.CharField(max_length=255, blank=True, null=True)
	location = models.CharField(max_length=255, blank=True, null=True)
	start_date = models.DateField(blank=True, null=True)
	end_date = models.DateField(blank=True, null=True)
	achieved_on = models.DateField(blank=True, null=True)
	url = models.URLField(blank=True, null=True)
	certificate_file = models.FileField(upload_to='achievements/certificates/', blank=True, null=True)
	metadata = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ['-achieved_on', '-created_at']
		indexes = [
			models.Index(fields=['category']),
			models.Index(fields=['owner_type']),
		]

	def __str__(self):
		return f"{self.title} ({self.get_category_display()})"


class Skill(OwnedEntity):
	name = models.CharField(max_length=120)
	proficiency = models.IntegerField(default=0)  # 0-100
	years_of_experience = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
	is_core = models.BooleanField(default=False)

	class Meta:
		unique_together = ('owner_content_type', 'owner_object_id', 'name')
		ordering = ['-is_core', '-proficiency', 'name']

	def __str__(self):
		return self.name


class Education(OwnedEntity):
	institution = models.CharField(max_length=255)
	degree = models.CharField(max_length=255)
	field_of_study = models.CharField(max_length=255, blank=True, null=True)
	start_date = models.DateField()
	end_date = models.DateField(blank=True, null=True)
	grade = models.CharField(max_length=50, blank=True, null=True)
	description = models.TextField(blank=True, null=True)

	class Meta:
		ordering = ['-end_date', '-start_date']


class Experience(OwnedEntity):
	title = models.CharField(max_length=255)
	organization = models.CharField(max_length=255)
	start_date = models.DateField()
	end_date = models.DateField(blank=True, null=True)
	currently_working = models.BooleanField(default=False)
	location = models.CharField(max_length=255, blank=True, null=True)
	responsibilities = models.TextField(blank=True, null=True)
	metadata = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ['-end_date', '-start_date']


class Publication(OwnedEntity):
	title = models.CharField(max_length=255)
	authors = models.CharField(max_length=255)
	journal_or_conference = models.CharField(max_length=255, blank=True, null=True)
	year = models.IntegerField(blank=True, null=True)
	doi = models.CharField(max_length=128, blank=True, null=True)
	url = models.URLField(blank=True, null=True)

	class Meta:
		ordering = ['-year', 'title']


class Project(OwnedEntity):
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	start_date = models.DateField(blank=True, null=True)
	end_date = models.DateField(blank=True, null=True)
	role = models.CharField(max_length=255, blank=True, null=True)
	technologies = models.JSONField(default=list, blank=True)
	url = models.URLField(blank=True, null=True)
	repository_url = models.URLField(blank=True, null=True)

	class Meta:
		ordering = ['-end_date', '-start_date']


class ResumeProfile(OwnedEntity):
	"""Aggregated resume profile for a student/faculty/department showcase."""
	headline = models.CharField(max_length=255, blank=True, null=True)
	summary = models.TextField(blank=True, null=True)
	location = models.CharField(max_length=255, blank=True, null=True)
	website = models.URLField(blank=True, null=True)
	links = models.JSONField(default=list, blank=True)

	class Meta:
		unique_together = ('owner_content_type', 'owner_object_id')
