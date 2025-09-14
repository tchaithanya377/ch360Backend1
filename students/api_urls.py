from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    StudentViewSet, StudentEnrollmentHistoryViewSet, StudentDocumentViewSet,
    CustomFieldViewSet, StudentCustomFieldValueViewSet, StudentImportViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'enrollment-history', StudentEnrollmentHistoryViewSet, basename='enrollment-history')
router.register(r'documents', StudentDocumentViewSet, basename='document')
router.register(r'custom-fields', CustomFieldViewSet, basename='custom-field')
router.register(r'custom-field-values', StudentCustomFieldValueViewSet, basename='custom-field-value')
router.register(r'imports', StudentImportViewSet, basename='import')

app_name = 'students_api'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional API endpoints
    path('students/<uuid:pk>/documents/', 
         StudentViewSet.as_view({'get': 'documents'}), 
         name='student-documents'),
    
    path('students/<uuid:pk>/enrollment-history/', 
         StudentViewSet.as_view({'get': 'enrollment_history'}), 
         name='student-enrollment-history'),
    
    path('students/<uuid:pk>/custom-fields/', 
         StudentViewSet.as_view({'get': 'custom_fields'}), 
         name='student-custom-fields'),
    
    path('students/<uuid:pk>/create-login/', 
         StudentViewSet.as_view({'post': 'create_login'}), 
         name='student-create-login'),
    
    # Bulk operations
    path('students/bulk-create/', 
         StudentViewSet.as_view({'post': 'bulk_create'}), 
         name='student-bulk-create'),
    
    path('students/bulk-update/', 
         StudentViewSet.as_view({'post': 'bulk_update'}), 
         name='student-bulk-update'),
    
    path('students/bulk-delete/', 
         StudentViewSet.as_view({'delete': 'bulk_delete'}), 
         name='student-bulk-delete'),
    
    # Statistics endpoints
    path('students/stats/', 
         StudentViewSet.as_view({'get': 'stats'}), 
         name='student-stats'),
    
    path('custom-fields/stats/', 
         CustomFieldViewSet.as_view({'get': 'stats'}), 
         name='custom-field-stats'),
    
    path('imports/stats/', 
         StudentImportViewSet.as_view({'get': 'stats'}), 
         name='import-stats'),
    
    # Search endpoints
    path('students/search/', 
         StudentViewSet.as_view({'get': 'search'}), 
         name='student-search'),

    # Division statistics and divisions (API v1)
    path('students/division-statistics/',
         StudentViewSet.as_view({'get': 'division_statistics'}),
         name='student-division-statistics'),
    path('students/divisions/',
         StudentViewSet.as_view({'get': 'divisions'}),
         name='student-divisions'),
    
    # Custom field types
    path('custom-fields/types/', 
         CustomFieldViewSet.as_view({'get': 'types'}), 
         name='custom-field-types'),
    
    # Custom field values by student/field
    path('custom-field-values/by-student/', 
         StudentCustomFieldValueViewSet.as_view({'get': 'by_student'}), 
         name='custom-field-values-by-student'),
    
    path('custom-field-values/by-field/', 
         StudentCustomFieldValueViewSet.as_view({'get': 'by_field'}), 
         name='custom-field-values-by-field'),
]

