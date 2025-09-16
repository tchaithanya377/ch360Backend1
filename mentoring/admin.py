from django.contrib import admin
from .models import Mentorship, Project, Meeting, Feedback, ActionItem


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0
    fields = ('title', 'status', 'start_date', 'due_date')


class MeetingInline(admin.TabularInline):
    model = Meeting
    extra = 0
    fields = ('scheduled_at', 'duration_minutes', 'agenda')


class ActionItemInline(admin.TabularInline):
    model = ActionItem
    extra = 0
    fields = ('title', 'priority', 'status', 'due_date', 'assigned_to_user')


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    list_display = (
        'mentor', 'student', 'department_ref', 'academic_year', 'grade_level', 'section',
        'risk_score', 'start_date', 'end_date', 'is_active'
    )
    list_filter = (
        'is_active', 'department_ref', 'academic_year', 'grade_level', 'section',
        'start_date', 'risk_score'
    )
    search_fields = (
        'mentor__name', 'student__first_name', 'student__last_name', 'student__roll_number',
        'objective'
    )
    date_hierarchy = 'start_date'
    inlines = [ProjectInline, MeetingInline, ActionItemInline]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentorship', 'status', 'start_date', 'due_date')
    list_filter = ('status',)
    search_fields = ('title', 'mentorship__mentor__name', 'mentorship__student__first_name', 'mentorship__student__last_name')


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'scheduled_at', 'duration_minutes', 'agenda', 'created_by')
    list_filter = ('scheduled_at', 'created_by')
    search_fields = ('agenda', 'mentorship__mentor__name', 'mentorship__student__first_name', 'mentorship__student__last_name')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('mentorship', 'project', 'meeting', 'rating', 'given_by', 'created_at')
    list_filter = ('rating', 'given_by')
    search_fields = (
        'mentorship__mentor__name', 'mentorship__student__first_name', 'mentorship__student__last_name',
        'comments'
    )


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'mentorship', 'meeting', 'priority', 'status', 'due_date', 'assigned_to_user')
    list_filter = ('priority', 'status', 'due_date')
    search_fields = (
        'title', 'description', 'mentorship__mentor__name', 'mentorship__student__first_name', 'mentorship__student__last_name'
    )
