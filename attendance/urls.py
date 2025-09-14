from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AttendanceSessionViewSet, AttendanceRecordViewSet, get_students_for_session


router = DefaultRouter()
router.register(r'attendance/sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'attendance/records', AttendanceRecordViewSet, basename='attendance-record')

urlpatterns = router.urls + [
    path('admin/attendance/attendance-record/get-students-for-session/', get_students_for_session, name='get_students_for_session'),
]

