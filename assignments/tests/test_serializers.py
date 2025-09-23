"""
Comprehensive serializer tests for assignments app.
Tests all serializers, validation, and serialization logic.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from assignments.serializers import (
    AssignmentCategorySerializer, AssignmentFileSerializer, AssignmentCommentSerializer,
    AssignmentGradeSerializer, AssignmentSubmissionSerializer, AssignmentSubmissionCreateSerializer,
    AssignmentSerializer, AssignmentCreateSerializer, AssignmentGroupSerializer,
    AssignmentTemplateSerializer, AssignmentTemplateCreateSerializer, AssignmentStatsSerializer,
    StudentAssignmentStatsSerializer, FacultyAssignmentStatsSerializer, AssignmentRubricSerializer,
    AssignmentRubricGradeSerializer, AssignmentPeerReviewSerializer, AssignmentPlagiarismCheckSerializer,
    AssignmentLearningOutcomeSerializer, AssignmentAnalyticsSerializer, AssignmentNotificationSerializer,
    AssignmentScheduleSerializer, SimpleAssignmentSerializer, SimpleAssignmentCreateSerializer
)
from assignments.tests.factories import (
    assignment_category_factory, assignment_factory, assignment_submission_factory,
    assignment_file_factory, assignment_grade_factory, assignment_comment_factory,
    assignment_group_factory, assignment_template_factory, assignment_rubric_factory,
    assignment_rubric_grade_factory, assignment_peer_review_factory,
    assignment_plagiarism_check_factory, assignment_learning_outcome_factory,
    assignment_analytics_factory, assignment_notification_factory,
    assignment_schedule_factory, user_factory, faculty_factory, student_factory
)


class TestAssignmentCategorySerializer(TestCase):
    """Test AssignmentCategorySerializer"""

    def test_serialization(self):
        """Test serializing assignment category"""
        category = assignment_category_factory.make()
        serializer = AssignmentCategorySerializer(category)
        data = serializer.data
        
        self.assertEqual(data['id'], str(category.id))
        self.assertEqual(data['name'], category.name)
        self.assertEqual(data['description'], category.description)
        self.assertEqual(data['color_code'], category.color_code)
        self.assertEqual(data['is_active'], category.is_active)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_deserialization(self):
        """Test deserializing assignment category"""
        data = {
            'name': 'Test Category',
            'description': 'Test description',
            'color_code': '#ff0000',
            'is_active': True
        }
        serializer = AssignmentCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.description, 'Test description')
        self.assertEqual(category.color_code, '#ff0000')
        self.assertTrue(category.is_active)

    def test_validation(self):
        """Test serializer validation"""
        # Test required fields
        serializer = AssignmentCategorySerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

        # Test valid data
        data = {
            'name': 'Valid Category',
            'description': 'Valid description',
            'color_code': '#00ff00',
            'is_active': True
        }
        serializer = AssignmentCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())


class TestAssignmentFileSerializer(TestCase):
    """Test AssignmentFileSerializer"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_serialization(self):
        """Test serializing assignment file"""
        file_obj = assignment_file_factory.make()
        request = self.factory.get('/')
        serializer = AssignmentFileSerializer(file_obj, context={'request': request})
        data = serializer.data
        
        self.assertEqual(data['id'], str(file_obj.id))
        self.assertEqual(data['file_name'], file_obj.file_name)
        self.assertEqual(data['file_type'], file_obj.file_type)
        self.assertEqual(data['file_size'], file_obj.file_size)
        self.assertEqual(data['mime_type'], file_obj.mime_type)
        self.assertIn('file_url', data)
        self.assertIn('file_size_mb', data)
        self.assertIn('uploaded_at', data)

    def test_file_url_method(self):
        """Test file_url method"""
        file_obj = assignment_file_factory.make()
        request = self.factory.get('/')
        serializer = AssignmentFileSerializer(file_obj, context={'request': request})
        data = serializer.data
        
        # Should return None if no file_path
        self.assertIsNone(data['file_url'])

    def test_file_size_mb_method(self):
        """Test file_size_mb method"""
        file_obj = assignment_file_factory.make(file_size=1048576)  # 1MB
        serializer = AssignmentFileSerializer(file_obj)
        data = serializer.data
        
        self.assertEqual(data['file_size_mb'], 1.0)

    def test_file_size_mb_zero(self):
        """Test file_size_mb with zero size"""
        file_obj = assignment_file_factory.make(file_size=0)
        serializer = AssignmentFileSerializer(file_obj)
        data = serializer.data
        
        self.assertEqual(data['file_size_mb'], 0)


