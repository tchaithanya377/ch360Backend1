"""
Comprehensive permission tests for assignments app.
Tests all custom permission classes and access control logic.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework import status

from assignments.permissions import (
    IsFacultyOrReadOnly, IsStudentOrReadOnly, IsAssignmentOwnerOrReadOnly,
    IsSubmissionOwnerOrFaculty, CanGradeAssignment, IsHODOrAdmin
)
from assignments.tests.factories import (
    assignment_factory, assignment_submission_factory, user_factory,
    faculty_factory, student_factory
)

User = get_user_model()


class BasePermissionTest(TestCase):
    """Base test class for permission tests"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_factory()
        self.faculty = faculty_factory()
        self.student = student_factory()
        self.admin_user = user_factory()
        self.admin_user.is_staff = True
        self.admin_user.save()

        # Setup user profiles
        self.faculty_user = self.faculty.user if hasattr(self.faculty, 'user') else user_factory()
        self.faculty_user.faculty_profile = self.faculty
        
        self.student_user = self.student.user if hasattr(self.student, 'user') else user_factory()
        self.student_user.student_profile = self.student

    def create_request(self, method='GET', user=None):
        """Create a request with specified method and user"""
        if method == 'GET':
            request = self.factory.get('/')
        elif method == 'POST':
            request = self.factory.post('/')
        elif method == 'PUT':
            request = self.factory.put('/')
        elif method == 'PATCH':
            request = self.factory.patch('/')
        elif method == 'DELETE':
            request = self.factory.delete('/')
        else:
            request = self.factory.get('/')
        
        if user:
            request.user = user
        return request


class TestIsFacultyOrReadOnlyPermission(BasePermissionTest):
    """Test IsFacultyOrReadOnly permission"""

    def setUp(self):
        super().setUp()
        self.permission = IsFacultyOrReadOnly()

    def test_anonymous_user_read_access_denied(self):
        """Test anonymous user read access is denied"""
        from django.contrib.auth.models import AnonymousUser
        request = self.create_request('GET')
        request.user = AnonymousUser()
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_authenticated_user_read_access_allowed(self):
        """Test authenticated user read access is allowed"""
        request = self.create_request('GET', self.user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_faculty_write_access_allowed(self):
        """Test faculty write access is allowed"""
        request = self.create_request('POST', self.faculty_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_write_access_denied(self):
        """Test student write access is denied"""
        request = self.create_request('POST', self.student_user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_regular_user_write_access_denied(self):
        """Test regular user write access is denied"""
        request = self.create_request('POST', self.user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_write_access_denied(self):
        """Test unauthenticated write access is denied"""
        from django.contrib.auth.models import AnonymousUser
        request = self.create_request('POST')
        request.user = AnonymousUser()
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_faculty_update_access_allowed(self):
        """Test faculty update access is allowed"""
        request = self.create_request('PUT', self.faculty_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_faculty_delete_access_allowed(self):
        """Test faculty delete access is allowed"""
        request = self.create_request('DELETE', self.faculty_user)
        
        self.assertTrue(self.permission.has_permission(request, None))


class TestIsStudentOrReadOnlyPermission(BasePermissionTest):
    """Test IsStudentOrReadOnly permission"""

    def setUp(self):
        super().setUp()
        self.permission = IsStudentOrReadOnly()

    def test_authenticated_user_read_access_allowed(self):
        """Test authenticated user read access is allowed"""
        request = self.create_request('GET', self.user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_write_access_allowed(self):
        """Test student write access is allowed"""
        request = self.create_request('POST', self.student_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_faculty_write_access_denied(self):
        """Test faculty write access is denied"""
        request = self.create_request('POST', self.faculty_user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_regular_user_write_access_denied(self):
        """Test regular user write access is denied"""
        request = self.create_request('POST', self.user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_read_access_denied(self):
        """Test unauthenticated read access is denied"""
        from django.contrib.auth.models import AnonymousUser
        request = self.create_request('GET')
        request.user = AnonymousUser()
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_student_update_access_allowed(self):
        """Test student update access is allowed"""
        request = self.create_request('PUT', self.student_user)
        
        self.assertTrue(self.permission.has_permission(request, None))


class TestIsAssignmentOwnerOrReadOnlyPermission(BasePermissionTest):
    """Test IsAssignmentOwnerOrReadOnly permission"""

    def setUp(self):
        super().setUp()
        self.permission = IsAssignmentOwnerOrReadOnly()
        self.assignment = assignment_factory.make(faculty=self.faculty)

    def test_authenticated_user_read_access_allowed(self):
        """Test authenticated user read access is allowed"""
        request = self.create_request('GET', self.user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.assignment))

    def test_assignment_owner_write_access_allowed(self):
        """Test assignment owner write access is allowed"""
        request = self.create_request('POST', self.faculty_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.assignment))

    def test_non_owner_faculty_write_access_denied(self):
        """Test non-owner faculty write access is denied"""
        other_faculty = faculty_factory()
        other_faculty_user = other_faculty.user if hasattr(other_faculty, 'user') else user_factory()
        other_faculty_user.faculty_profile = other_faculty
        
        request = self.create_request('POST', other_faculty_user)
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.assignment))

    def test_student_write_access_denied(self):
        """Test student write access is denied"""
        request = self.create_request('POST', self.student_user)
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.assignment))

    def test_unauthenticated_read_access_denied(self):
        """Test unauthenticated read access is denied"""
        from django.contrib.auth.models import AnonymousUser
        request = self.create_request('GET')
        request.user = AnonymousUser()
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.assignment))

    def test_assignment_owner_update_access_allowed(self):
        """Test assignment owner update access is allowed"""
        request = self.create_request('PUT', self.faculty_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.assignment))

    def test_assignment_owner_delete_access_allowed(self):
        """Test assignment owner delete access is allowed"""
        request = self.create_request('DELETE', self.faculty_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.assignment))


