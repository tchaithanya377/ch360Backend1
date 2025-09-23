from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model

User = get_user_model()


class IsStudent(BasePermission):
    """Permission class to ensure user has Student role"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role via groups
        return request.user.groups.filter(name='Student').exists()
    
    def has_object_permission(self, request, view, obj):
        # For student profile access, ensure user can only access their own profile
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        if hasattr(obj, 'student_profile') and obj.student_profile.user == request.user:
            return True
        return False


class IsClassRepresentative(BasePermission):
    """Permission class for Class Representatives (CR)"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Check if user is a current Class Representative
        try:
            student = request.user.student_profile
            rep_role = student.representative_role
            return (rep_role.representative_type == 'CR' and 
                   rep_role.is_current and 
                   rep_role.is_active)
        except:
            return False


class IsLadiesRepresentative(BasePermission):
    """Permission class for Ladies Representatives (LR)"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Check if user is a current Ladies Representative
        try:
            student = request.user.student_profile
            rep_role = student.representative_role
            return (rep_role.representative_type == 'LR' and 
                   rep_role.is_current and 
                   rep_role.is_active)
        except:
            return False


class IsStudentRepresentative(BasePermission):
    """Permission class for any Student Representative (CR, LR, etc.)"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Check if user is a current representative
        try:
            student = request.user.student_profile
            rep_role = student.representative_role
            return rep_role.is_current and rep_role.is_active
        except:
            return False


class IsRepresentativeOrReadOnly(BasePermission):
    """Permission class that allows representatives to write, others to read only"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Allow read access to all students
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Allow write access only to representatives
        try:
            student = request.user.student_profile
            rep_role = student.representative_role
            return rep_role.is_current and rep_role.is_active
        except:
            return False


class CanAccessRepresentedStudents(BasePermission):
    """Permission class for accessing students represented by the current representative"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Check if user is a current representative
        try:
            student = request.user.student_profile
            rep_role = student.representative_role
            return rep_role.is_current and rep_role.is_active
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Check if the object (student) is represented by the current representative
        try:
            current_rep = request.user.student_profile.representative_role
            represented_students = current_rep.get_represented_students()
            return obj in represented_students
        except:
            return False


class CanHandleFeedback(BasePermission):
    """Permission class for handling student feedback"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Allow students to submit feedback
        if request.method == 'POST':
            return True
        
        # Allow representatives to handle feedback
        try:
            student = request.user.student_profile
            rep_role = student.representative_role
            return rep_role.is_current and rep_role.is_active
        except:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Students can only access their own feedback
        if hasattr(obj, 'student') and obj.student.user == request.user:
            return True
        
        # Representatives can access feedback they're handling
        try:
            current_rep = request.user.student_profile.representative_role
            return (current_rep.is_current and 
                   current_rep.is_active and 
                   obj.representative == current_rep)
        except:
            return False


class IsAPUniversityStudent(BasePermission):
    """Permission class specific to AP University students"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Additional AP University specific checks can be added here
        # For example, checking if student belongs to AP University
        try:
            student = request.user.student_profile
            # You can add specific checks for AP University here
            # For now, just ensure it's a valid student
            return True
        except:
            return False


class CanAccessClassData(BasePermission):
    """Permission class for accessing class-specific data"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Students can access data from their own class/section
        try:
            current_student = request.user.student_profile
            current_batch = current_student.student_batch
            
            # Check if the object belongs to the same class/section
            if hasattr(obj, 'student_batch'):
                return obj.student_batch == current_batch
            elif hasattr(obj, 'student'):
                return obj.student.student_batch == current_batch
            
            return False
        except:
            return False


class CanAccessDepartmentData(BasePermission):
    """Permission class for accessing department-specific data"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has Student role
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Students can access data from their own department
        try:
            current_student = request.user.student_profile
            current_department = current_student.student_batch.department
            
            # Check if the object belongs to the same department
            if hasattr(obj, 'department'):
                return obj.department == current_department
            elif hasattr(obj, 'student_batch'):
                return obj.student_batch.department == current_department
            elif hasattr(obj, 'student'):
                return obj.student.student_batch.department == current_department
            
            return False
        except:
            return False
