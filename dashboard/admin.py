from django.contrib import admin

# The API testing models were removed. Keep admin import safe to avoid errors
try:
    from .models import (
        APICollection, APIEnvironment, APIRequest, APITest, APITestResult,
        APITestSuite, APITestSuiteResult, APIAutomation
    )

    @admin.register(APICollection)
    class APICollectionAdmin(admin.ModelAdmin):
        list_display = ['name', 'created_by', 'is_public', 'base_url', 'created_at']
        list_filter = ['is_public', 'created_at']
        search_fields = ['name', 'description']
        readonly_fields = ['id', 'created_at', 'updated_at']
        ordering = ['-created_at']

    @admin.register(APIEnvironment)
    class APIEnvironmentAdmin(admin.ModelAdmin):
        list_display = ['name', 'created_by', 'is_default', 'created_at']
        list_filter = ['is_default', 'created_at']
        search_fields = ['name', 'description']
        readonly_fields = ['id', 'created_at', 'updated_at']
        ordering = ['-created_at']

    @admin.register(APIRequest)
    class APIRequestAdmin(admin.ModelAdmin):
        list_display = ['name', 'collection', 'method', 'url', 'order', 'created_at']
        list_filter = ['method', 'auth_type', 'body_type', 'created_at']
        search_fields = ['name', 'description', 'url']
        readonly_fields = ['id', 'created_at', 'updated_at']
        ordering = ['collection__name', 'order']
        list_select_related = ['collection']

    @admin.register(APITest)
    class APITestAdmin(admin.ModelAdmin):
        list_display = ['name', 'request', 'enabled', 'created_at']
        list_filter = ['enabled', 'created_at']
        search_fields = ['name', 'description']
        readonly_fields = ['id', 'created_at', 'updated_at']
        ordering = ['request__collection__name', 'request__order', 'name']
        list_select_related = ['request', 'request__collection']

    @admin.register(APITestResult)
    class APITestResultAdmin(admin.ModelAdmin):
        list_display = ['test', 'status', 'response_status', 'response_time', 'executed_at']
        list_filter = ['status', 'response_status', 'executed_at']
        search_fields = ['test__name', 'error_message']
        readonly_fields = ['id', 'created_at', 'updated_at', 'executed_at']
        ordering = ['-executed_at']
        list_select_related = ['test', 'request', 'environment']

    @admin.register(APITestSuite)
    class APITestSuiteAdmin(admin.ModelAdmin):
        list_display = ['name', 'collection', 'enabled', 'created_at']
        list_filter = ['enabled', 'created_at']
        search_fields = ['name', 'description']
        readonly_fields = ['id', 'created_at', 'updated_at']
        ordering = ['-created_at']
        list_select_related = ['collection']

    @admin.register(APITestSuiteResult)
    class APITestSuiteResultAdmin(admin.ModelAdmin):
        list_display = ['suite', 'status', 'total_tests', 'passed_tests', 'failed_tests', 'total_time', 'started_at']
        list_filter = ['status', 'started_at']
        search_fields = ['suite__name']
        readonly_fields = ['id', 'created_at', 'updated_at', 'started_at']
        ordering = ['-started_at']
        list_select_related = ['suite', 'environment']

    @admin.register(APIAutomation)
    class APIAutomationAdmin(admin.ModelAdmin):
        list_display = ['name', 'test_suite', 'is_active', 'schedule', 'last_run', 'next_run']
        list_filter = ['is_active', 'last_run']
        search_fields = ['name', 'description']
        readonly_fields = ['id', 'created_at', 'updated_at', 'last_run', 'next_run']
        ordering = ['-created_at']
        list_select_related = ['test_suite']
except Exception:
    # Silently skip API testing admin if models are not present
    pass