class TestAssignmentCommentSerializer(TestCase):
    """Test AssignmentCommentSerializer"""

    def test_serialization(self):
        """Test serializing assignment comment"""
        comment = assignment_comment_factory.make()
        serializer = AssignmentCommentSerializer(comment)
        data = serializer.data
        
        self.assertEqual(data['id'], str(comment.id))
        self.assertEqual(data['assignment'], str(comment.assignment.id))
        self.assertEqual(data['author'], str(comment.author.id))
        self.assertEqual(data['content'], comment.content)
        self.assertEqual(data['comment_type'], comment.comment_type)
        self.assertIn('author_name', data)
        self.assertIn('replies', data)

    def test_author_name_field(self):
        """Test author_name field"""
        user = user_factory()
        comment = assignment_comment_factory.make(author=user)
        serializer = AssignmentCommentSerializer(comment)
        data = serializer.data
        
        self.assertEqual(data['author_name'], user.email)

    def test_replies_field(self):
        """Test replies field"""
        comment = assignment_comment_factory.make()
        # Add a reply
        reply = assignment_comment_factory.make(
            assignment=comment.assignment,
            parent_comment=comment
        )
        serializer = AssignmentCommentSerializer(comment)
        data = serializer.data
        
        self.assertIsInstance(data['replies'], list)
        self.assertEqual(len(data['replies']), 1)

    def test_deserialization(self):
        """Test deserializing assignment comment"""
        assignment = assignment_factory.make()
        user = user_factory()
        data = {
            'assignment': str(assignment.id),
            'content': 'Test comment',
            'comment_type': 'GENERAL'
        }
        serializer = AssignmentCommentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        comment = serializer.save(author=user)
        
        self.assertEqual(comment.assignment, assignment)
        self.assertEqual(comment.content, 'Test comment')
        self.assertEqual(comment.comment_type, 'GENERAL')
        self.assertEqual(comment.author, user)


class TestAssignmentGradeSerializer(TestCase):
    """Test AssignmentGradeSerializer"""

    def test_serialization(self):
        """Test serializing assignment grade"""
        grade = assignment_grade_factory.make()
        serializer = AssignmentGradeSerializer(grade)
        data = serializer.data
        
        self.assertEqual(data['id'], str(grade.id))
        self.assertEqual(data['marks_obtained'], str(grade.marks_obtained))
        self.assertEqual(data['grade_letter'], grade.grade_letter)
        self.assertEqual(data['feedback'], grade.feedback)
        self.assertIn('graded_by_name', data)
        self.assertIn('out_of_marks', data)
        self.assertIn('percentage', data)

    def test_graded_by_name_field(self):
        """Test graded_by_name field"""
        user = user_factory()
        grade = assignment_grade_factory.make(graded_by=user)
        serializer = AssignmentGradeSerializer(grade)
        data = serializer.data
        
        self.assertEqual(data['graded_by_name'], user.email)

    def test_percentage_method(self):
        """Test percentage calculation method"""
        # Create a submission with max_marks
        assignment = assignment_factory.make(max_marks=Decimal("100.00"))
        submission = assignment_submission_factory.make(assignment=assignment)
        grade = assignment_grade_factory.make(marks_obtained=Decimal("85.00"))
        grade.submission = submission
        grade.save()
        
        serializer = AssignmentGradeSerializer(grade)
        data = serializer.data
        
        self.assertEqual(data['percentage'], 85.0)

    def test_percentage_method_no_submission(self):
        """Test percentage method with no submission"""
        grade = assignment_grade_factory.make()
        serializer = AssignmentGradeSerializer(grade)
        data = serializer.data
        
        self.assertIsNone(data['percentage'])

    def test_deserialization(self):
        """Test deserializing assignment grade"""
        user = user_factory()
        data = {
            'marks_obtained': '90.00',
            'grade_letter': 'A',
            'feedback': 'Excellent work!'
        }
        serializer = AssignmentGradeSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        grade = serializer.save(graded_by=user)
        
        self.assertEqual(grade.marks_obtained, Decimal("90.00"))
        self.assertEqual(grade.grade_letter, 'A')
        self.assertEqual(grade.feedback, 'Excellent work!')
        self.assertEqual(grade.graded_by, user)


