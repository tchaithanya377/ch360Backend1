from rest_framework import permissions


class IsFacultyOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow faculty to create/edit assignments.
    Read permissions are allowed for all authenticated users.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for faculty
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'faculty_profile')
        )


class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow students to submit assignments.
    Read permissions are allowed for faculty and students.
    """
    
    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for students
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'student_profile')
        )


class IsAssignmentOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow faculty to edit their own assignments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for the assignment owner (faculty)
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'faculty_profile') and
            obj.faculty == request.user.faculty_profile
        )


class IsSubmissionOwnerOrFaculty(permissions.BasePermission):
    """
    Custom permission to allow students to edit their own submissions
    and faculty to view/edit submissions for their assignments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Faculty can view/edit submissions for their assignments
        if (hasattr(request.user, 'faculty_profile') and 
            obj.assignment.faculty == request.user.faculty_profile):
            return True
        
        # Students can view/edit their own submissions
        if (hasattr(request.user, 'student_profile') and 
            obj.student == request.user.student_profile):
            return True
        
        # Admin can do anything
        return request.user.is_staff


class CanGradeAssignment(permissions.BasePermission):
    """
    Custom permission to only allow faculty to grade assignments.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (hasattr(request.user, 'faculty_profile') or request.user.is_staff)
        )
    
    def has_object_permission(self, request, view, obj):
        # Faculty can grade submissions for their assignments
        if (hasattr(request.user, 'faculty_profile') and 
            obj.assignment.faculty == request.user.faculty_profile):
            return True
        
        # Admin can grade any assignment
        return request.user.is_staff


class IsHODOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow HOD and admin users.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admin users
        if request.user.is_staff:
            return True
        
        # HOD users (assuming HOD is a designation in faculty model)
        if (hasattr(request.user, 'faculty_profile') and 
            request.user.faculty_profile.designation == 'HEAD_OF_DEPARTMENT'):
            return True
        
        return False
