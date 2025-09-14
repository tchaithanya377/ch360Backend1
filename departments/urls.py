from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, DepartmentResourceViewSet,
    DepartmentAnnouncementViewSet, DepartmentEventViewSet, DepartmentDocumentViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', DepartmentViewSet, basename='department')
router.register(r'resources', DepartmentResourceViewSet, basename='department-resource')
router.register(r'announcements', DepartmentAnnouncementViewSet, basename='department-announcement')
router.register(r'events', DepartmentEventViewSet, basename='department-event')
router.register(r'documents', DepartmentDocumentViewSet, basename='department-document')

app_name = 'departments'

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
]