class TestAssignmentSubmissionSerializer(TestCase):
    """Test AssignmentSubmissionSerializer"""

    def test_serialization(self):
        """Test serializing assignment submission"""
        submission = assignment_submission_factory.make()
        serializer = AssignmentSubmissionSerializer(submission)
        data = serializer.data
        
        self.assertEqual(data['id'], str(submission.id))
        self.assertEqual(data['assignment'], str(submission.assignment.id))
        self.assertEqual(data['student'], str(submission.student.id))
        self.assertEqual(data['content'], submission.content)
        self.assertEqual(data['status'], submission.status)
        self.assertIn('student_name', data)
        self.assertIn('student_id', data)
        self.assertIn('grade', data)
        self.assertIn('files', data)

    def test_student_name_field(self):
        """Test student_name field"""
        student = student_factory()
        submission = assignment_submission_factory.make(student=student)
        serializer = AssignmentSubmissionSerializer(submission)
        data = serializer.data
        
        self.assertEqual(data['student_name'], student.name)

    def test_student_id_field(self):
        """Test student_id field"""
        student = student_factory()
        submission = assignment_submission_factory.make(student=student)
        serializer = AssignmentSubmissionSerializer(submission)
        data = serializer.data
        
        self.assertEqual(data['student_id'], student.apaar_student_id)

    def test_grade_field(self):
        """Test grade field"""
        submission = assignment_submission_factory.make()
        grade = assignment_grade_factory.make()
        submission.grade = grade
        submission.save()
        
        serializer = AssignmentSubmissionSerializer(submission)
        data = serializer.data
        
        self.assertIsNotNone(data['grade'])
        self.assertEqual(data['grade']['id'], str(grade.id))

    def test_files_field(self):
        """Test files field"""
        submission = assignment_submission_factory.make()
        file_obj = assignment_file_factory.make(
            assignment=submission.assignment,
            submission=submission
        )
        
        serializer = AssignmentSubmissionSerializer(submission)
        data = serializer.data
        
        self.assertIsInstance(data['files'], list)
        self.assertEqual(len(data['files']), 1)


