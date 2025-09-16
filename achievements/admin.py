from django.contrib import admin
from django.utils.html import format_html
from .models import Achievement, Skill, Education, Experience, Publication, Project, ResumeProfile


class OwnedEntityAdmin(admin.ModelAdmin):
	list_select_related = ('owner_content_type',)
	readonly_fields = ('owner_type', 'owner_content_type', 'owner_object_id', 'created_at', 'updated_at')
	search_fields = ('owner_object_id',)
	list_filter = ('owner_type', 'is_public') if hasattr(ResumeProfile, 'is_public') else ('owner_type',)
	actions = ('make_public', 'make_private')
	date_hierarchy = 'created_at'

	def owner_display(self, obj):
		owner_label = obj.owner_type.split('.')[-1].title() if obj.owner_type else '—'
		owner_obj = getattr(obj, 'owner', None)
		if owner_obj:
			return f"{owner_label}: {owner_obj}"
		return f"{owner_label} ({obj.owner_object_id})"
	owner_display.short_description = 'Owner'

	def make_public(self, request, queryset):
		if hasattr(queryset.model, 'is_public'):
			updated = queryset.update(is_public=True)
			self.message_user(request, f"Marked {updated} record(s) as public.")
	make_public.short_description = 'Mark selected as public'

	def make_private(self, request, queryset):
		if hasattr(queryset.model, 'is_public'):
			updated = queryset.update(is_public=False)
			self.message_user(request, f"Marked {updated} record(s) as private.")
	make_private.short_description = 'Mark selected as private'

	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.select_related('owner_content_type')

	def get_fieldsets(self, request, obj=None):
		base_owner = (
			('Owner', {
				'fields': ('owner_display', 'owner_type', 'owner_content_type', 'owner_object_id'),
				'description': 'Generic owner linking to Student, Faculty or Department'
			}),
		)
		meta = (
			('Metadata', {
				'fields': ('created_at', 'updated_at', 'created_by', 'updated_by') if hasattr(self.model, 'created_by') else ('created_at', 'updated_at'),
				'classes': ('collapse',),
			}),
		)
		if obj is None:
			return base_owner + tuple()
		return base_owner + meta

	# Show owner_display as a computed readonly
	def get_readonly_fields(self, request, obj=None):
		fields = list(super().get_readonly_fields(request, obj))
		fields.append('owner_display')
		return tuple(fields)


@admin.register(Achievement)
class AchievementAdmin(OwnedEntityAdmin):
	list_display = ('title', 'category', 'owner_display', 'achieved_on', 'is_public', 'updated_at')
	list_filter = ('category',) + OwnedEntityAdmin.list_filter
	search_fields = ('title', 'description', 'issuer_or_organizer') + OwnedEntityAdmin.search_fields
	ordering = ('-achieved_on', '-updated_at')


@admin.register(Skill)
class SkillAdmin(OwnedEntityAdmin):
	list_display = ('name', 'owner_display', 'proficiency', 'is_core', 'updated_at')
	list_filter = ('is_core',) + OwnedEntityAdmin.list_filter
	search_fields = ('name',) + OwnedEntityAdmin.search_fields
	ordering = ('-is_core', '-proficiency', 'name')


@admin.register(Education)
class EducationAdmin(OwnedEntityAdmin):
	list_display = ('institution', 'degree', 'owner_display', 'start_date', 'end_date', 'updated_at')
	search_fields = ('institution', 'degree', 'field_of_study') + OwnedEntityAdmin.search_fields
	ordering = ('-end_date', '-start_date')


@admin.register(Experience)
class ExperienceAdmin(OwnedEntityAdmin):
	list_display = ('title', 'organization', 'owner_display', 'start_date', 'end_date', 'currently_working', 'updated_at')
	list_filter = ('currently_working',) + OwnedEntityAdmin.list_filter
	search_fields = ('title', 'organization') + OwnedEntityAdmin.search_fields
	ordering = ('-end_date', '-start_date')


@admin.register(Publication)
class PublicationAdmin(OwnedEntityAdmin):
	list_display = ('title', 'year', 'owner_display', 'journal_or_conference', 'updated_at')
	list_filter = ('year',) + OwnedEntityAdmin.list_filter
	search_fields = ('title', 'authors', 'journal_or_conference') + OwnedEntityAdmin.search_fields
	ordering = ('-year', 'title')


@admin.register(Project)
class ProjectAdmin(OwnedEntityAdmin):
	list_display = ('title', 'owner_display', 'start_date', 'end_date', 'updated_at')
	search_fields = ('title', 'description', 'role') + OwnedEntityAdmin.search_fields
	ordering = ('-end_date', '-start_date')


@admin.register(ResumeProfile)
class ResumeProfileAdmin(OwnedEntityAdmin):
	list_display = ('headline', 'owner_display', 'updated_at')
	search_fields = ('headline', 'summary') + OwnedEntityAdmin.search_fields
	ordering = ('-updated_at', '-created_at')

