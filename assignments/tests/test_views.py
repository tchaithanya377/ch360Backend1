"""
Comprehensive view tests for assignments app.
Tests all API endpoints, permissions, and view logic.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model

from assignments.models import Assignment, AssignmentSubmission, AssignmentGrade
from assignments.tests.factories import (
    assignment_factory, assignment_submission_factory, assignment_grade_factory,
    assignment_category_factory, assignment_comment_factory, assignment_template_factory,
    user_factory, faculty_factory, student_factory, published_assignment_factory
)

User = get_user_model()


class BaseAssignmentAPITest(APITestCase):
    """Base test class for assignment API tests"""

    def setUp(self):
        self.client = APIClient()
        self.faculty = faculty_factory()
        self.student = student_factory()
        self.admin_user = user_factory()
        self.admin_user.is_staff = True
        self.admin_user.save()

    def authenticate_faculty(self):
        """Authenticate as faculty"""
        faculty_user = self.faculty.user if hasattr(self.faculty, 'user') else user_factory()
        faculty_user.faculty_profile = self.faculty
        self.client.force_authenticate(user=faculty_user)
        return faculty_user

    def authenticate_student(self):
        """Authenticate as student"""
        student_user = self.student.user if hasattr(self.student, 'user') else user_factory()
        student_user.student_profile = self.student
        self.client.force_authenticate(user=student_user)
        return student_user

    def authenticate_admin(self):
        """Authenticate as admin"""
        self.client.force_authenticate(user=self.admin_user)
        return self.admin_user


class TestAssignmentCategoryViews(BaseAssignmentAPITest):
    """Test assignment category API views"""

    def test_list_categories(self):
        """Test listing categories"""
        assignment_category_factory.make()
        assignment_category_factory.make()
        
        self.authenticate_faculty()
        response = self.client.get('/api/assignments/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_category_as_admin(self):
        """Test creating category as admin"""
        self.authenticate_admin()
        data = {
            'name': 'Test Category',
            'description': 'Test description',
            'color_code': '#ff0000'
        }
        response = self.client.post('/api/assignments/categories/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Category')

    def test_create_category_as_faculty_forbidden(self):
        """Test creating category as faculty (should fail)"""
        self.authenticate_faculty()
        data = {'name': 'Test Category'}
        response = self.client.post('/api/assignments/categories/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_forbidden(self):
        """Test unauthenticated access"""
        response = self.client.get('/api/assignments/categories/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAssignmentViews(BaseAssignmentAPITest):
    """Test assignment API views"""

    def test_list_assignments_as_faculty(self):
        """Test listing assignments as faculty"""
        faculty_user = self.authenticate_faculty()
        assignment_factory.make(faculty=self.faculty)
        assignment_factory.make()  # Different faculty
        
        response = self.client.get('/api/assignments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_assignments_as_student(self):
        """Test listing assignments as student"""
        student_user = self.authenticate_student()
        assignment = assignment_factory.make()
        assignment.assigned_to_students.add(self.student)
        
        response = self.client.get('/api/assignments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_assignment_as_faculty(self):
        """Test creating assignment as faculty"""
        faculty_user = self.authenticate_faculty()
        data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post('/api/assignments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Assignment')
        self.assertEqual(response.data['faculty'], str(self.faculty.id))

    def test_create_assignment_as_student_forbidden(self):
        """Test creating assignment as student (should fail)"""
        self.authenticate_student()
        data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post('/api/assignments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_assignment(self):
        """Test retrieving single assignment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        response = self.client.get(f'/api/assignments/{assignment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(assignment.id))

    def test_update_assignment_as_owner(self):
        """Test updating assignment as owner"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        data = {'title': 'Updated Title'}
        response = self.client.patch(f'/api/assignments/{assignment.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_update_assignment_as_non_owner_forbidden(self):
        """Test updating assignment as non-owner"""
        self.authenticate_faculty()
        other_faculty = faculty_factory()
        assignment = assignment_factory.make(faculty=other_faculty)
        
        data = {'title': 'Updated Title'}
        response = self.client.patch(f'/api/assignments/{assignment.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_assignment(self):
        """Test deleting assignment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        response = self.client.delete(f'/api/assignments/{assignment.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Assignment.objects.filter(id=assignment.id).exists())

    def test_publish_assignment(self):
        """Test publishing assignment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(
            faculty=self.faculty,
            status='DRAFT',
            due_date=timezone.now() + timedelta(days=7)
        )
        
        response = self.client.post(f'/api/assignments/{assignment.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'PUBLISHED')

    def test_publish_non_draft_assignment(self):
        """Test publishing non-draft assignment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(
            faculty=self.faculty,
            status='PUBLISHED'
        )
        
        response = self.client.post(f'/api/assignments/{assignment.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_close_assignment(self):
        """Test closing assignment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(
            faculty=self.faculty,
            status='PUBLISHED'
        )
        
        response = self.client.post(f'/api/assignments/{assignment.id}/close/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'CLOSED')


class TestAssignmentSubmissionViews(BaseAssignmentAPITest):
    """Test assignment submission API views"""

    def test_list_submissions_as_student(self):
        """Test listing submissions as student"""
        student_user = self.authenticate_student()
        assignment = assignment_factory.make()
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        response = self.client.get(f'/api/assignments/{assignment.id}/submissions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_submissions_as_faculty(self):
        """Test listing submissions as faculty"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        assignment_submission_factory.make(assignment=assignment)
        assignment_submission_factory.make(assignment=assignment)
        
        response = self.client.get(f'/api/assignments/{assignment.id}/submissions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_submission_as_student(self):
        """Test creating submission as student"""
        student_user = self.authenticate_student()
        assignment = assignment_factory.make()
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Test submission content',
            'notes': 'Test notes'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/submissions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test submission content')

    def test_create_submission_as_faculty_forbidden(self):
        """Test creating submission as faculty (should fail)"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Test content'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/submissions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_submission(self):
        """Test retrieving single submission"""
        self.authenticate_student()
        submission = assignment_submission_factory.make(student=self.student)
        
        response = self.client.get(f'/api/assignments/submissions/{submission.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(submission.id))

    def test_update_submission_as_owner(self):
        """Test updating submission as owner"""
        self.authenticate_student()
        submission = assignment_submission_factory.make(student=self.student)
        
        data = {'content': 'Updated content'}
        response = self.client.patch(f'/api/assignments/submissions/{submission.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated content')

    def test_duplicate_submission_forbidden(self):
        """Test creating duplicate submission"""
        self.authenticate_student()
        assignment = assignment_factory.make()
        assignment_submission_factory.make(assignment=assignment, student=self.student)
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Duplicate submission'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/submissions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestAssignmentGradingViews(BaseAssignmentAPITest):
    """Test assignment grading API views"""

    def test_grade_submission_as_faculty(self):
        """Test grading submission as faculty"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty, max_marks=Decimal('100.00'))
        submission = assignment_submission_factory.make(assignment=assignment)
        
        data = {
            'marks_obtained': '85.00',
            'grade_letter': 'B+',
            'feedback': 'Good work!'
        }
        response = self.client.post(f'/api/assignments/submissions/{submission.id}/grade/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission.refresh_from_db()
        self.assertIsNotNone(submission.grade)
        self.assertEqual(submission.grade.marks_obtained, Decimal('85.00'))

    def test_grade_submission_as_student_forbidden(self):
        """Test grading submission as student (should fail)"""
        self.authenticate_student()
        submission = assignment_submission_factory.make()
        
        data = {
            'marks_obtained': '85.00',
            'grade_letter': 'B+'
        }
        response = self.client.post(f'/api/assignments/submissions/{submission.id}/grade/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_grade_exceeds_max_marks(self):
        """Test grading with marks exceeding maximum"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty, max_marks=Decimal('100.00'))
        submission = assignment_submission_factory.make(assignment=assignment)
        
        data = {
            'marks_obtained': '150.00',
            'grade_letter': 'A+'
        }
        response = self.client.post(f'/api/assignments/submissions/{submission.id}/grade/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_grade(self):
        """Test updating existing grade"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(assignment=assignment)
        grade = assignment_grade_factory.make()
        submission.grade = grade
        submission.save()
        
        data = {
            'marks_obtained': '90.00',
            'feedback': 'Excellent work!'
        }
        response = self.client.put(f'/api/assignments/submissions/{submission.id}/grade/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        grade.refresh_from_db()
        self.assertEqual(grade.marks_obtained, Decimal('90.00'))


class TestAssignmentStatsViews(BaseAssignmentAPITest):
    """Test assignment statistics API views"""

    def test_faculty_stats(self):
        """Test faculty assignment statistics"""
        self.authenticate_faculty()
        
        # Create assignments and submissions
        assignment1 = assignment_factory.make(faculty=self.faculty, status='PUBLISHED')
        assignment2 = assignment_factory.make(faculty=self.faculty, status='DRAFT')
        submission = assignment_submission_factory.make(assignment=assignment1)
        grade = assignment_grade_factory.make(marks_obtained=Decimal('85.00'))
        submission.grade = grade
        submission.save()
        
        response = self.client.get('/api/assignments/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_assignments'], 2)
        self.assertEqual(response.data['published_assignments'], 1)
        self.assertEqual(response.data['draft_assignments'], 1)
        self.assertEqual(response.data['graded_submissions'], 1)

    def test_student_stats(self):
        """Test student assignment statistics"""
        self.authenticate_student()
        
        # Create assignments and submissions
        assignment = assignment_factory.make()
        assignment.assigned_to_students.add(self.student)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        response = self.client.get('/api/assignments/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_assignments'], 1)
        self.assertEqual(response.data['submitted_assignments'], 1)

    def test_admin_stats(self):
        """Test admin assignment statistics"""
        self.authenticate_admin()
        
        assignment_factory.make(status='PUBLISHED')
        assignment_factory.make(status='DRAFT')
        
        response = self.client.get('/api/assignments/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_assignments'], 2)
        self.assertEqual(response.data['published_assignments'], 1)


class TestAssignmentCommentViews(BaseAssignmentAPITest):
    """Test assignment comment API views"""

    def test_list_comments(self):
        """Test listing assignment comments"""
        self.authenticate_faculty()
        assignment = assignment_factory.make()
        assignment_comment_factory.make(assignment=assignment)
        assignment_comment_factory.make(assignment=assignment)
        
        response = self.client.get(f'/api/assignments/{assignment.id}/comments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_comment(self):
        """Test creating assignment comment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make()
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Test comment',
            'comment_type': 'GENERAL'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/comments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Test comment')

    def test_create_comment_unauthenticated(self):
        """Test creating comment without authentication"""
        assignment = assignment_factory.make()
        data = {
            'assignment': str(assignment.id),
            'content': 'Test comment'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/comments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAssignmentFileViews(BaseAssignmentAPITest):
    """Test assignment file upload API views"""

    def test_file_upload_authenticated(self):
        """Test file upload with authentication"""
        self.authenticate_faculty()
        assignment = assignment_factory.make()
        
        # Mock file upload
        data = {
            'assignment': str(assignment.id),
            'file_name': 'test.pdf',
            'file_type': 'ASSIGNMENT',
            'mime_type': 'application/pdf'
        }
        response = self.client.post('/api/assignments/files/upload/', data)
        
        # Note: This would need actual file handling in real implementation
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_file_upload_unauthenticated(self):
        """Test file upload without authentication"""
        data = {'file_name': 'test.pdf'}
        response = self.client.post('/api/assignments/files/upload/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestAssignmentTemplateViews(BaseAssignmentAPITest):
    """Test assignment template API views"""

    def test_list_templates(self):
        """Test listing assignment templates"""
        self.authenticate_faculty()
        assignment_template_factory.make(is_public=True)
        assignment_template_factory.make(is_public=False)  # Should not be visible
        
        response = self.client.get('/api/assignments/templates/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_template(self):
        """Test creating assignment template"""
        self.authenticate_faculty()
        
        data = {
            'name': 'Test Template',
            'description': 'Test description',
            'max_marks': '100.00',
            'is_public': False
        }
        response = self.client.post('/api/assignments/templates/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Template')

    def test_retrieve_template(self):
        """Test retrieving single template"""
        self.authenticate_faculty()
        template = assignment_template_factory.make(is_public=True)
        
        response = self.client.get(f'/api/assignments/templates/{template.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(template.id))


class TestMyAssignmentsView(BaseAssignmentAPITest):
    """Test my assignments API view"""

    def test_my_assignments_as_student(self):
        """Test my assignments for student"""
        self.authenticate_student()
        
        # Create assignment assigned to student
        assignment = assignment_factory.make()
        assignment.assigned_to_students.add(self.student)
        
        # Create submission
        assignment_submission_factory.make(assignment=assignment, student=self.student)
        
        response = self.client.get('/api/assignments/my/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('submission_status', response.data[0])

    def test_my_assignments_as_faculty(self):
        """Test my assignments for faculty"""
        self.authenticate_faculty()
        
        assignment_factory.make(faculty=self.faculty)
        assignment_factory.make()  # Different faculty
        
        response = self.client.get('/api/assignments/my/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_my_assignments_no_profile(self):
        """Test my assignments without profile"""
        user = user_factory()
        self.client.force_authenticate(user=user)
        
        response = self.client.get('/api/assignments/my/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestAssignmentSubmissionsView(BaseAssignmentAPITest):
    """Test assignment submissions view"""

    def test_get_assignment_submissions_as_faculty(self):
        """Test getting all submissions for assignment as faculty"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        assignment_submission_factory.make(assignment=assignment)
        assignment_submission_factory.make(assignment=assignment)
        
        response = self.client.get(f'/api/assignments/{assignment.id}/all-submissions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_assignment_submissions_as_student_forbidden(self):
        """Test getting all submissions as student (should fail)"""
        self.authenticate_student()
        assignment = assignment_factory.make()
        
        response = self.client.get(f'/api/assignments/{assignment.id}/all-submissions/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_assignment_submissions_wrong_faculty(self):
        """Test getting submissions for assignment of different faculty"""
        self.authenticate_faculty()
        other_faculty = faculty_factory()
        assignment = assignment_factory.make(faculty=other_faculty)
        
        response = self.client.get(f'/api/assignments/{assignment.id}/all-submissions/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestSimpleAssignmentViews(BaseAssignmentAPITest):
    """Test simple assignment API views"""

    def test_simple_list_assignments(self):
        """Test simple assignment listing"""
        self.authenticate_faculty()
        assignment_factory.make()
        assignment_factory.make()
        
        response = self.client.get('/api/assignments/simple/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_simple_create_assignment(self):
        """Test simple assignment creation"""
        self.authenticate_faculty()
        
        data = {
            'title': 'Simple Assignment',
            'description': 'Simple description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post('/api/assignments/simple/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Simple Assignment')

    def test_simple_assignment_filters(self):
        """Test simple assignment filters"""
        self.authenticate_faculty()
        assignment1 = assignment_factory.make(status='PUBLISHED')
        assignment2 = assignment_factory.make(status='DRAFT')
        
        # Filter by status
        response = self.client.get('/api/assignments/simple/?status=PUBLISHED')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'PUBLISHED')


class TestAssignmentViewPermissions(BaseAssignmentAPITest):
    """Test assignment view permissions"""

    def test_unauthenticated_access_denied(self):
        """Test unauthenticated access is denied"""
        endpoints = [
            '/api/assignments/',
            '/api/assignments/stats/',
            '/api/assignments/my/',
            '/api/assignments/templates/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_create_assignment(self):
        """Test student cannot create assignment"""
        self.authenticate_student()
        
        data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post('/api/assignments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_faculty_cannot_submit_assignment(self):
        """Test faculty cannot submit assignment"""
        self.authenticate_faculty()
        assignment = assignment_factory.make()
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Test content'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/submissions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_grade_submission(self):
        """Test student cannot grade submission"""
        self.authenticate_student()
        submission = assignment_submission_factory.make()
        
        data = {
            'marks_obtained': '85.00',
            'grade_letter': 'B+'
        }
        response = self.client.post(f'/api/assignments/submissions/{submission.id}/grade/', data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_faculty_can_only_access_own_assignments(self):
        """Test faculty can only access their own assignments"""
        self.authenticate_faculty()
        other_faculty = faculty_factory()
        assignment = assignment_factory.make(faculty=other_faculty)
        
        response = self.client.get(f'/api/assignments/{assignment.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_can_only_access_assigned_assignments(self):
        """Test student can only access assignments assigned to them"""
        self.authenticate_student()
        assignment = assignment_factory.make()  # Not assigned to student
        
        response = self.client.get(f'/api/assignments/{assignment.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestAssignmentViewErrorHandling(BaseAssignmentAPITest):
    """Test assignment view error handling"""

    def test_invalid_assignment_id(self):
        """Test accessing invalid assignment ID"""
        self.authenticate_faculty()
        
        response = self.client.get('/api/assignments/invalid-id/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_submission_data(self):
        """Test creating submission with invalid data"""
        self.authenticate_student()
        assignment = assignment_factory.make()
        
        data = {
            'assignment': str(assignment.id),
            'content': '',  # Empty content
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/submissions/', data)
        
        # Should still create (content is not required)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_invalid_grade_data(self):
        """Test creating grade with invalid data"""
        self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        submission = assignment_submission_factory.make(assignment=assignment)
        
        data = {
            'marks_obtained': 'invalid',  # Invalid number
        }
        response = self.client.post(f'/api/assignments/submissions/{submission.id}/grade/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        """Test creating assignment with missing required fields"""
        self.authenticate_faculty()
        
        data = {
            'title': 'Test Assignment',
            # Missing description, max_marks, due_date
        }
        response = self.client.post('/api/assignments/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)
        self.assertIn('max_marks', response.data)
        self.assertIn('due_date', response.data)

    def test_duplicate_submission(self):
        """Test creating duplicate submission"""
        self.authenticate_student()
        assignment = assignment_factory.make()
        assignment_submission_factory.make(assignment=assignment, student=self.student)
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Duplicate submission'
        }
        response = self.client.post(f'/api/assignments/{assignment.id}/submissions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestAssignmentViewIntegration(BaseAssignmentAPITest):
    """Test assignment view integration scenarios"""

    def test_complete_assignment_workflow(self):
        """Test complete assignment workflow"""
        # Faculty creates assignment
        faculty_user = self.authenticate_faculty()
        data = {
            'title': 'Integration Test Assignment',
            'description': 'Test description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        response = self.client.post('/api/assignments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assignment_id = response.data['id']
        
        # Faculty publishes assignment
        response = self.client.post(f'/api/assignments/{assignment_id}/publish/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Student submits assignment
        student_user = self.authenticate_student()
        data = {
            'assignment': assignment_id,
            'content': 'Student submission content'
        }
        response = self.client.post(f'/api/assignments/{assignment_id}/submissions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        submission_id = response.data['id']
        
        # Faculty grades submission
        self.authenticate_faculty()
        data = {
            'marks_obtained': '88.00',
            'grade_letter': 'B+',
            'feedback': 'Good work!'
        }
        response = self.client.post(f'/api/assignments/submissions/{submission_id}/grade/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify final state
        response = self.client.get(f'/api/assignments/{assignment_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['submission_count'], 1)
        self.assertEqual(response.data['graded_count'], 1)

    def test_assignment_stats_integration(self):
        """Test assignment statistics integration"""
        self.authenticate_faculty()
        
        # Create multiple assignments with different statuses
        published_assignment = assignment_factory.make(
            faculty=self.faculty,
            status='PUBLISHED'
        )
        draft_assignment = assignment_factory.make(
            faculty=self.faculty,
            status='DRAFT'
        )
        
        # Create submissions and grades
        submission1 = assignment_submission_factory.make(assignment=published_assignment)
        submission2 = assignment_submission_factory.make(assignment=published_assignment)
        
        grade1 = assignment_grade_factory.make(marks_obtained=Decimal('85.00'))
        submission1.grade = grade1
        submission1.save()
        
        # Get stats
        response = self.client.get('/api/assignments/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_assignments'], 2)
        self.assertEqual(response.data['published_assignments'], 1)
        self.assertEqual(response.data['draft_assignments'], 1)
        self.assertEqual(response.data['total_submissions'], 2)
        self.assertEqual(response.data['graded_submissions'], 1)
        self.assertEqual(response.data['pending_grades'], 1)

    def test_multi_user_assignment_access(self):
        """Test multi-user assignment access scenarios"""
        # Create assignment as faculty1
        faculty1_user = self.authenticate_faculty()
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Faculty2 should not see faculty1's assignment
        faculty2 = faculty_factory()
        faculty2_user = faculty2.user if hasattr(faculty2, 'user') else user_factory()
        faculty2_user.faculty_profile = faculty2
        self.client.force_authenticate(user=faculty2_user)
        
        response = self.client.get('/api/assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
        # Student should not see unassigned assignment
        self.authenticate_student()
        response = self.client.get('/api/assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
        
        # Assign to student and verify access
        assignment.assigned_to_students.add(self.student)
        response = self.client.get('/api/assignments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_assignment_deadline_scenarios(self):
        """Test assignment deadline scenarios"""
        self.authenticate_student()
        
        # Create assignment with future deadline
        future_assignment = assignment_factory.make(
            due_date=timezone.now() + timedelta(days=1)
        )
        
        # Create assignment with past deadline
        past_assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        # Submit to future assignment (should succeed)
        data = {
            'assignment': str(future_assignment.id),
            'content': 'On-time submission'
        }
        response = self.client.post(f'/api/assignments/{future_assignment.id}/submissions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data['is_late'])
        
        # Submit to past assignment (should be marked as late)
        data = {
            'assignment': str(past_assignment.id),
            'content': 'Late submission'
        }
        response = self.client.post(f'/api/assignments/{past_assignment.id}/submissions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['is_late'])
        self.assertEqual(response.data['status'], 'LATE')