class TestAssignmentSubmissionCreateSerializer(TestCase):
    """Test AssignmentSubmissionCreateSerializer"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_serialization(self):
        """Test serializing for creation"""
        assignment = assignment_factory.make()
        data = {
            'assignment': str(assignment.id),
            'content': 'Test submission content',
            'notes': 'Test notes',
            'attachment_files': []
        }
        serializer = AssignmentSubmissionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_method(self):
        """Test create method"""
        student = student_factory()
        assignment = assignment_factory.make()
        request = self.factory.post('/')
        request.user = student.user if hasattr(student, 'user') else user_factory()
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Test content',
            'notes': 'Test notes'
        }
        serializer = AssignmentSubmissionCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        submission = serializer.save()
        
        self.assertEqual(submission.assignment, assignment)
        self.assertEqual(submission.content, 'Test content')

    def test_create_method_no_student_profile(self):
        """Test create method without student profile"""
        assignment = assignment_factory.make()
        request = self.factory.post('/')
        request.user = user_factory()  # User without student profile
        
        data = {
            'assignment': str(assignment.id),
            'content': 'Test content'
        }
        serializer = AssignmentSubmissionCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(ValidationError):
            serializer.save()


class TestAssignmentSerializer(TestCase):
    """Test AssignmentSerializer"""

    def test_serialization(self):
        """Test serializing assignment"""
        assignment = assignment_factory.make()
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['id'], str(assignment.id))
        self.assertEqual(data['title'], assignment.title)
        self.assertEqual(data['description'], assignment.description)
        self.assertEqual(data['assignment_type'], assignment.assignment_type)
        self.assertEqual(data['max_marks'], str(assignment.max_marks))
        self.assertIn('faculty_name', data)
        self.assertIn('faculty_id', data)
        self.assertIn('category_name', data)
        self.assertIn('submission_count', data)
        self.assertIn('graded_count', data)
        self.assertIn('is_overdue', data)

    def test_faculty_name_field(self):
        """Test faculty_name field"""
        faculty = faculty_factory()
        assignment = assignment_factory.make(faculty=faculty)
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['faculty_name'], faculty.name)

    def test_faculty_id_field(self):
        """Test faculty_id field"""
        faculty = faculty_factory()
        assignment = assignment_factory.make(faculty=faculty)
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['faculty_id'], faculty.apaar_faculty_id)

    def test_category_name_field(self):
        """Test category_name field"""
        category = assignment_category_factory.make()
        assignment = assignment_factory.make(category=category)
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['category_name'], category.name)

    def test_submission_count_field(self):
        """Test submission_count field"""
        assignment = assignment_factory.make()
        assignment_submission_factory.make(assignment=assignment)
        assignment_submission_factory.make(assignment=assignment)
        
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['submission_count'], 2)

    def test_graded_count_field(self):
        """Test graded_count field"""
        assignment = assignment_factory.make()
        submission = assignment_submission_factory.make(assignment=assignment)
        grade = assignment_grade_factory.make()
        submission.grade = grade
        submission.save()
        
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['graded_count'], 1)

    def test_is_overdue_field(self):
        """Test is_overdue field"""
        assignment = assignment_factory.make(
            status="PUBLISHED",
            due_date=timezone.now() - timedelta(days=1)
        )
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertTrue(data['is_overdue'])

    def test_files_field(self):
        """Test files field"""
        assignment = assignment_factory.make()
        assignment_file_factory.make(assignment=assignment)
        
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertIsInstance(data['files'], list)
        self.assertEqual(len(data['files']), 1)

    def test_comments_field(self):
        """Test comments field"""
        assignment = assignment_factory.make()
        assignment_comment_factory.make(assignment=assignment)
        
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertIsInstance(data['comments'], list)
        self.assertEqual(len(data['comments']), 1)

    def test_submissions_field(self):
        """Test submissions field"""
        assignment = assignment_factory.make()
        assignment_submission_factory.make(assignment=assignment)
        
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertIsInstance(data['submissions'], list)
        self.assertEqual(len(data['submissions']), 1)


class TestAssignmentCreateSerializer(TestCase):
    """Test AssignmentCreateSerializer"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_serialization(self):
        """Test serializing for creation"""
        category = assignment_category_factory.make()
        data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'instructions': 'Test instructions',
            'category': str(category.id),
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'is_group_assignment': False,
            'max_group_size': 1
        }
        serializer = AssignmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_method(self):
        """Test create method"""
        faculty = faculty_factory()
        request = self.factory.post('/')
        request.user = faculty.user if hasattr(faculty, 'user') else user_factory()
        
        data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        serializer = AssignmentCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        assignment = serializer.save()
        
        self.assertEqual(assignment.title, 'Test Assignment')
        self.assertEqual(assignment.description, 'Test description')

    def test_create_method_no_faculty_profile(self):
        """Test create method without faculty profile"""
        request = self.factory.post('/')
        request.user = user_factory()  # User without faculty profile
        
        data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        serializer = AssignmentCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(ValidationError):
            serializer.save()


class TestAssignmentGroupSerializer(TestCase):
    """Test AssignmentGroupSerializer"""

    def test_serialization(self):
        """Test serializing assignment group"""
        group = assignment_group_factory.make()
        serializer = AssignmentGroupSerializer(group)
        data = serializer.data
        
        self.assertEqual(data['id'], str(group.id))
        self.assertEqual(data['assignment'], str(group.assignment.id))
        self.assertEqual(data['group_name'], group.group_name)
        self.assertEqual(data['leader'], str(group.leader.id))
        self.assertIn('assignment_title', data)
        self.assertIn('leader_name', data)
        self.assertIn('members_names', data)
        self.assertIn('member_count', data)

    def test_assignment_title_field(self):
        """Test assignment_title field"""
        assignment = assignment_factory.make(title="Test Assignment")
        group = assignment_group_factory.make(assignment=assignment)
        serializer = AssignmentGroupSerializer(group)
        data = serializer.data
        
        self.assertEqual(data['assignment_title'], "Test Assignment")

    def test_leader_name_field(self):
        """Test leader_name field"""
        student = student_factory()
        group = assignment_group_factory.make(leader=student)
        serializer = AssignmentGroupSerializer(group)
        data = serializer.data
        
        self.assertEqual(data['leader_name'], student.name)

    def test_member_count_method(self):
        """Test member_count method"""
        group = assignment_group_factory.make()
        # Add members
        students = [student_factory() for _ in range(3)]
        for student in students:
            group.members.add(student)
        
        serializer = AssignmentGroupSerializer(group)
        data = serializer.data
        
        self.assertEqual(data['member_count'], 3)

    def test_deserialization(self):
        """Test deserializing assignment group"""
        assignment = assignment_factory.make()
        student = student_factory()
        data = {
            'assignment': str(assignment.id),
            'group_name': 'Test Group',
            'leader': str(student.id)
        }
        serializer = AssignmentGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        group = serializer.save()
        
        self.assertEqual(group.assignment, assignment)
        self.assertEqual(group.group_name, 'Test Group')
        self.assertEqual(group.leader, student)


