from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Department, DepartmentResource, 
    DepartmentAnnouncement, DepartmentEvent, DepartmentDocument
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin interface for Department model"""
    
    list_display = [
        'code', 'name', 'short_name', 'department_type', 'head_of_department',
        'current_faculty_count', 'current_student_count', 'status', 'is_active',
        'created_at'
    ]
    list_filter = [
        'department_type', 'status', 'is_active', 'created_at',
        'head_of_department', 'parent_department'
    ]
    search_fields = ['name', 'short_name', 'code', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'current_faculty_count', 
        'current_student_count', 'faculty_utilization_percentage', 
        'student_utilization_percentage'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_name', 'code', 'department_type', 'parent_department')
        }),
        ('Leadership', {
            'fields': ('head_of_department', 'deputy_head')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'fax')
        }),
        ('Location', {
            'fields': ('building', 'floor', 'room_number', 'address_line1', 
                      'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Academic Information', {
            'fields': ('established_date', 'accreditation_status', 'accreditation_valid_until')
        }),
        ('Department Details', {
            'fields': ('description', 'mission', 'vision', 'objectives')
        }),
        ('Capacity & Resources', {
            'fields': ('max_faculty_capacity', 'max_student_capacity', 
                      'current_faculty_count', 'current_student_count',
                      'faculty_utilization_percentage', 'student_utilization_percentage')
        }),
        ('Financial Information', {
            'fields': ('annual_budget', 'budget_year')
        }),
        ('Status & Metadata', {
            'fields': ('status', 'is_active', 'website_url', 'social_media_links', 'logo')
        }),
        ('System Information', {
            'fields': ('id', 'created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'head_of_department', 'deputy_head', 'parent_department',
            'created_by', 'updated_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DepartmentResource)
class DepartmentResourceAdmin(admin.ModelAdmin):
    """Admin interface for DepartmentResource model"""
    
    list_display = [
        'name', 'department', 'resource_type', 'status', 'location', 
        'responsible_person', 'cost'
    ]
    list_filter = ['resource_type', 'status', 'department', 'responsible_person']
    search_fields = ['name', 'description', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('department', 'name', 'resource_type', 'description', 'location')
        }),
        ('Status & Maintenance', {
            'fields': ('status', 'purchase_date', 'warranty_expiry', 'maintenance_schedule')
        }),
        ('Responsibility & Cost', {
            'fields': ('responsible_person', 'cost', 'notes')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DepartmentAnnouncement)
class DepartmentAnnouncementAdmin(admin.ModelAdmin):
    """Admin interface for DepartmentAnnouncement model"""
    
    list_display = [
        'title', 'department', 'announcement_type', 'priority', 
        'is_published', 'publish_date', 'target_audience'
    ]
    list_filter = [
        'announcement_type', 'priority', 'is_published', 'department', 
        'target_audience', 'publish_date'
    ]
    search_fields = ['title', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at', 'publish_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('department', 'title', 'content')
        }),
        ('Classification', {
            'fields': ('announcement_type', 'priority', 'target_audience')
        }),
        ('Publishing', {
            'fields': ('is_published', 'publish_date', 'expiry_date')
        }),
        ('System Information', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by field"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DepartmentEvent)
class DepartmentEventAdmin(admin.ModelAdmin):
    """Admin interface for DepartmentEvent model"""
    
    list_display = [
        'title', 'department', 'event_type', 'start_date', 'end_date', 
        'location', 'status', 'is_public'
    ]
    list_filter = [
        'event_type', 'status', 'is_public', 'department', 
        'organizer', 'start_date'
    ]
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at', 'duration_hours']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('department', 'title', 'description', 'event_type')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'duration_hours', 'location')
        }),
        ('Event Details', {
            'fields': ('status', 'is_public', 'max_attendees', 'registration_required', 
                      'registration_deadline')
        }),
        ('Organization', {
            'fields': ('organizer', 'contact_email', 'contact_phone')
        }),
        ('System Information', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by field"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DepartmentDocument)
class DepartmentDocumentAdmin(admin.ModelAdmin):
    """Admin interface for DepartmentDocument model"""
    
    list_display = [
        'title', 'department', 'document_type', 'version', 
        'is_public', 'uploaded_by', 'created_at'
    ]
    list_filter = [
        'document_type', 'is_public', 'department', 'uploaded_by', 'created_at'
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('department', 'title', 'document_type', 'description')
        }),
        ('File Information', {
            'fields': ('file', 'version', 'is_public')
        }),
        ('System Information', {
            'fields': ('id', 'uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set uploaded_by field"""
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
