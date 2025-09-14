from django.db import models
from django.conf import settings
from students.models import Student
from departments.models import Department
from academics.models import AcademicProgram


class Company(models.Model):
    """Hiring company or organization."""
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    headquarters = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class JobType(models.TextChoices):
    FULL_TIME = 'FULL_TIME', 'Full-time'
    PART_TIME = 'PART_TIME', 'Part-time'
    INTERNSHIP = 'INTERNSHIP', 'Internship'
    CONTRACT = 'CONTRACT', 'Contract'
    TEMPORARY = 'TEMPORARY', 'Temporary'


class WorkMode(models.TextChoices):
    ONSITE = 'ONSITE', 'On-site'
    REMOTE = 'REMOTE', 'Remote'
    HYBRID = 'HYBRID', 'Hybrid'


class JobPosting(models.Model):
    """Job or internship posting."""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    work_mode = models.CharField(max_length=10, choices=WorkMode.choices, default=WorkMode.ONSITE)
    job_type = models.CharField(max_length=15, choices=JobType.choices, default=JobType.INTERNSHIP)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    skills = models.JSONField(default=list, blank=True, help_text='List of required skills')
    eligibility_criteria = models.TextField(blank=True)
    application_deadline = models.DateField(null=True, blank=True)
    openings = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.title} - {self.company.name}"


class ApplicationStatus(models.TextChoices):
    APPLIED = 'APPLIED', 'Applied'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    INTERVIEW = 'INTERVIEW', 'Interview'
    OFFERED = 'OFFERED', 'Offered'
    REJECTED = 'REJECTED', 'Rejected'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    HIRED = 'HIRED', 'Hired'


class Application(models.Model):
    """Student application to a job posting."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    # Optional link to a placement drive through which the student applied
    drive = models.ForeignKey('PlacementDrive', on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    resume = models.FileField(upload_to='applications/resumes/', blank=True, null=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'job')
        ordering = ['-applied_at']

    def __str__(self) -> str:
        return f"{self.student.roll_number} -> {self.job.title}"


class PlacementDrive(models.Model):
    """University-level placement or internship drive."""
    DRIVE_TYPE = [
        ('CAMPUS', 'On Campus'),
        ('POOL', 'Pool Campus'),
        ('VIRTUAL', 'Virtual'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='drives')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    drive_type = models.CharField(max_length=10, choices=DRIVE_TYPE, default='CAMPUS')
    venue = models.CharField(max_length=255, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    eligible_departments = models.ManyToManyField(Department, blank=True, related_name='placement_drives')
    eligible_programs = models.ManyToManyField(AcademicProgram, blank=True, related_name='placement_drives')
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    max_backlogs_allowed = models.PositiveIntegerField(default=0)
    batch_year = models.CharField(max_length=9, blank=True, help_text='e.g., 2024-2025')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_drives')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self) -> str:
        return f"{self.company.name} - {self.title}"


class InterviewRoundType(models.TextChoices):
    APTITUDE = 'APTITUDE', 'Aptitude Test'
    TECHNICAL_TEST = 'TECH_TEST', 'Technical Test'
    GROUP_DISCUSSION = 'GD', 'Group Discussion'
    TECHNICAL_INTERVIEW = 'TECH_INTERVIEW', 'Technical Interview'
    HR_INTERVIEW = 'HR_INTERVIEW', 'HR Interview'
    OTHER = 'OTHER', 'Other'


class InterviewRound(models.Model):
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='rounds')
    name = models.CharField(max_length=255)
    round_type = models.CharField(max_length=20, choices=InterviewRoundType.choices, default=InterviewRoundType.OTHER)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at', 'id']

    def __str__(self) -> str:
        return f"{self.name} - {self.drive.title}"


class OfferStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    DECLINED = 'DECLINED', 'Declined'
    EXPIRED = 'EXPIRED', 'Expired'


class Offer(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='offer')
    offered_role = models.CharField(max_length=255)
    package_annual_ctc = models.DecimalField(max_digits=12, decimal_places=2, help_text='Annual CTC')
    joining_location = models.CharField(max_length=255, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=OfferStatus.choices, default=OfferStatus.PENDING)
    offered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-offered_at']

    def __str__(self) -> str:
        return f"Offer: {self.application.student.roll_number} - {self.offered_role}"