class TestAssignmentTemplateSerializer(TestCase):
    """Test AssignmentTemplateSerializer"""

    def test_serialization(self):
        """Test serializing assignment template"""
        template = assignment_template_factory.make()
        serializer = AssignmentTemplateSerializer(template)
        data = serializer.data
        
        self.assertEqual(data['id'], str(template.id))
        self.assertEqual(data['name'], template.name)
        self.assertEqual(data['description'], template.description)
        self.assertEqual(data['max_marks'], str(template.max_marks))
        self.assertIn('category_name', data)
        self.assertIn('created_by_name', data)

    def test_category_name_field(self):
        """Test category_name field"""
        category = assignment_category_factory.make()
        template = assignment_template_factory.make(category=category)
        serializer = AssignmentTemplateSerializer(template)
        data = serializer.data
        
        self.assertEqual(data['category_name'], category.name)

    def test_created_by_name_field(self):
        """Test created_by_name field"""
        user = user_factory()
        template = assignment_template_factory.make(created_by=user)
        serializer = AssignmentTemplateSerializer(template)
        data = serializer.data
        
        self.assertEqual(data['created_by_name'], user.email)

    def test_deserialization(self):
        """Test deserializing assignment template"""
        category = assignment_category_factory.make()
        data = {
            'name': 'Test Template',
            'description': 'Test description',
            'category': str(category.id),
            'max_marks': '100.00',
            'is_public': False
        }
        serializer = AssignmentTemplateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        template = serializer.save()
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.description, 'Test description')
        self.assertEqual(template.category, category)


