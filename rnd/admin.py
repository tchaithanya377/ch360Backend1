from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import date
from . import models


@admin.register(models.Researcher)
class ResearcherAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'department', 'orcid', 'google_scholar_id')
    list_filter = ('department',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department', 'orcid')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'department', 'bio')
        }),
        ('Academic Profiles', {
            'fields': ('orcid', 'google_scholar_id')
        })
    )


@admin.register(models.Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ('title', 'sponsor', 'amount', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'sponsor', 'reference_code')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'sponsor', 'reference_code')
        }),
        ('Financial Details', {
            'fields': ('amount',)
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        })
    )


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'principal_investigator', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('title', 'abstract', 'keywords')
    filter_horizontal = ('members', 'grants')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'abstract', 'principal_investigator', 'members', 'grants')
        }),
        ('Timeline', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Content', {
            'fields': ('keywords',)
        })
    )


@admin.register(models.Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_type', 'venue', 'year', 'doi')
    list_filter = ('publication_type', 'year')
    search_fields = ('title', 'venue', 'doi')
    filter_horizontal = ('authors', 'projects')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'publication_type', 'venue', 'year', 'doi')
        }),
        ('Content', {
            'fields': ('open_access_url',)
        }),
        ('Relationships', {
            'fields': ('authors', 'projects')
        })
    )


@admin.register(models.Patent)
class PatentAdmin(admin.ModelAdmin):
    list_display = ('title', 'application_number', 'grant_number', 'filing_date', 'grant_date')
    list_filter = ('filing_date', 'grant_date')
    search_fields = ('title', 'application_number', 'grant_number')
    filter_horizontal = ('inventors', 'projects')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title',)
        }),
        ('Application Details', {
            'fields': ('application_number', 'grant_number', 'filing_date', 'grant_date')
        }),
        ('Relationships', {
            'fields': ('inventors', 'projects')
        })
    )


@admin.register(models.Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_public', 'storage_url')
    list_filter = ('is_public',)
    search_fields = ('name', 'description')
    filter_horizontal = ('projects',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_public')
        }),
        ('Storage', {
            'fields': ('storage_url',)
        }),
        ('Relationships', {
            'fields': ('projects',)
        })
    )


@admin.register(models.Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = ('project', 'partner_institution', 'contact_person', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('partner_institution', 'contact_person')
    fieldsets = (
        ('Basic Information', {
            'fields': ('project', 'partner_institution', 'contact_person')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        })
    )


# Custom Admin Site Configuration
admin.site.site_header = "CampsHub360 R&D Administration"
admin.site.site_title = "R&D Admin"
admin.site.index_title = "Research & Development Management"


