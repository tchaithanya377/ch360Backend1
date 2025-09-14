from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for API endpoints
router = DefaultRouter()
router.register(r'api/students', views.StudentViewSet, basename='student')
router.register(r'api/enrollment-history', views.StudentEnrollmentHistoryViewSet, basename='enrollment-history')
router.register(r'api/documents', views.StudentDocumentViewSet, basename='student-documents')
router.register(r'api/custom-fields', views.CustomFieldViewSet, basename='custom-field')
router.register(r'api/custom-field-values', views.StudentCustomFieldValueViewSet, basename='custom-field-value')
router.register(r'api/student-batches', views.StudentBatchViewSet, basename='student-batch')
router.register(r'api/bulk-assignments', views.BulkAssignmentViewSet, basename='bulk-assignment')

app_name = 'students'

urlpatterns = [
    # Include API routes
    path('', include(router.urls)),
    
    # Web interface routes
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('list/', views.student_list_view, name='list'),
    path('detail/<uuid:student_id>/', views.student_detail_view, name='detail'),
    
    # Student division and assignment routes
    path('api/students/divisions/', views.StudentViewSet.as_view({'get': 'divisions'}), name='student-divisions'),
    path('api/students/assign/', views.StudentViewSet.as_view({'post': 'assign_students'}), name='assign-students'),
    path('api/students/bulk-assign/', views.StudentViewSet.as_view({'post': 'bulk_assign_by_criteria'}), name='bulk-assign-students'),
    path('api/students/smart-bulk-assign/', views.StudentViewSet.as_view({'post': 'smart_bulk_assign'}), name='smart-bulk-assign-students'),
    path('api/students/division-statistics/', views.StudentViewSet.as_view({'get': 'division_statistics'}), name='division-statistics'),
]
