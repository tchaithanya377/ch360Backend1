from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsDepartmentAdmin(BasePermission):
    """
    Custom permission to only allow department administrators to manage departments.
    """
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsDepartmentHead(BasePermission):
    """
    Custom permission to only allow department heads to manage their department.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check if user is a faculty member and head of department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.is_head_of_department
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check if user is head of this specific department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.department_ref == obj and faculty.is_head_of_department
        
        return False


class CanManageDepartment(BasePermission):
    """
    Custom permission to allow department management based on user role.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage their department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.is_head_of_department
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage their own department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.department_ref == obj and faculty.is_head_of_department
        
        return False


class CanViewDepartment(BasePermission):
    """
    Custom permission to allow viewing departments based on user access.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # All authenticated users can view departments
        return True
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can view everything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Faculty can view their own department and sub-departments
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            if faculty.department_ref:
                return (faculty.department_ref == obj or 
                       obj.parent_department == faculty.department_ref)
        
        # Students can view their own department
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            return student.department == obj
        
        # Regular users can view active departments
        return obj.is_active and obj.status == 'ACTIVE'


class CanCreateDepartment(BasePermission):
    """
    Custom permission to only allow authorized users to create departments.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Only superusers and staff can create departments
        return request.user.is_superuser or request.user.is_staff


class CanManageDepartmentResource(BasePermission):
    """
    Custom permission to manage department resources.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads and responsible persons can manage resources
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.is_head_of_department
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage resources in their department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return (faculty.department_ref == obj.department and 
                   faculty.is_head_of_department)
        
        # Responsible persons can manage their assigned resources
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return obj.responsible_person == faculty
        
        return False


class CanManageDepartmentAnnouncement(BasePermission):
    """
    Custom permission to manage department announcements.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage announcements
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.is_head_of_department
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage announcements in their department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return (faculty.department_ref == obj.department and 
                   faculty.is_head_of_department)
        
        # Authors can manage their own announcements
        return obj.created_by == request.user


class CanManageDepartmentEvent(BasePermission):
    """
    Custom permission to manage department events.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage events
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.is_head_of_department
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage events in their department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return (faculty.department_ref == obj.department and 
                   faculty.is_head_of_department)
        
        # Organizers can manage their own events
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return obj.organizer == faculty
        
        # Authors can manage their own events
        return obj.created_by == request.user


class CanManageDepartmentDocument(BasePermission):
    """
    Custom permission to manage department documents.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage documents
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return faculty.is_head_of_department
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Superusers and staff can do anything
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Department heads can manage documents in their department
        if hasattr(request.user, 'faculty_profile'):
            faculty = request.user.faculty_profile
            return (faculty.department_ref == obj.department and 
                   faculty.is_head_of_department)
        
        # Authors can manage their own documents
        return obj.uploaded_by == request.user