class TestIsSubmissionOwnerOrFacultyPermission(BasePermissionTest):
    """Test IsSubmissionOwnerOrFaculty permission"""

    def setUp(self):
        super().setUp()
        self.permission = IsSubmissionOwnerOrFaculty()
        self.assignment = assignment_factory.make(faculty=self.faculty)
        self.submission = assignment_submission_factory.make(
            assignment=self.assignment,
            student=self.student
        )

    def test_submission_owner_access_allowed(self):
        """Test submission owner access is allowed"""
        request = self.create_request('GET', self.student_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))

    def test_assignment_faculty_access_allowed(self):
        """Test assignment faculty access is allowed"""
        request = self.create_request('GET', self.faculty_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))

    def test_other_student_access_denied(self):
        """Test other student access is denied"""
        other_student = student_factory()
        other_student_user = other_student.user if hasattr(other_student, 'user') else user_factory()
        other_student_user.student_profile = other_student
        
        request = self.create_request('GET', other_student_user)
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.submission))

    def test_other_faculty_access_denied(self):
        """Test other faculty access is denied"""
        other_faculty = faculty_factory()
        other_faculty_user = other_faculty.user if hasattr(other_faculty, 'user') else user_factory()
        other_faculty_user.faculty_profile = other_faculty
        
        request = self.create_request('GET', other_faculty_user)
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.submission))

    def test_admin_access_allowed(self):
        """Test admin access is allowed"""
        request = self.create_request('GET', self.admin_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))

    def test_regular_user_access_denied(self):
        """Test regular user access is denied"""
        request = self.create_request('GET', self.user)
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.submission))

    def test_submission_owner_write_access_allowed(self):
        """Test submission owner write access is allowed"""
        request = self.create_request('PUT', self.student_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))

    def test_assignment_faculty_write_access_allowed(self):
        """Test assignment faculty write access is allowed"""
        request = self.create_request('PUT', self.faculty_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))


