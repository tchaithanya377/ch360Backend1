from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Tutorial, APIEndpoint, CodeExample, 
    Step, DocumentationPage, FAQ
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color_display', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']

    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">●</span> {}',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Color'


class StepInline(admin.TabularInline):
    model = Step
    extra = 0
    ordering = ['order']


class CodeExampleInline(admin.TabularInline):
    model = CodeExample
    extra = 0
    ordering = ['order']


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'estimated_time', 'featured', 'is_published', 'view_count', 'created_at']
    list_filter = ['category', 'difficulty', 'featured', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'content', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['featured', 'is_published']
    inlines = [StepInline, CodeExampleInline]
    ordering = ['order', 'title']
    filter_horizontal = []

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category', 'difficulty', 'estimated_time')
        }),
        ('Content', {
            'fields': ('content', 'prerequisites', 'tags')
        }),
        ('Settings', {
            'fields': ('author', 'featured', 'is_published', 'order')
        }),
    )


@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    list_display = ['title', 'method', 'endpoint', 'category', 'authentication_required', 'featured', 'is_active', 'created_at']
    list_filter = ['method', 'category', 'authentication_required', 'featured', 'is_active', 'created_at']
    search_fields = ['title', 'endpoint', 'description', 'tags']
    list_editable = ['featured', 'is_active']
    inlines = [CodeExampleInline]
    ordering = ['order', 'title']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'endpoint', 'method', 'description', 'category')
        }),
        ('Request Details', {
            'fields': ('request_headers', 'request_body', 'query_parameters', 'path_parameters')
        }),
        ('Response Details', {
            'fields': ('response_schema', 'example_response', 'status_codes')
        }),
        ('Additional Info', {
            'fields': ('authentication_required', 'rate_limit', 'tags', 'featured', 'is_active', 'order')
        }),
    )


@admin.register(CodeExample)
class CodeExampleAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'tutorial', 'api_endpoint', 'order', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['title', 'code', 'description']
    list_editable = ['order']
    ordering = ['order', 'title']


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ['tutorial', 'order', 'title', 'has_code', 'created_at']
    list_filter = ['has_code', 'created_at']
    search_fields = ['title', 'content']
    list_editable = ['order']
    ordering = ['tutorial', 'order']


@admin.register(DocumentationPage)
class DocumentationPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'category', 'is_published', 'order', 'created_at']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published', 'order']
    ordering = ['order', 'title']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_published', 'order', 'created_at']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['is_published', 'order']
    ordering = ['order', 'question']