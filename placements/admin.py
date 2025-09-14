from django.contrib import admin
from .models import Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'is_active', 'created_at')
    search_fields = ('name', 'industry')
    list_filter = ('industry', 'is_active')


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'work_mode', 'is_active', 'application_deadline')
    search_fields = ('title', 'company__name')
    list_filter = ('job_type', 'work_mode', 'is_active')
    autocomplete_fields = ('company',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'status', 'applied_at')
    search_fields = ('student__roll_number', 'job__title', 'job__company__name')
    list_filter = ('status',)
    autocomplete_fields = ('student', 'job')


@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'drive_type', 'start_date', 'is_active')
    search_fields = ('title', 'company__name')
    list_filter = ('drive_type', 'is_active')
    autocomplete_fields = ('company',)


@admin.register(InterviewRound)
class InterviewRoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'drive', 'round_type', 'scheduled_at')
    search_fields = ('name', 'drive__title')
    list_filter = ('round_type',)
    autocomplete_fields = ('drive',)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('application', 'offered_role', 'package_annual_ctc', 'status', 'offered_at')
    search_fields = ('application__student__roll_number', 'application__job__title')
    list_filter = ('status',)
    autocomplete_fields = ('application',)


