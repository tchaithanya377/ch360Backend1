from django.contrib import admin
from .models import Mentorship, Project, Meeting, Feedback


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'student', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('mentor__name', 'student__first_name', 'student__last_name')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentorship', 'status', 'start_date', 'due_date')
    list_filter = ('status',)
    search_fields = ('title', 'mentorship__mentor__name', 'mentorship__student__first_name', 'mentorship__student__last_name')


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'scheduled_at', 'duration_minutes')
    list_filter = ('scheduled_at',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'project', 'meeting', 'rating')
    list_filter = ('rating',)
