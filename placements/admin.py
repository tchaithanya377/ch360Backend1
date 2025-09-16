from django.contrib import admin
from .models import (
    Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer,
    PlacementStatistics, CompanyFeedback, PlacementDocument, AlumniPlacement
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'company_size', 'rating', 'total_placements', 'is_active', 'created_at')
    search_fields = ('name', 'industry', 'headquarters')
    list_filter = ('industry', 'company_size', 'is_active')
    readonly_fields = ('rating', 'total_placements', 'total_drives')


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


@admin.register(PlacementStatistics)
class PlacementStatisticsAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'department', 'program', 'placement_percentage', 'average_salary', 'total_students', 'placed_students')
    search_fields = ('academic_year', 'department__name', 'program__name')
    list_filter = ('academic_year', 'department', 'program')
    readonly_fields = ('placement_percentage',)


@admin.register(CompanyFeedback)
class CompanyFeedbackAdmin(admin.ModelAdmin):
    list_display = ('company', 'drive', 'overall_rating', 'would_visit_again', 'feedback_by', 'created_at')
    search_fields = ('company__name', 'drive__title', 'feedback_by')
    list_filter = ('overall_rating', 'would_visit_again', 'created_at')
    autocomplete_fields = ('company', 'drive')


@admin.register(PlacementDocument)
class PlacementDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'company', 'student', 'document_date', 'is_active')
    search_fields = ('title', 'company__name', 'student__roll_number')
    list_filter = ('document_type', 'is_active', 'document_date')
    autocomplete_fields = ('company', 'student', 'drive', 'created_by')


@admin.register(AlumniPlacement)
class AlumniPlacementAdmin(admin.ModelAdmin):
    list_display = ('student', 'current_company', 'current_designation', 'total_experience_years', 'willing_to_mentor', 'willing_to_recruit')
    search_fields = ('student__roll_number', 'student__first_name', 'student__last_name', 'current_company')
    list_filter = ('willing_to_mentor', 'willing_to_recruit', 'is_entrepreneur', 'pursuing_higher_studies')
    autocomplete_fields = ('student',)


