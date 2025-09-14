from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exam-sessions', views.ExamSessionViewSet)
router.register(r'exam-schedules', views.ExamScheduleViewSet)
router.register(r'exam-rooms', views.ExamRoomViewSet)
router.register(r'room-allocations', views.ExamRoomAllocationViewSet)
router.register(r'staff-assignments', views.ExamStaffAssignmentViewSet)
router.register(r'student-dues', views.StudentDueViewSet)
router.register(r'exam-registrations', views.ExamRegistrationViewSet)
router.register(r'hall-tickets', views.HallTicketViewSet)
router.register(r'exam-attendance', views.ExamAttendanceViewSet)
router.register(r'exam-violations', views.ExamViolationViewSet)
router.register(r'exam-results', views.ExamResultViewSet)

app_name = 'exams'

urlpatterns = [
    path('api/', include(router.urls)),
    
    # Additional custom endpoints
    path('api/dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
    path('api/reports/exam-summary/', views.ExamSummaryReportView.as_view(), name='exam-summary-report'),
    path('api/reports/student-performance/', views.StudentPerformanceReportView.as_view(), name='student-performance-report'),
    path('api/bulk-operations/generate-hall-tickets/', views.BulkGenerateHallTicketsView.as_view(), name='bulk-generate-hall-tickets'),
    path('api/bulk-operations/assign-rooms/', views.BulkAssignRoomsView.as_view(), name='bulk-assign-rooms'),
    path('api/bulk-operations/assign-staff/', views.BulkAssignStaffView.as_view(), name='bulk-assign-staff'),
]
