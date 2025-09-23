"""
Enhanced URL Configuration for Integrated Academic System
Provides comprehensive API endpoints for Academic Periods, Timetable, and Attendance
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views_integrated import (
    AcademicPeriodViewSet,
    TimetableSlotViewSet,
    AttendanceSessionViewSet,
    AttendanceRecordViewSet
)

# =============================================================================
# MAIN ROUTER
# =============================================================================

router = DefaultRouter()
router.register(r'academic-periods', AcademicPeriodViewSet, basename='academic-period')
router.register(r'timetable-slots', TimetableSlotViewSet, basename='timetable-slot')
router.register(r'attendance-sessions', AttendanceSessionViewSet, basename='attendance-session')
router.register(r'attendance-records', AttendanceRecordViewSet, basename='attendance-record')

# =============================================================================
# NESTED ROUTERS
# =============================================================================

# Academic Period nested routes
academic_period_router = routers.NestedDefaultRouter(router, r'academic-periods', lookup='academic_period')
academic_period_router.register(r'timetable-slots', TimetableSlotViewSet, basename='academic-period-timetable-slots')
academic_period_router.register(r'attendance-sessions', AttendanceSessionViewSet, basename='academic-period-attendance-sessions')
academic_period_router.register(r'attendance-records', AttendanceRecordViewSet, basename='academic-period-attendance-records')

# Timetable Slot nested routes
timetable_slot_router = routers.NestedDefaultRouter(router, r'timetable-slots', lookup='timetable_slot')
timetable_slot_router.register(r'attendance-sessions', AttendanceSessionViewSet, basename='timetable-slot-attendance-sessions')

# Attendance Session nested routes
attendance_session_router = routers.NestedDefaultRouter(router, r'attendance-sessions', lookup='attendance_session')
attendance_session_router.register(r'attendance-records', AttendanceRecordViewSet, basename='attendance-session-attendance-records')

# =============================================================================
# URL PATTERNS
# =============================================================================

urlpatterns = [
    # Main API routes
    path('', include(router.urls)),
    
    # Nested routes
    path('', include(academic_period_router.urls)),
    path('', include(timetable_slot_router.urls)),
    path('', include(attendance_session_router.urls)),
    
    # Additional custom endpoints
    path('dashboard/', include([
        path('academic-periods/', AcademicPeriodViewSet.as_view({'get': 'current'}), name='current-academic-period'),
        path('academic-periods/by-date/', AcademicPeriodViewSet.as_view({'get': 'by_date'}), name='academic-period-by-date'),
        path('timetable-slots/by-faculty/', TimetableSlotViewSet.as_view({'get': 'by_faculty'}), name='timetable-slots-by-faculty'),
        path('timetable-slots/by-course-section/', TimetableSlotViewSet.as_view({'get': 'by_course_section'}), name='timetable-slots-by-course-section'),
        path('attendance-sessions/today/', AttendanceSessionViewSet.as_view({'get': 'today'}), name='today-attendance-sessions'),
        path('attendance-sessions/open/', AttendanceSessionViewSet.as_view({'get': 'open_sessions'}), name='open-attendance-sessions'),
        path('attendance-records/student-summary/', AttendanceRecordViewSet.as_view({'get': 'student_summary'}), name='student-attendance-summary'),
        path('attendance-records/course-section-summary/', AttendanceRecordViewSet.as_view({'get': 'course_section_summary'}), name='course-section-attendance-summary'),
    ])),
    
    # Bulk operations
    path('bulk/', include([
        path('timetable-slots/create/', TimetableSlotViewSet.as_view({'post': 'bulk_create'}), name='bulk-create-timetable-slots'),
        path('attendance-sessions/create/', AttendanceSessionViewSet.as_view({'post': 'bulk_create'}), name='bulk-create-attendance-sessions'),
        path('attendance-records/mark/', AttendanceRecordViewSet.as_view({'post': 'bulk_mark'}), name='bulk-mark-attendance'),
    ])),
    
    # QR Code operations
    path('qr/', include([
        path('scan/', AttendanceRecordViewSet.as_view({'post': 'qr_scan'}), name='qr-scan-attendance'),
        path('generate/<uuid:pk>/', AttendanceSessionViewSet.as_view({'post': 'generate_qr'}), name='generate-qr-code'),
    ])),
    
    # Session management
    path('sessions/', include([
        path('<uuid:pk>/open/', AttendanceSessionViewSet.as_view({'post': 'open'}), name='open-attendance-session'),
        path('<uuid:pk>/close/', AttendanceSessionViewSet.as_view({'post': 'close'}), name='close-attendance-session'),
        path('<uuid:pk>/summary/', AttendanceSessionViewSet.as_view({'get': 'attendance_summary'}), name='attendance-session-summary'),
    ])),
    
    # Academic period management
    path('academic-periods/', include([
        path('<uuid:pk>/set-current/', AcademicPeriodViewSet.as_view({'post': 'set_current'}), name='set-current-academic-period'),
        path('<uuid:pk>/generate-timetable-slots/', AcademicPeriodViewSet.as_view({'post': 'generate_timetable_slots'}), name='generate-timetable-slots'),
        path('<uuid:pk>/generate-attendance-sessions/', AcademicPeriodViewSet.as_view({'post': 'generate_attendance_sessions'}), name='generate-attendance-sessions'),
        path('<uuid:pk>/statistics/', AcademicPeriodViewSet.as_view({'get': 'statistics'}), name='academic-period-statistics'),
    ])),
    
    # Timetable slot management
    path('timetable-slots/', include([
        path('<uuid:pk>/generate-sessions/', TimetableSlotViewSet.as_view({'post': 'generate_sessions'}), name='generate-sessions-for-slot'),
    ])),
]

# =============================================================================
# API DOCUMENTATION ENDPOINTS
# =============================================================================

# Add API documentation endpoints if needed
try:
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    from rest_framework import permissions
    
    schema_view = get_schema_view(
        openapi.Info(
            title="CampsHub360 Integrated Academic System API",
            default_version='v1',
            description="Comprehensive API for managing academic periods, timetables, and attendance",
            terms_of_service="https://www.campshub360.com/terms/",
            contact=openapi.Contact(email="api@campshub360.com"),
            license=openapi.License(name="MIT License"),
        ),
        public=True,
        permission_classes=[permissions.AllowAny],
    )
    
    # Add API documentation URLs
    urlpatterns += [
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    ]
except ImportError:
    # drf-yasg not installed, skip API documentation
    pass

# =============================================================================
# URL PATTERN SUMMARY
# =============================================================================

"""
URL Pattern Summary:

