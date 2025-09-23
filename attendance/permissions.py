"""
Enhanced Attendance Permissions for CampsHub360
Role-based access control for production-ready attendance system
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    Read permissions are allowed for any authenticated user.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for admin users
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsFacultyOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow faculty members and admins to access attendance data.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user is faculty
        return hasattr(request.user, 'faculty') and request.user.faculty is not None


class IsStudentOrFacultyOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow students, faculty, and admins to access attendance data.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user is faculty
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        # Check if user is student
        if hasattr(request.user, 'student') and request.user.student is not None:
            return True
        
        return False


class CanManageAcademicPeriods(permissions.BasePermission):
    """
    Custom permission for academic period management.
    Only admins and academic coordinators can manage academic periods.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user has academic coordinator role
        if hasattr(request.user, 'roles'):
            return request.user.roles.filter(name__in=['Academic Coordinator', 'Dean']).exists()
        
        return False


class CanManageTimetableSlots(permissions.BasePermission):
    """
    Custom permission for timetable slot management.
    Faculty can manage their own slots, admins can manage all.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can manage their own slots
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can only manage their own slots
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return obj.faculty == request.user.faculty
        
        return False


class CanManageAttendanceSessions(permissions.BasePermission):
    """
    Custom permission for attendance session management.
    Faculty can manage their own sessions, admins can manage all.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can manage their own sessions
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can only manage their own sessions
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return obj.faculty == request.user.faculty
        
        return False


class CanViewAttendanceRecords(permissions.BasePermission):
    """
    Custom permission for viewing attendance records.
    Students can view their own records, faculty can view their class records, admins can view all.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty and students can view records
        if (hasattr(request.user, 'faculty') and request.user.faculty is not None) or \
           (hasattr(request.user, 'student') and request.user.student is not None):
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Students can only view their own records
        if hasattr(request.user, 'student') and request.user.student is not None:
            return obj.student == request.user.student
        
        # Faculty can view records for their sessions
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return obj.session.faculty == request.user.faculty
        
        return False


class CanMarkAttendance(permissions.BasePermission):
    """
    Custom permission for marking attendance.
    Only faculty and admins can mark attendance.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can mark attendance
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can only mark attendance for their own sessions
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return obj.session.faculty == request.user.faculty
        
        return False


class CanManageLeaveApplications(permissions.BasePermission):
    """
    Custom permission for leave application management.
    Students can create applications, faculty can approve/reject their class applications, admins can manage all.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Students can create applications
        if hasattr(request.user, 'student') and request.user.student is not None:
            return True
        
        # Faculty can manage applications
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Students can only manage their own applications
        if hasattr(request.user, 'student') and request.user.student is not None:
            return obj.student == request.user.student
        
        # Faculty can manage applications for their students
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            # Check if the student is in any of the faculty's classes
            return obj.student.course_sections.filter(faculty=request.user.faculty).exists()
        
        return False


class CanManageCorrectionRequests(permissions.BasePermission):
    """
    Custom permission for attendance correction request management.
    Students can create requests, faculty can approve/reject their class requests, admins can manage all.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Students can create requests
        if hasattr(request.user, 'student') and request.user.student is not None:
            return True
        
        # Faculty can manage requests
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Students can only manage their own requests
        if hasattr(request.user, 'student') and request.user.student is not None:
            return obj.student == request.user.student
        
        # Faculty can manage requests for their sessions
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return obj.session.faculty == request.user.faculty
        
        return False


class CanViewStatistics(permissions.BasePermission):
    """
    Custom permission for viewing attendance statistics.
    Faculty can view their class statistics, admins can view all.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Faculty can view statistics
        if hasattr(request.user, 'faculty') and request.user.faculty is not None:
            return True
        
        return False


class CanExportData(permissions.BasePermission):
    """
    Custom permission for data export.
    Only admins and authorized personnel can export data.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user has data export role
        if hasattr(request.user, 'roles'):
            return request.user.roles.filter(name__in=['Data Analyst', 'Academic Coordinator', 'Dean']).exists()
        
        return False


class CanManageBiometricDevices(permissions.BasePermission):
    """
    Custom permission for biometric device management.
    Only IT administrators can manage biometric devices.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user has IT administrator role
        if hasattr(request.user, 'roles'):
            return request.user.roles.filter(name__in=['IT Administrator', 'System Administrator']).exists()
        
        return False


class CanViewAuditLogs(permissions.BasePermission):
    """
    Custom permission for viewing audit logs.
    Only admins and authorized personnel can view audit logs.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user has audit access role
        if hasattr(request.user, 'roles'):
            return request.user.roles.filter(name__in=['Auditor', 'Academic Coordinator', 'Dean']).exists()
        
        return False


# Permission combinations for different viewsets
class AcademicPeriodPermissions(permissions.BasePermission):
    """Combined permissions for AcademicPeriod operations"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return CanManageAcademicPeriods().has_permission(request, view)


class TimetableSlotPermissions(permissions.BasePermission):
    """Combined permissions for TimetableSlot operations"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return CanManageTimetableSlots().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return CanManageTimetableSlots().has_object_permission(request, view, obj)


class AttendanceSessionPermissions(permissions.BasePermission):
    """Combined permissions for AttendanceSession operations"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return CanManageAttendanceSessions().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return CanManageAttendanceSessions().has_object_permission(request, view, obj)


class AttendanceRecordPermissions(permissions.BasePermission):
    """Combined permissions for AttendanceRecord operations"""
    
    def has_permission(self, request, view):
        return CanViewAttendanceRecords().has_permission(request, view)
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return CanViewAttendanceRecords().has_object_permission(request, view, obj)
        return CanMarkAttendance().has_object_permission(request, view, obj)