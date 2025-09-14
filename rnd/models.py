from django.conf import settings
from django.db import models


class Researcher(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='research_profiles')
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    orcid = models.CharField(max_length=50, blank=True)
    google_scholar_id = models.CharField(max_length=64, blank=True)

    def __str__(self) -> str:
        return f"{self.user.username or self.user.email}"


class Grant(models.Model):
    title = models.CharField(max_length=255)
    sponsor = models.CharField(max_length=255, blank=True)
    reference_code = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.title


class Project(models.Model):
    DRAFT = 'draft'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (ACTIVE, 'Active'),
        (PAUSED, 'Paused'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    abstract = models.TextField(blank=True)
    principal_investigator = models.ForeignKey(Researcher, on_delete=models.PROTECT, related_name='led_projects')
    members = models.ManyToManyField(Researcher, related_name='projects', blank=True)
    grants = models.ManyToManyField(Grant, related_name='projects', blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=DRAFT)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    keywords = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return self.title


class Publication(models.Model):
    JOURNAL = 'journal'
    CONFERENCE = 'conference'
    BOOK = 'book'
    PREPRINT = 'preprint'
    OTHER = 'other'

    TYPE_CHOICES = [
        (JOURNAL, 'Journal'),
        (CONFERENCE, 'Conference'),
        (BOOK, 'Book'),
        (PREPRINT, 'Preprint'),
        (OTHER, 'Other'),
    ]

    title = models.CharField(max_length=512)
    publication_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=JOURNAL)
    venue = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=128, blank=True)
    projects = models.ManyToManyField(Project, related_name='publications', blank=True)
    authors = models.ManyToManyField(Researcher, related_name='publications', blank=True)
    open_access_url = models.URLField(blank=True)

    def __str__(self) -> str:
        return self.title


class Patent(models.Model):
    title = models.CharField(max_length=512)
    application_number = models.CharField(max_length=128, blank=True)
    grant_number = models.CharField(max_length=128, blank=True)
    filing_date = models.DateField(null=True, blank=True)
    grant_date = models.DateField(null=True, blank=True)
    inventors = models.ManyToManyField(Researcher, related_name='patents', blank=True)
    projects = models.ManyToManyField(Project, related_name='patents', blank=True)

    def __str__(self) -> str:
        return self.title


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    storage_url = models.URLField(blank=True)
    projects = models.ManyToManyField(Project, related_name='datasets', blank=True)
    is_public = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class Collaboration(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collaborations')
    partner_institution = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.partner_institution} - {self.project.title}"