class TestAssignmentTemplateCreateSerializer(TestCase):
    """Test AssignmentTemplateCreateSerializer"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_serialization(self):
        """Test serializing for creation"""
        category = assignment_category_factory.make()
        data = {
            'name': 'Test Template',
            'description': 'Test description',
            'category': str(category.id),
            'max_marks': '100.00',
            'is_public': False
        }
        serializer = AssignmentTemplateCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_create_method(self):
        """Test create method"""
        user = user_factory()
        request = self.factory.post('/')
        request.user = user
        
        data = {
            'name': 'Test Template',
            'description': 'Test description',
            'max_marks': '100.00'
        }
        serializer = AssignmentTemplateCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        template = serializer.save()
        
        self.assertEqual(template.name, 'Test Template')
        self.assertEqual(template.created_by, user)

    def test_create_method_no_user(self):
        """Test create method without user"""
        data = {
            'name': 'Test Template',
            'description': 'Test description',
            'max_marks': '100.00'
        }
        serializer = AssignmentTemplateCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        with self.assertRaises(ValidationError):
            serializer.save()


class TestStatsSerializers(TestCase):
    """Test statistics serializers"""

    def test_assignment_stats_serializer(self):
        """Test AssignmentStatsSerializer"""
        data = {
            'total_assignments': 10,
            'published_assignments': 8,
            'draft_assignments': 2,
            'overdue_assignments': 1,
            'total_submissions': 50,
            'graded_submissions': 40,
            'pending_grades': 10,
            'average_grade': Decimal('85.50')
        }
        serializer = AssignmentStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total_assignments'], 10)

    def test_student_assignment_stats_serializer(self):
        """Test StudentAssignmentStatsSerializer"""
        data = {
            'total_assignments': 5,
            'submitted_assignments': 4,
            'pending_assignments': 1,
            'late_submissions': 1,
            'average_grade': Decimal('88.00'),
            'total_marks_obtained': Decimal('350.00'),
            'total_max_marks': Decimal('400.00')
        }
        serializer = StudentAssignmentStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total_assignments'], 5)

    def test_faculty_assignment_stats_serializer(self):
        """Test FacultyAssignmentStatsSerializer"""
        data = {
            'total_assignments': 8,
            'published_assignments': 6,
            'draft_assignments': 2,
            'total_submissions': 40,
            'graded_submissions': 35,
            'pending_grades': 5,
            'average_grade': Decimal('82.50'),
            'overdue_assignments': 1
        }
        serializer = FacultyAssignmentStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total_assignments'], 8)


class TestAdvancedSerializers(TestCase):
    """Test advanced serializers"""

    def test_assignment_rubric_serializer(self):
        """Test AssignmentRubricSerializer"""
        rubric = assignment_rubric_factory.make()
        serializer = AssignmentRubricSerializer(rubric)
        data = serializer.data
        
        self.assertEqual(data['id'], str(rubric.id))
        self.assertEqual(data['name'], rubric.name)
        self.assertEqual(data['rubric_type'], rubric.rubric_type)
        self.assertEqual(data['total_points'], str(rubric.total_points))
        self.assertIn('created_by_name', data)

    def test_assignment_rubric_grade_serializer(self):
        """Test AssignmentRubricGradeSerializer"""
        rubric_grade = assignment_rubric_grade_factory.make()
        serializer = AssignmentRubricGradeSerializer(rubric_grade)
        data = serializer.data
        
        self.assertEqual(data['id'], str(rubric_grade.id))
        self.assertEqual(data['total_score'], str(rubric_grade.total_score))
        self.assertIn('graded_by_name', data)

    def test_assignment_peer_review_serializer(self):
        """Test AssignmentPeerReviewSerializer"""
        peer_review = assignment_peer_review_factory.make()
        serializer = AssignmentPeerReviewSerializer(peer_review)
        data = serializer.data
        
        self.assertEqual(data['id'], str(peer_review.id))
        self.assertEqual(data['content_rating'], peer_review.content_rating)
        self.assertEqual(data['overall_rating'], peer_review.overall_rating)
        self.assertIn('reviewer_name', data)
        self.assertIn('reviewee_name', data)

    def test_assignment_plagiarism_check_serializer(self):
        """Test AssignmentPlagiarismCheckSerializer"""
        plagiarism_check = assignment_plagiarism_check_factory.make()
        serializer = AssignmentPlagiarismCheckSerializer(plagiarism_check)
        data = serializer.data
        
        self.assertEqual(data['id'], str(plagiarism_check.id))
        self.assertEqual(data['status'], plagiarism_check.status)
        self.assertEqual(data['similarity_percentage'], str(plagiarism_check.similarity_percentage))
        self.assertIn('student_name', data)
        self.assertIn('assignment_title', data)

    def test_assignment_learning_outcome_serializer(self):
        """Test AssignmentLearningOutcomeSerializer"""
        learning_outcome = assignment_learning_outcome_factory.make()
        serializer = AssignmentLearningOutcomeSerializer(learning_outcome)
        data = serializer.data
        
        self.assertEqual(data['id'], str(learning_outcome.id))
        self.assertEqual(data['outcome_code'], learning_outcome.outcome_code)
        self.assertEqual(data['bloom_level'], learning_outcome.bloom_level)
        self.assertIn('assignment_title', data)

    def test_assignment_analytics_serializer(self):
        """Test AssignmentAnalyticsSerializer"""
        analytics = assignment_analytics_factory.make()
        serializer = AssignmentAnalyticsSerializer(analytics)
        data = serializer.data
        
        self.assertEqual(data['id'], str(analytics.id))
        self.assertEqual(data['submission_rate'], str(analytics.submission_rate))
        self.assertEqual(data['average_grade'], str(analytics.average_grade))
        self.assertIn('assignment_title', data)

    def test_assignment_notification_serializer(self):
        """Test AssignmentNotificationSerializer"""
        notification = assignment_notification_factory.make()
        serializer = AssignmentNotificationSerializer(notification)
        data = serializer.data
        
        self.assertEqual(data['id'], str(notification.id))
        self.assertEqual(data['notification_type'], notification.notification_type)
        self.assertEqual(data['title'], notification.title)
        self.assertIn('assignment_title', data)
        self.assertIn('recipient_name', data)

    def test_assignment_schedule_serializer(self):
        """Test AssignmentScheduleSerializer"""
        schedule = assignment_schedule_factory.make()
        serializer = AssignmentScheduleSerializer(schedule)
        data = serializer.data
        
        self.assertEqual(data['id'], str(schedule.id))
        self.assertEqual(data['name'], schedule.name)
        self.assertEqual(data['schedule_type'], schedule.schedule_type)
        self.assertIn('template_name', data)
        self.assertIn('created_by_name', data)


class TestSimpleSerializers(TestCase):
    """Test simple serializers"""

    def test_simple_assignment_serializer(self):
        """Test SimpleAssignmentSerializer"""
        assignment = assignment_factory.make()
        serializer = SimpleAssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['id'], str(assignment.id))
        self.assertEqual(data['title'], assignment.title)
        self.assertEqual(data['assignment_type'], assignment.assignment_type)
        self.assertIn('faculty_name', data)
        self.assertIn('department_name', data)
        self.assertIn('course_code', data)

    def test_simple_assignment_create_serializer(self):
        """Test SimpleAssignmentCreateSerializer"""
        data = {
            'title': 'Simple Assignment',
            'description': 'Simple description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'is_active': True
        }
        serializer = SimpleAssignmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_simple_assignment_create_method(self):
        """Test SimpleAssignmentCreateSerializer create method"""
        faculty = faculty_factory()
        request = self.factory.post('/')
        request.user = faculty.user if hasattr(faculty, 'user') else user_factory()
        
        data = {
            'title': 'Simple Assignment',
            'description': 'Simple description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        serializer = SimpleAssignmentCreateSerializer(
            data=data, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())
        assignment = serializer.save()
        
        self.assertEqual(assignment.title, 'Simple Assignment')
        self.assertEqual(assignment.faculty, faculty)

    def test_section_display_method(self):
        """Test section_display method"""
        assignment = assignment_factory.make()
        serializer = SimpleAssignmentSerializer(assignment)
        data = serializer.data
        
        # Should return None if no course_section
        self.assertIsNone(data['section_display'])


class TestSerializerValidation(TestCase):
    """Test serializer validation"""

    def test_assignment_validation(self):
        """Test assignment serializer validation"""
        # Test required fields
        serializer = AssignmentCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)
        self.assertIn('description', serializer.errors)
        self.assertIn('max_marks', serializer.errors)
        self.assertIn('due_date', serializer.errors)

        # Test valid data
        data = {
            'title': 'Valid Assignment',
            'description': 'Valid description',
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat()
        }
        serializer = AssignmentCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_submission_validation(self):
        """Test submission serializer validation"""
        # Test required fields
        serializer = AssignmentSubmissionCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        data = {
            'assignment': str(assignment.id),
            'content': 'Valid content'
        }
        serializer = AssignmentSubmissionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_grade_validation(self):
        """Test grade serializer validation"""
        # Test required fields
        serializer = AssignmentGradeSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('marks_obtained', serializer.errors)

        # Test valid data
        data = {
            'marks_obtained': '85.00',
            'grade_letter': 'B+',
            'feedback': 'Good work!'
        }
        serializer = AssignmentGradeSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_comment_validation(self):
        """Test comment serializer validation"""
        # Test required fields
        serializer = AssignmentCommentSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)
        self.assertIn('content', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        data = {
            'assignment': str(assignment.id),
            'content': 'Valid comment'
        }
        serializer = AssignmentCommentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_group_validation(self):
        """Test group serializer validation"""
        # Test required fields
        serializer = AssignmentGroupSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)
        self.assertIn('group_name', serializer.errors)
        self.assertIn('leader', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        student = student_factory()
        data = {
            'assignment': str(assignment.id),
            'group_name': 'Valid Group',
            'leader': str(student.id)
        }
        serializer = AssignmentGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_template_validation(self):
        """Test template serializer validation"""
        # Test required fields
        serializer = AssignmentTemplateCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('description', serializer.errors)
        self.assertIn('max_marks', serializer.errors)

        # Test valid data
        data = {
            'name': 'Valid Template',
            'description': 'Valid description',
            'max_marks': '100.00'
        }
        serializer = AssignmentTemplateCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_rubric_validation(self):
        """Test rubric serializer validation"""
        # Test required fields
        serializer = AssignmentRubricSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('description', serializer.errors)
        self.assertIn('total_points', serializer.errors)

        # Test valid data
        data = {
            'name': 'Valid Rubric',
            'description': 'Valid description',
            'rubric_type': 'ANALYTIC',
            'total_points': '100.00'
        }
        serializer = AssignmentRubricSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_peer_review_validation(self):
        """Test peer review serializer validation"""
        # Test required fields
        serializer = AssignmentPeerReviewSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)
        self.assertIn('reviewer', serializer.errors)
        self.assertIn('reviewee', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        reviewer = student_factory()
        reviewee = student_factory()
        submission = assignment_submission_factory.make(assignment=assignment, student=reviewee)
        data = {
            'assignment': str(assignment.id),
            'reviewer': str(reviewer.id),
            'reviewee': str(reviewee.id),
            'submission': str(submission.id),
            'content_rating': 4,
            'clarity_rating': 3,
            'creativity_rating': 4,
            'overall_rating': 4,
            'strengths': 'Good content',
            'improvements': 'Could be clearer'
        }
        serializer = AssignmentPeerReviewSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_learning_outcome_validation(self):
        """Test learning outcome serializer validation"""
        # Test required fields
        serializer = AssignmentLearningOutcomeSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)
        self.assertIn('outcome_code', serializer.errors)
        self.assertIn('description', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        data = {
            'assignment': str(assignment.id),
            'outcome_code': 'LO1',
            'description': 'Valid outcome',
            'bloom_level': 'APPLY',
            'weight': '25.00'
        }
        serializer = AssignmentLearningOutcomeSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_analytics_validation(self):
        """Test analytics serializer validation"""
        # Test required fields
        serializer = AssignmentAnalyticsSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        data = {
            'assignment': str(assignment.id),
            'total_expected_submissions': 30,
            'actual_submissions': 25,
            'submission_rate': '83.33'
        }
        serializer = AssignmentAnalyticsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_notification_validation(self):
        """Test notification serializer validation"""
        # Test required fields
        serializer = AssignmentNotificationSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('assignment', serializer.errors)
        self.assertIn('recipient', serializer.errors)
        self.assertIn('notification_type', serializer.errors)
        self.assertIn('title', serializer.errors)
        self.assertIn('message', serializer.errors)

        # Test valid data
        assignment = assignment_factory.make()
        user = user_factory()
        data = {
            'assignment': str(assignment.id),
            'recipient': str(user.id),
            'notification_type': 'ASSIGNMENT_CREATED',
            'title': 'New Assignment',
            'message': 'A new assignment has been created'
        }
        serializer = AssignmentNotificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_schedule_validation(self):
        """Test schedule serializer validation"""
        # Test required fields
        serializer = AssignmentScheduleSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('template', serializer.errors)
        self.assertIn('schedule_type', serializer.errors)

        # Test valid data
        template = assignment_template_factory.make()
        data = {
            'name': 'Valid Schedule',
            'template': str(template.id),
            'schedule_type': 'WEEKLY',
            'interval_days': 7,
            'is_active': True,
            'start_date': timezone.now().isoformat()
        }
        serializer = AssignmentScheduleSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class TestSerializerEdgeCases(TestCase):
    """Test serializer edge cases"""

    def test_serializer_with_none_values(self):
        """Test serializers with None values"""
        # Test assignment with None category
        assignment = assignment_factory.make(category=None)
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertIsNone(data['category'])
        self.assertIsNone(data['category_name'])

        # Test submission with None grade
        submission = assignment_submission_factory.make(grade=None)
        serializer = AssignmentSubmissionSerializer(submission)
        data = serializer.data
        
        self.assertIsNone(data['grade'])

    def test_serializer_with_empty_relationships(self):
        """Test serializers with empty relationships"""
        # Test assignment with no submissions
        assignment = assignment_factory.make()
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['submission_count'], 0)
        self.assertEqual(data['graded_count'], 0)
        self.assertEqual(len(data['submissions']), 0)
        self.assertEqual(len(data['files']), 0)
        self.assertEqual(len(data['comments']), 0)

    def test_serializer_with_large_data(self):
        """Test serializers with large data sets"""
        # Test assignment with many submissions
        assignment = assignment_factory.make()
        for _ in range(10):
            assignment_submission_factory.make(assignment=assignment)
        
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        
        self.assertEqual(data['submission_count'], 10)
        self.assertEqual(len(data['submissions']), 10)

    def test_serializer_performance(self):
        """Test serializer performance with complex data"""
        # Create complex assignment with all relationships
        assignment = assignment_factory.make()
        
        # Add submissions with grades
        for _ in range(5):
            submission = assignment_submission_factory.make(assignment=assignment)
            grade = assignment_grade_factory.make()
            submission.grade = grade
            submission.save()
        
        # Add files
        for _ in range(3):
            assignment_file_factory.make(assignment=assignment)
        
        # Add comments
        for _ in range(2):
            assignment_comment_factory.make(assignment=assignment)
        
        # Test serialization performance
        import time
        start_time = time.time()
        serializer = AssignmentSerializer(assignment)
        data = serializer.data
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
        self.assertEqual(data['submission_count'], 5)
        self.assertEqual(data['graded_count'], 5)
        self.assertEqual(len(data['files']), 3)
        self.assertEqual(len(data['comments']), 2)
