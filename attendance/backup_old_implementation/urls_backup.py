from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceSessionViewSet, AttendanceRecordViewSet, AttendanceCorrectionRequestViewSet,
    LeaveApplicationViewSet, StudentAttendanceSummaryView, AttendanceReportView,
    BiometricWebhookView, AttendanceStatisticsView, QRCheckinView, OfflineSyncView,
    get_students_for_session
)

router = DefaultRouter()
router.register(r'attendance/sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'attendance/records', AttendanceRecordViewSet, basename='attendance-record')
router.register(r'attendance/corrections', AttendanceCorrectionRequestViewSet, basename='attendance-correction')
router.register(r'attendance/leave', LeaveApplicationViewSet, basename='attendance-leave')

urlpatterns = router.urls + [
    # QR and offline sync endpoints
    path('attendance/qr/checkin/', QRCheckinView.as_view(), name='qr-checkin'),
    path('attendance/offline/sync/', OfflineSyncView.as_view(), name='offline-sync'),
    
    # Student summary and reports
    path('attendance/summary/student/<uuid:student_id>/', StudentAttendanceSummaryView.as_view(), name='student-summary'),
    path('attendance/reports/', AttendanceReportView.as_view(), name='attendance-reports'),
    path('attendance/statistics/', AttendanceStatisticsView.as_view(), name='attendance-statistics'),
    
    # Webhook endpoints
    path('attendance/webhooks/biometric/', BiometricWebhookView.as_view(), name='biometric-webhook'),
    
    # Legacy AJAX endpoint
    path('admin/attendance/attendance-record/get-students-for-session/', get_students_for_session, name='get_students_for_session'),
]

