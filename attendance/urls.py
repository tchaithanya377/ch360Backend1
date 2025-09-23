"""
Enhanced Attendance URLs for CampsHub360
URL configuration for production-ready attendance system
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AcademicPeriodViewSet,
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
    BiometricWebhookView,
)
from .api_views import DropdownAPIViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'academic-periods', AcademicPeriodViewSet, basename='academicperiod')
router.register(r'configurations', AttendanceConfigurationViewSet, basename='attendanceconfiguration')
router.register(r'holidays', AcademicCalendarHolidayViewSet, basename='academiccalendarholiday')
router.register(r'timetable-slots', TimetableSlotViewSet, basename='timetableslot')
router.register(r'sessions', AttendanceSessionViewSet, basename='attendancesession')
router.register(r'records', AttendanceRecordViewSet, basename='attendancerecord')
router.register(r'leave-applications', LeaveApplicationViewSet, basename='leaveapplication')
router.register(r'correction-requests', AttendanceCorrectionRequestViewSet, basename='attendancecorrectionrequest')
router.register(r'statistics', AttendanceStatisticsViewSet, basename='attendancestatistics')
router.register(r'biometric-devices', BiometricDeviceViewSet, basename='biometricdevice')
router.register(r'biometric-templates', BiometricTemplateViewSet, basename='biometrictemplate')
router.register(r'audit-logs', AttendanceAuditLogViewSet, basename='attendanceauditlog')
router.register(r'export', AttendanceExportViewSet, basename='attendanceexport')
router.register(r'dropdowns', DropdownAPIViewSet, basename='attendancedropdowns')

# app_name = 'attendance'  # Removed to match test expectations

urlpatterns = [
    # Custom statistics endpoint (must come before router to avoid conflicts)
    path('api/statistics/overview/', AttendanceStatisticsViewSet.as_view({'get': 'attendance_statistics'}), name='attendance-statistics'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Test-compatible URL patterns (for backward compatibility with tests)
    path('api/sessions/', AttendanceSessionViewSet.as_view({'get': 'list', 'post': 'create'}), name='attendance-session-list'),
    path('api/sessions/<int:pk>/', AttendanceSessionViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='attendance-session-detail'),
    path('api/sessions/<int:pk>/open/', AttendanceSessionViewSet.as_view({'post': 'open_session'}), name='attendance-session-open'),
    path('api/sessions/<int:pk>/close/', AttendanceSessionViewSet.as_view({'post': 'close_session'}), name='attendance-session-close'),
    path('api/sessions/<int:pk>/lock/', AttendanceSessionViewSet.as_view({'post': 'lock_session'}), name='attendance-session-lock'),
    path('api/sessions/<int:pk>/qr-token/', AttendanceSessionViewSet.as_view({'post': 'generate_qr'}), name='attendance-session-qr-token'),
    path('api/sessions/<int:pk>/generate-records/', AttendanceSessionViewSet.as_view({'post': 'generate_records'}), name='attendance-session-generate-records'),
    
    # Additional URL patterns for test compatibility
    path('api/sessions/<int:pk>/open-session/', AttendanceSessionViewSet.as_view({'post': 'open_session'}), name='attendancesession-open-session'),
    path('api/sessions/<int:pk>/close-session/', AttendanceSessionViewSet.as_view({'post': 'close_session'}), name='attendancesession-close-session'),
    path('api/sessions/<int:pk>/generate-qr/', AttendanceSessionViewSet.as_view({'post': 'generate_qr'}), name='attendancesession-generate-qr'),
    
    # Records are handled by the router, but add explicit patterns for test compatibility
    path('api/records/', AttendanceRecordViewSet.as_view({'get': 'list', 'post': 'create'}), name='attendance-record-list'),
    path('api/records/<int:pk>/', AttendanceRecordViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='attendance-record-detail'),
    
    path('api/leave-applications/', LeaveApplicationViewSet.as_view({'get': 'list', 'post': 'create'}), name='attendance-leave-list'),
    path('api/leave-applications/<int:pk>/', LeaveApplicationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='attendance-leave-detail'),
    path('api/leave-applications/<int:pk>/approve/', LeaveApplicationViewSet.as_view({'post': 'approve'}), name='attendance-leave-approve'),
    path('api/leave-applications/<int:pk>/reject/', LeaveApplicationViewSet.as_view({'post': 'reject'}), name='attendance-leave-reject'),
    
    path('api/correction-requests/', AttendanceCorrectionRequestViewSet.as_view({'get': 'list', 'post': 'create'}), name='attendance-correction-list'),
    path('api/correction-requests/<int:pk>/', AttendanceCorrectionRequestViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='attendance-correction-detail'),
    path('api/correction-requests/<int:pk>/approve/', AttendanceCorrectionRequestViewSet.as_view({'post': 'approve'}), name='attendance-correction-approve'),
    path('api/correction-requests/<int:pk>/reject/', AttendanceCorrectionRequestViewSet.as_view({'post': 'reject'}), name='attendance-correction-reject'),
    
    path('api/statistics/', AttendanceStatisticsViewSet.as_view({'get': 'list'}), name='attendance-statistics-list'),
    path('api/statistics/student-summary/<uuid:student_id>/', AttendanceStatisticsViewSet.as_view({'get': 'student_summary'}), name='student-summary'),
    
    # QR Check-in endpoint
    path('api/qr-checkin/', AttendanceRecordViewSet.as_view({'post': 'qr_scan'}), name='qr-checkin'),
    
    # Offline sync endpoint
    path('api/offline-sync/', AttendanceRecordViewSet.as_view({'post': 'offline_sync'}), name='offline-sync'),
    
    # Additional custom endpoints
    path('api/academic-periods/current/', AcademicPeriodViewSet.as_view({'get': 'current'}), name='academic-period-current'),
    path('api/academic-periods/by-date/', AcademicPeriodViewSet.as_view({'get': 'by_date'}), name='academic-period-by-date'),
    path('api/academic-periods/<int:pk>/set-current/', AcademicPeriodViewSet.as_view({'post': 'set_current'}), name='academic-period-set-current'),
    path('api/academic-periods/<int:pk>/generate-timetable-slots/', AcademicPeriodViewSet.as_view({'post': 'generate_timetable_slots'}), name='academic-period-generate-slots'),
    path('api/academic-periods/<int:pk>/generate-attendance-sessions/', AcademicPeriodViewSet.as_view({'post': 'generate_attendance_sessions'}), name='academic-period-generate-sessions'),
    
    path('api/sessions/<int:pk>/open/', AttendanceSessionViewSet.as_view({'post': 'open_session'}), name='session-open'),
    path('api/sessions/<int:pk>/close/', AttendanceSessionViewSet.as_view({'post': 'close_session'}), name='session-close'),
    path('api/sessions/<int:pk>/generate-qr/', AttendanceSessionViewSet.as_view({'post': 'generate_qr'}), name='session-generate-qr'),
    path('api/sessions/generate/', AttendanceSessionViewSet.as_view({'post': 'generate_sessions'}), name='sessions-generate'),
    
    path('api/records/bulk-mark/', AttendanceRecordViewSet.as_view({'post': 'bulk_mark'}), name='records-bulk-mark'),
    path('api/records/qr-scan/', AttendanceRecordViewSet.as_view({'post': 'qr_scan'}), name='records-qr-scan'),
    
    path('api/leave-applications/<int:pk>/approve/', LeaveApplicationViewSet.as_view({'post': 'approve'}), name='leave-approve'),
    path('api/leave-applications/<int:pk>/reject/', LeaveApplicationViewSet.as_view({'post': 'reject'}), name='leave-reject'),
    
    path('api/correction-requests/<int:pk>/approve/', AttendanceCorrectionRequestViewSet.as_view({'post': 'approve'}), name='correction-approve'),
    path('api/correction-requests/<int:pk>/reject/', AttendanceCorrectionRequestViewSet.as_view({'post': 'reject'}), name='correction-reject'),
    
    path('api/statistics/student-summary/<uuid:student_id>/', AttendanceStatisticsViewSet.as_view({'get': 'student_summary'}), name='student-summary'),
    path('api/statistics/course-summary/', AttendanceStatisticsViewSet.as_view({'get': 'course_summary'}), name='statistics-course-summary'),
    
    path('api/export/data/', AttendanceExportViewSet.as_view({'post': 'export_data'}), name='export-data'),
    
    # Biometric webhook endpoint
    path('api/webhooks/biometric/', BiometricWebhookView.as_view(), name='biometric-webhook'),
    
    # Dropdown API endpoints
    path('api/dropdowns/semesters-by-academic-year/', DropdownAPIViewSet.as_view({'get': 'semesters_by_academic_year'}), name='dropdowns-semesters-by-year'),
    path('api/dropdowns/course-sections-by-period/', DropdownAPIViewSet.as_view({'get': 'course_sections_by_period'}), name='dropdowns-course-sections-by-period'),
    path('api/dropdowns/timetable-slots-by-period/', DropdownAPIViewSet.as_view({'get': 'timetable_slots_by_period'}), name='dropdowns-timetable-slots-by-period'),
    path('api/dropdowns/sessions/<int:pk>/students/', DropdownAPIViewSet.as_view({'get': 'session_students'}), name='dropdowns-session-students'),
]