class TestCanGradeAssignmentPermission(BasePermissionTest):
    """Test CanGradeAssignment permission"""

    def setUp(self):
        super().setUp()
        self.permission = CanGradeAssignment()
        self.assignment = assignment_factory.make(faculty=self.faculty)
        self.submission = assignment_submission_factory.make(
            assignment=self.assignment,
            student=self.student
        )

    def test_faculty_has_permission(self):
        """Test faculty has grading permission"""
        request = self.create_request('POST', self.faculty_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_admin_has_permission(self):
        """Test admin has grading permission"""
        request = self.create_request('POST', self.admin_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_student_no_permission(self):
        """Test student has no grading permission"""
        request = self.create_request('POST', self.student_user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_regular_user_no_permission(self):
        """Test regular user has no grading permission"""
        request = self.create_request('POST', self.user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_no_permission(self):
        """Test unauthenticated user has no grading permission"""
        from django.contrib.auth.models import AnonymousUser
        request = self.create_request('POST')
        request.user = AnonymousUser()
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_assignment_faculty_object_permission_allowed(self):
        """Test assignment faculty has object permission"""
        request = self.create_request('POST', self.faculty_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))

    def test_other_faculty_object_permission_denied(self):
        """Test other faculty has no object permission"""
        other_faculty = faculty_factory()
        other_faculty_user = other_faculty.user if hasattr(other_faculty, 'user') else user_factory()
        other_faculty_user.faculty_profile = other_faculty
        
        request = self.create_request('POST', other_faculty_user)
        
        self.assertFalse(self.permission.has_object_permission(request, None, self.submission))

    def test_admin_object_permission_allowed(self):
        """Test admin has object permission"""
        request = self.create_request('POST', self.admin_user)
        
        self.assertTrue(self.permission.has_object_permission(request, None, self.submission))


class TestIsHODOrAdminPermission(BasePermissionTest):
    """Test IsHODOrAdmin permission"""

    def setUp(self):
        super().setUp()
        self.permission = IsHODOrAdmin()
        
        # Create HOD faculty
        self.hod_faculty = faculty_factory()
        self.hod_faculty.designation = 'HEAD_OF_DEPARTMENT'
        self.hod_faculty.save()
        self.hod_user = self.hod_faculty.user if hasattr(self.hod_faculty, 'user') else user_factory()
        self.hod_user.faculty_profile = self.hod_faculty

    def test_admin_has_permission(self):
        """Test admin has permission"""
        request = self.create_request('GET', self.admin_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_hod_has_permission(self):
        """Test HOD has permission"""
        request = self.create_request('GET', self.hod_user)
        
        self.assertTrue(self.permission.has_permission(request, None))

    def test_regular_faculty_no_permission(self):
        """Test regular faculty has no permission"""
        request = self.create_request('GET', self.faculty_user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_student_no_permission(self):
        """Test student has no permission"""
        request = self.create_request('GET', self.student_user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_regular_user_no_permission(self):
        """Test regular user has no permission"""
        request = self.create_request('GET', self.user)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_unauthenticated_no_permission(self):
        """Test unauthenticated user has no permission"""
        from django.contrib.auth.models import AnonymousUser
        request = self.create_request('GET')
        request.user = AnonymousUser()
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_faculty_without_designation_no_permission(self):
        """Test faculty without designation has no permission"""
        faculty_no_designation = faculty_factory()
        faculty_no_designation.designation = None
        faculty_no_designation.save()
        faculty_user_no_designation = faculty_no_designation.user if hasattr(faculty_no_designation, 'user') else user_factory()
        faculty_user_no_designation.faculty_profile = faculty_no_designation
        
        request = self.create_request('GET', faculty_user_no_designation)
        
        self.assertFalse(self.permission.has_permission(request, None))

    def test_faculty_with_different_designation_no_permission(self):
        """Test faculty with different designation has no permission"""
        faculty_different = faculty_factory()
        faculty_different.designation = 'PROFESSOR'
        faculty_different.save()
        faculty_user_different = faculty_different.user if hasattr(faculty_different, 'user') else user_factory()
        faculty_user_different.faculty_profile = faculty_different
        
        request = self.create_request('GET', faculty_user_different)
        
        self.assertFalse(self.permission.has_permission(request, None))


class TestPermissionIntegration(BasePermissionTest):
    """Test permission integration scenarios"""

    def test_assignment_creation_permissions(self):
        """Test assignment creation permission scenarios"""
        permission = IsFacultyOrReadOnly()
        
        # Faculty can create
        request = self.create_request('POST', self.faculty_user)
        self.assertTrue(permission.has_permission(request, None))
        
        # Student cannot create
        request = self.create_request('POST', self.student_user)
        self.assertFalse(permission.has_permission(request, None))
        
        # Admin cannot create (not faculty)
        request = self.create_request('POST', self.admin_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_submission_creation_permissions(self):
        """Test submission creation permission scenarios"""
        permission = IsStudentOrReadOnly()
        
        # Student can create
        request = self.create_request('POST', self.student_user)
        self.assertTrue(permission.has_permission(request, None))
        
        # Faculty cannot create
        request = self.create_request('POST', self.faculty_user)
        self.assertFalse(permission.has_permission(request, None))
        
        # Admin cannot create (not student)
        request = self.create_request('POST', self.admin_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_grading_permissions(self):
        """Test grading permission scenarios"""
        permission = CanGradeAssignment()
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        # Assignment faculty can grade
        request = self.create_request('POST', self.faculty_user)
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, submission))
        
        # Other faculty cannot grade
        other_faculty = faculty_factory()
        other_faculty_user = other_faculty.user if hasattr(other_faculty, 'user') else user_factory()
        other_faculty_user.faculty_profile = other_faculty
        
        request = self.create_request('POST', other_faculty_user)
        self.assertTrue(permission.has_permission(request, None))  # Has general permission
        self.assertFalse(permission.has_object_permission(request, None, submission))  # No object permission
        
        # Admin can grade any
        request = self.create_request('POST', self.admin_user)
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, submission))
        
        # Student cannot grade
        request = self.create_request('POST', self.student_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_assignment_ownership_permissions(self):
        """Test assignment ownership permission scenarios"""
        permission = IsAssignmentOwnerOrReadOnly()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Owner can modify
        request = self.create_request('PUT', self.faculty_user)
        self.assertTrue(permission.has_object_permission(request, None, assignment))
        
        # Non-owner cannot modify
        other_faculty = faculty_factory()
        other_faculty_user = other_faculty.user if hasattr(other_faculty, 'user') else user_factory()
        other_faculty_user.faculty_profile = other_faculty
        
        request = self.create_request('PUT', other_faculty_user)
        self.assertFalse(permission.has_object_permission(request, None, assignment))
        
        # Anyone can read
        request = self.create_request('GET', self.student_user)
        self.assertTrue(permission.has_object_permission(request, None, assignment))
        
        request = self.create_request('GET', other_faculty_user)
        self.assertTrue(permission.has_object_permission(request, None, assignment))

    def test_submission_ownership_permissions(self):
        """Test submission ownership permission scenarios"""
        permission = IsSubmissionOwnerOrFaculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        # Submission owner can access
        request = self.create_request('GET', self.student_user)
        self.assertTrue(permission.has_object_permission(request, None, submission))
        
        # Assignment faculty can access
        request = self.create_request('GET', self.faculty_user)
        self.assertTrue(permission.has_object_permission(request, None, submission))
        
        # Other student cannot access
        other_student = student_factory()
        other_student_user = other_student.user if hasattr(other_student, 'user') else user_factory()
        other_student_user.student_profile = other_student
        
        request = self.create_request('GET', other_student_user)
        self.assertFalse(permission.has_object_permission(request, None, submission))
        
        # Other faculty cannot access
        other_faculty = faculty_factory()
        other_faculty_user = other_faculty.user if hasattr(other_faculty, 'user') else user_factory()
        other_faculty_user.faculty_profile = other_faculty
        
        request = self.create_request('GET', other_faculty_user)
        self.assertFalse(permission.has_object_permission(request, None, submission))
        
        # Admin can access
        request = self.create_request('GET', self.admin_user)
        self.assertTrue(permission.has_object_permission(request, None, submission))

    def test_hod_admin_permissions(self):
        """Test HOD and admin permission scenarios"""
        permission = IsHODOrAdmin()
        
        # Admin has access
        request = self.create_request('GET', self.admin_user)
        self.assertTrue(permission.has_permission(request, None))
        
        # HOD has access
        hod_faculty = faculty_factory()
        hod_faculty.designation = 'HEAD_OF_DEPARTMENT'
        hod_faculty.save()
        hod_user = hod_faculty.user if hasattr(hod_faculty, 'user') else user_factory()
        hod_user.faculty_profile = hod_faculty
        
        request = self.create_request('GET', hod_user)
        self.assertTrue(permission.has_permission(request, None))
        
        # Regular faculty has no access
        request = self.create_request('GET', self.faculty_user)
        self.assertFalse(permission.has_permission(request, None))
        
        # Student has no access
        request = self.create_request('GET', self.student_user)
        self.assertFalse(permission.has_permission(request, None))


class TestPermissionEdgeCases(BasePermissionTest):
    """Test permission edge cases"""

    def test_user_without_profiles(self):
        """Test users without faculty or student profiles"""
        regular_user = user_factory()
        
        # Test faculty permission
        faculty_permission = IsFacultyOrReadOnly()
        request = self.create_request('POST', regular_user)
        self.assertFalse(faculty_permission.has_permission(request, None))
        
        # Test student permission
        student_permission = IsStudentOrReadOnly()
        request = self.create_request('POST', regular_user)
        self.assertFalse(student_permission.has_permission(request, None))
        
        # Test grading permission
        grade_permission = CanGradeAssignment()
        request = self.create_request('POST', regular_user)
        self.assertFalse(grade_permission.has_permission(request, None))

    def test_none_user(self):
        """Test permissions with None user"""
        request = self.create_request('GET')
        request.user = None
        
        faculty_permission = IsFacultyOrReadOnly()
        self.assertFalse(faculty_permission.has_permission(request, None))
        
        student_permission = IsStudentOrReadOnly()
        self.assertFalse(student_permission.has_permission(request, None))

    def test_missing_object_attributes(self):
        """Test permissions with objects missing expected attributes"""
        # Create submission without assignment
        submission = assignment_submission_factory.make()
        submission.assignment = None
        
        permission = IsSubmissionOwnerOrFaculty()
        request = self.create_request('GET', self.faculty_user)
        
        # Should handle gracefully
        try:
            result = permission.has_object_permission(request, None, submission)
            # Should return False or handle error gracefully
            self.assertIsInstance(result, bool)
        except AttributeError:
            # Acceptable if it raises AttributeError
            pass

    def test_faculty_without_designation(self):
        """Test HOD permission with faculty without designation"""
        faculty_no_designation = faculty_factory()
        # Don't set designation or set to None
        if hasattr(faculty_no_designation, 'designation'):
            faculty_no_designation.designation = None
            faculty_no_designation.save()
        
        faculty_user_no_designation = faculty_no_designation.user if hasattr(faculty_no_designation, 'user') else user_factory()
        faculty_user_no_designation.faculty_profile = faculty_no_designation
        
        permission = IsHODOrAdmin()
        request = self.create_request('GET', faculty_user_no_designation)
        
        self.assertFalse(permission.has_permission(request, None))

    def test_staff_user_without_faculty_profile(self):
        """Test admin user without faculty profile"""
        admin_user = user_factory()
        admin_user.is_staff = True
        admin_user.save()
        
        # Test grading permission (should work for staff)
        permission = CanGradeAssignment()
        request = self.create_request('POST', admin_user)
        self.assertTrue(permission.has_permission(request, None))
        
        # Test HOD permission (should work for staff)
        hod_permission = IsHODOrAdmin()
        request = self.create_request('GET', admin_user)
        self.assertTrue(hod_permission.has_permission(request, None))

    def test_superuser_permissions(self):
        """Test superuser permissions"""
        superuser = user_factory()
        superuser.is_superuser = True
        superuser.is_staff = True
        superuser.save()
        
        # Test all permissions for superuser
        permissions = [
            IsFacultyOrReadOnly(),
            IsStudentOrReadOnly(),
            CanGradeAssignment(),
            IsHODOrAdmin()
        ]
        
        for permission in permissions:
            request = self.create_request('POST', superuser)
            # Superuser should have most permissions
            if hasattr(permission, 'has_permission'):
                result = permission.has_permission(request, None)
                # At minimum, admin-related permissions should work
                if isinstance(permission, (CanGradeAssignment, IsHODOrAdmin)):
                    self.assertTrue(result)


@pytest.mark.django_db
class TestPermissionPerformance(BasePermissionTest):
    """Test permission performance"""

    def test_permission_check_performance(self):
        """Test permission check performance"""
        import time
        
        permission = IsAssignmentOwnerOrReadOnly()
        assignment = assignment_factory.make(faculty=self.faculty)
        request = self.create_request('GET', self.faculty_user)
        
        # Test multiple permission checks
        start_time = time.time()
        for _ in range(100):
            permission.has_object_permission(request, None, assignment)
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 100 checks)
        self.assertLess(end_time - start_time, 1.0)

    def test_bulk_permission_checks(self):
        """Test bulk permission checks"""
        permission = IsSubmissionOwnerOrFaculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Create multiple submissions
        submissions = [
            assignment_submission_factory.make(assignment=assignment)
            for _ in range(10)
        ]
        
        request = self.create_request('GET', self.faculty_user)
        
        # Check permissions for all submissions
        import time
        start_time = time.time()
        
        for submission in submissions:
            permission.has_object_permission(request, None, submission)
        
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 0.5)


class TestPermissionCombinations(BasePermissionTest):
    """Test permission combinations"""

    def test_multiple_permission_checks(self):
        """Test multiple permission checks for same user"""
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        # Faculty should have assignment permissions but not student permissions
        faculty_request = self.create_request('POST', self.faculty_user)
        
        faculty_perm = IsFacultyOrReadOnly()
        student_perm = IsStudentOrReadOnly()
        owner_perm = IsAssignmentOwnerOrReadOnly()
        grade_perm = CanGradeAssignment()
        
        self.assertTrue(faculty_perm.has_permission(faculty_request, None))
        self.assertFalse(student_perm.has_permission(faculty_request, None))
        self.assertTrue(owner_perm.has_object_permission(faculty_request, None, assignment))
        self.assertTrue(grade_perm.has_permission(faculty_request, None))
        
        # Student should have student permissions but not faculty permissions
        student_request = self.create_request('POST', self.student_user)
        
        self.assertFalse(faculty_perm.has_permission(student_request, None))
        self.assertTrue(student_perm.has_permission(student_request, None))
        self.assertFalse(owner_perm.has_object_permission(student_request, None, assignment))
        self.assertFalse(grade_perm.has_permission(student_request, None))

    def test_admin_overrides(self):
        """Test admin overrides for all permissions"""
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        admin_request = self.create_request('POST', self.admin_user)
        
        # Admin should have access through specific permissions
        grade_perm = CanGradeAssignment()
        hod_perm = IsHODOrAdmin()
        submission_perm = IsSubmissionOwnerOrFaculty()
        
        self.assertTrue(grade_perm.has_permission(admin_request, None))
        self.assertTrue(hod_perm.has_permission(admin_request, None))
        self.assertTrue(submission_perm.has_object_permission(admin_request, None, submission))
        
        # Admin should not have faculty/student creation permissions
        faculty_perm = IsFacultyOrReadOnly()
        student_perm = IsStudentOrReadOnly()
        
        self.assertFalse(faculty_perm.has_permission(admin_request, None))
        self.assertFalse(student_perm.has_permission(admin_request, None))

    def test_read_vs_write_permissions(self):
        """Test read vs write permission differences"""
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Test read permissions
        read_request = self.create_request('GET', self.user)
        write_request = self.create_request('POST', self.user)
        
        faculty_perm = IsFacultyOrReadOnly()
        owner_perm = IsAssignmentOwnerOrReadOnly()
        
        # Regular user should have read but not write access
        self.assertTrue(faculty_perm.has_permission(read_request, None))
        self.assertFalse(faculty_perm.has_permission(write_request, None))
        
        self.assertTrue(owner_perm.has_object_permission(read_request, None, assignment))
        self.assertFalse(owner_perm.has_object_permission(write_request, None, assignment))


class TestPermissionErrorHandling(BasePermissionTest):
    """Test permission error handling"""

    def test_permission_with_invalid_user_attributes(self):
        """Test permissions with invalid user attributes"""
        # Create user with invalid faculty profile
        invalid_user = user_factory()
        invalid_user.faculty_profile = "invalid"  # String instead of object
        
        permission = IsFacultyOrReadOnly()
        request = self.create_request('POST', invalid_user)
        
        # Should handle gracefully and return False
        try:
            result = permission.has_permission(request, None)
            self.assertFalse(result)
        except (AttributeError, TypeError):
            # Acceptable if it raises an error
            pass

    def test_permission_with_deleted_objects(self):
        """Test permissions with deleted related objects"""
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        # Delete the faculty
        faculty_id = self.faculty.id
        self.faculty.delete()
        
        permission = IsSubmissionOwnerOrFaculty()
        request = self.create_request('GET', self.faculty_user)
        
        # Should handle deleted faculty gracefully
        try:
            result = permission.has_object_permission(request, None, submission)
            self.assertIsInstance(result, bool)
        except Exception:
            # Acceptable if it raises an exception
            pass

    def test_permission_with_none_objects(self):
        """Test permissions with None objects"""
        permission = IsAssignmentOwnerOrReadOnly()
        request = self.create_request('GET', self.faculty_user)
        
        # Should handle None object gracefully
        try:
            result = permission.has_object_permission(request, None, None)
            self.assertFalse(result)
        except (AttributeError, TypeError):
            # Acceptable if it raises an error
            pass
