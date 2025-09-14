from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FacultyViewSet, FacultySubjectViewSet, FacultyScheduleViewSet,
    FacultyLeaveViewSet, FacultyPerformanceViewSet, FacultyDocumentViewSet,
    CustomFieldViewSet, CustomFieldValueViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'faculty', FacultyViewSet, basename='faculty')
router.register(r'subjects', FacultySubjectViewSet, basename='faculty-subject')
router.register(r'schedules', FacultyScheduleViewSet, basename='faculty-schedule')
router.register(r'leaves', FacultyLeaveViewSet, basename='faculty-leave')
router.register(r'performance', FacultyPerformanceViewSet, basename='faculty-performance')
router.register(r'documents', FacultyDocumentViewSet, basename='faculty-document')
router.register(r'custom-fields', CustomFieldViewSet, basename='custom-field')
router.register(r'custom-field-values', CustomFieldValueViewSet, basename='custom-field-value')

app_name = 'faculty'

urlpatterns = [
    path('api/', include(router.urls)),
]
