"""
Enhanced Attendance URLs for CampsHub360
URL configuration for production-ready attendance system
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AttendanceConfigurationViewSet,
    AcademicCalendarHolidayViewSet,
    TimetableSlotViewSet,
    AttendanceSessionViewSet,
    AttendanceRecordViewSet,
    LeaveApplicationViewSet,
    AttendanceCorrectionRequestViewSet,
    AttendanceStatisticsViewSet,
    BiometricDeviceViewSet,
    BiometricTemplateViewSet,
    AttendanceAuditLogViewSet,
    AttendanceExportViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'configurations', AttendanceConfigurationViewSet, basename='attendance-configuration')
router.register(r'holidays', AcademicCalendarHolidayViewSet, basename='attendance-holiday')
router.register(r'timetable-slots', TimetableSlotViewSet, basename='attendance-timetable-slot')
router.register(r'sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'records', AttendanceRecordViewSet, basename='attendance-record')
router.register(r'leave-applications', LeaveApplicationViewSet, basename='attendance-leave-application')
router.register(r'correction-requests', AttendanceCorrectionRequestViewSet, basename='attendance-correction-request')
router.register(r'statistics', AttendanceStatisticsViewSet, basename='attendance-statistics')
router.register(r'biometric-devices', BiometricDeviceViewSet, basename='attendance-biometric-device')
router.register(r'biometric-templates', BiometricTemplateViewSet, basename='attendance-biometric-template')
router.register(r'audit-logs', AttendanceAuditLogViewSet, basename='attendance-audit-log')
router.register(r'export', AttendanceExportViewSet, basename='attendance-export')

app_name = 'attendance'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Additional custom endpoints
    path('api/sessions/<uuid:pk>/open/', AttendanceSessionViewSet.as_view({'post': 'open_session'}), name='session-open'),
    path('api/sessions/<uuid:pk>/close/', AttendanceSessionViewSet.as_view({'post': 'close_session'}), name='session-close'),
    path('api/sessions/<uuid:pk>/generate-qr/', AttendanceSessionViewSet.as_view({'post': 'generate_qr'}), name='session-generate-qr'),
    path('api/sessions/generate/', AttendanceSessionViewSet.as_view({'post': 'generate_sessions'}), name='sessions-generate'),
    
    path('api/records/bulk-mark/', AttendanceRecordViewSet.as_view({'post': 'bulk_mark'}), name='records-bulk-mark'),
    path('api/records/qr-scan/', AttendanceRecordViewSet.as_view({'post': 'qr_scan'}), name='records-qr-scan'),
    
    path('api/leave-applications/<uuid:pk>/approve/', LeaveApplicationViewSet.as_view({'post': 'approve'}), name='leave-approve'),
    path('api/leave-applications/<uuid:pk>/reject/', LeaveApplicationViewSet.as_view({'post': 'reject'}), name='leave-reject'),
    
    path('api/correction-requests/<uuid:pk>/approve/', AttendanceCorrectionRequestViewSet.as_view({'post': 'approve'}), name='correction-approve'),
    path('api/correction-requests/<uuid:pk>/reject/', AttendanceCorrectionRequestViewSet.as_view({'post': 'reject'}), name='correction-reject'),
    
    path('api/statistics/student-summary/', AttendanceStatisticsViewSet.as_view({'get': 'student_summary'}), name='statistics-student-summary'),
    path('api/statistics/course-summary/', AttendanceStatisticsViewSet.as_view({'get': 'course_summary'}), name='statistics-course-summary'),
    
    path('api/export/data/', AttendanceExportViewSet.as_view({'post': 'export_data'}), name='export-data'),
]