Main API Endpoints:
- /api/v1/attendance/academic-periods/ - Academic period management
- /api/v1/attendance/timetable-slots/ - Timetable slot management  
- /api/v1/attendance/attendance-sessions/ - Attendance session management
- /api/v1/attendance/attendance-records/ - Attendance record management

Nested Endpoints:
- /api/v1/attendance/academic-periods/{id}/timetable-slots/ - Slots for specific period
- /api/v1/attendance/academic-periods/{id}/attendance-sessions/ - Sessions for specific period
- /api/v1/attendance/academic-periods/{id}/attendance-records/ - Records for specific period
- /api/v1/attendance/timetable-slots/{id}/attendance-sessions/ - Sessions for specific slot
- /api/v1/attendance/attendance-sessions/{id}/attendance-records/ - Records for specific session

Dashboard Endpoints:
- /api/v1/attendance/dashboard/academic-periods/ - Current academic period
- /api/v1/attendance/dashboard/academic-periods/by-date/ - Period by date
- /api/v1/attendance/dashboard/timetable-slots/by-faculty/ - Slots by faculty
- /api/v1/attendance/dashboard/timetable-slots/by-course-section/ - Slots by course section
- /api/v1/attendance/dashboard/attendance-sessions/today/ - Today's sessions
- /api/v1/attendance/dashboard/attendance-sessions/open/ - Open sessions
- /api/v1/attendance/dashboard/attendance-records/student-summary/ - Student summary
- /api/v1/attendance/dashboard/attendance-records/course-section-summary/ - Course section summary

Bulk Operations:
- /api/v1/attendance/bulk/timetable-slots/create/ - Bulk create timetable slots
- /api/v1/attendance/bulk/attendance-sessions/create/ - Bulk create attendance sessions
- /api/v1/attendance/bulk/attendance-records/mark/ - Bulk mark attendance

QR Code Operations:
- /api/v1/attendance/qr/scan/ - Scan QR code for attendance
- /api/v1/attendance/qr/generate/{id}/ - Generate QR code for session

Session Management:
- /api/v1/attendance/sessions/{id}/open/ - Open session
- /api/v1/attendance/sessions/{id}/close/ - Close session
- /api/v1/attendance/sessions/{id}/summary/ - Session summary

Academic Period Management:
- /api/v1/attendance/academic-periods/{id}/set-current/ - Set as current period
- /api/v1/attendance/academic-periods/{id}/generate-timetable-slots/ - Generate slots
- /api/v1/attendance/academic-periods/{id}/generate-attendance-sessions/ - Generate sessions
- /api/v1/attendance/academic-periods/{id}/statistics/ - Period statistics

Timetable Slot Management:
- /api/v1/attendance/timetable-slots/{id}/generate-sessions/ - Generate sessions for slot

API Documentation (if drf-yasg is installed):
- /api/v1/attendance/swagger/ - Swagger UI
- /api/v1/attendance/redoc/ - ReDoc UI
- /api/v1/attendance/swagger.json - OpenAPI JSON schema
"""
