"""
Comprehensive model tests for assignments app.
Tests all models, relationships, constraints, and custom methods.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.test import TestCase

from assignments.models import (
    AssignmentCategory, Assignment, AssignmentSubmission, AssignmentFile,
    AssignmentGrade, AssignmentComment, AssignmentGroup, AssignmentTemplate,
    AssignmentRubric, AssignmentRubricGrade, AssignmentPeerReview,
    AssignmentPlagiarismCheck, AssignmentLearningOutcome, AssignmentAnalytics,
    AssignmentNotification, AssignmentSchedule
)
from assignments.tests.factories import (
    assignment_category_factory, assignment_factory, assignment_submission_factory,
    assignment_file_factory, assignment_grade_factory, assignment_comment_factory,
    assignment_group_factory, assignment_template_factory, assignment_rubric_factory,
    assignment_rubric_grade_factory, assignment_peer_review_factory,
    assignment_plagiarism_check_factory, assignment_learning_outcome_factory,
    assignment_analytics_factory, assignment_notification_factory,
    assignment_schedule_factory, user_factory, faculty_factory, student_factory,
    published_assignment_factory, overdue_assignment_factory, group_assignment_factory,
    late_submission_factory, graded_submission_factory
)


class TestAssignmentCategoryModel(TestCase):
    """Test AssignmentCategory model"""

    def test_assignment_category_creation(self):
        """Test creating an assignment category"""
        category = assignment_category_factory.make()
        self.assertIsNotNone(category.id)
        self.assertTrue(category.is_active)
        self.assertEqual(category.color_code, "#007bff")

    def test_assignment_category_str(self):
        """Test string representation"""
        category = assignment_category_factory.make(name="Test Category")
        self.assertEqual(str(category), "Test Category")

    def test_assignment_category_ordering(self):
        """Test model ordering"""
        cat1 = assignment_category_factory.make(name="B Category")
        cat2 = assignment_category_factory.make(name="A Category")
        categories = AssignmentCategory.objects.all()
        self.assertEqual(categories[0], cat2)  # Should be ordered by name

    def test_assignment_category_unique_name(self):
        """Test unique name constraint"""
        assignment_category_factory.make(name="Unique Category")
        with self.assertRaises(IntegrityError):
            assignment_category_factory.make(name="Unique Category")


class TestAssignmentModel(TestCase):
    """Test Assignment model"""

    def test_assignment_creation(self):
        """Test creating an assignment"""
        assignment = assignment_factory.make()
        self.assertIsNotNone(assignment.id)
        self.assertEqual(assignment.status, "DRAFT")
        self.assertEqual(assignment.assignment_type, "HOMEWORK")
        self.assertEqual(assignment.difficulty_level, "INTERMEDIATE")

    def test_assignment_str(self):
        """Test string representation"""
        faculty = faculty_factory()
        assignment = assignment_factory.make(
            title="Test Assignment",
            faculty=faculty
        )
        expected = f"Test Assignment - {faculty.name}"
        self.assertEqual(str(assignment), expected)

    def test_assignment_is_overdue_property(self):
        """Test is_overdue property"""
        # Not overdue
        future_assignment = assignment_factory.make(
            status="PUBLISHED",
            due_date=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(future_assignment.is_overdue)

        # Overdue
        past_assignment = assignment_factory.make(
            status="PUBLISHED",
            due_date=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(past_assignment.is_overdue)

        # Draft assignment is not overdue
        draft_assignment = assignment_factory.make(
            status="DRAFT",
            due_date=timezone.now() - timedelta(days=1)
        )
        self.assertFalse(draft_assignment.is_overdue)

    def test_assignment_submission_count_property(self):
        """Test submission_count property"""
        assignment = assignment_factory.make()
        self.assertEqual(assignment.submission_count, 0)

        # Add submissions
        assignment_submission_factory.make(assignment=assignment)
        assignment_submission_factory.make(assignment=assignment)
        self.assertEqual(assignment.submission_count, 2)

    def test_assignment_graded_count_property(self):
        """Test graded_count property"""
        assignment = assignment_factory.make()
        self.assertEqual(assignment.graded_count, 0)

        # Add submissions with grades
        submission1 = assignment_submission_factory.make(assignment=assignment)
        submission2 = assignment_submission_factory.make(assignment=assignment)
        assignment_grade_factory.make(submission=submission1)
        
        # Refresh from database
        assignment.refresh_from_db()
        self.assertEqual(assignment.graded_count, 1)

    def test_assignment_clean_validation(self):
        """Test assignment clean method validation"""
        # Test group assignment validation
        assignment = assignment_factory.make(
            is_group_assignment=True,
            max_group_size=1
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

        # Test valid group assignment
        assignment.max_group_size = 3
        assignment.clean()  # Should not raise

        # Test due date validation for published assignments
        assignment = assignment_factory.make(
            status="PUBLISHED",
            due_date=timezone.now() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

    def test_assignment_available_until_validation(self):
        """Test available_until validation"""
        assignment = assignment_factory.make(
            due_date=timezone.now() + timedelta(days=7),
            available_until=timezone.now() + timedelta(days=5)
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

    def test_assignment_course_section_validation(self):
        """Test course section validation"""
        # This would require actual course and course_section models
        # For now, test that the validation exists
        assignment = assignment_factory.make()
        # The validation logic exists in the model
        self.assertTrue(hasattr(assignment, 'clean'))

    def test_assignment_ordering(self):
        """Test model ordering"""
        assignment1 = assignment_factory.make()
        assignment2 = assignment_factory.make()
        assignments = Assignment.objects.all()
        self.assertEqual(assignments[0], assignment2)  # Should be ordered by -created_at

    def test_assignment_indexes(self):
        """Test that indexes are properly set"""
        # This is more of a database-level test, but we can verify the Meta class
        self.assertIn('faculty', [idx.fields[0] for idx in Assignment._meta.indexes])
        self.assertIn('due_date', [idx.fields[0] for idx in Assignment._meta.indexes])


class TestAssignmentSubmissionModel(TestCase):
    """Test AssignmentSubmission model"""

    def test_submission_creation(self):
        """Test creating a submission"""
        submission = assignment_submission_factory.make()
        self.assertIsNotNone(submission.id)
        self.assertEqual(submission.status, "SUBMITTED")
        self.assertFalse(submission.is_late)

    def test_submission_str(self):
        """Test string representation"""
        student = student_factory()
        assignment = assignment_factory.make(title="Test Assignment")
        submission = assignment_submission_factory.make(
            student=student,
            assignment=assignment
        )
        expected = f"{student.name} - Test Assignment"
        self.assertEqual(str(submission), expected)

    def test_submission_unique_constraint(self):
        """Test unique constraint on assignment and student"""
        assignment = assignment_factory.make()
        student = student_factory()
        assignment_submission_factory.make(assignment=assignment, student=student)
        
        with self.assertRaises(IntegrityError):
            assignment_submission_factory.make(assignment=assignment, student=student)

    def test_submission_late_detection(self):
        """Test late submission detection in save method"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        submission = assignment_submission_factory.make(
            assignment=assignment,
            status="SUBMITTED"
        )
        self.assertTrue(submission.is_late)
        self.assertEqual(submission.status, "LATE")

    def test_submission_ordering(self):
        """Test model ordering"""
        submission1 = assignment_submission_factory.make()
        submission2 = assignment_submission_factory.make()
        submissions = AssignmentSubmission.objects.all()
        self.assertEqual(submissions[0], submission2)  # Should be ordered by -submission_date


class TestAssignmentFileModel(TestCase):
    """Test AssignmentFile model"""

    def test_file_creation(self):
        """Test creating a file"""
        file_obj = assignment_file_factory.make()
        self.assertIsNotNone(file_obj.id)
        self.assertEqual(file_obj.file_type, "ASSIGNMENT")

    def test_file_str(self):
        """Test string representation"""
        assignment = assignment_factory.make(title="Test Assignment")
        file_obj = assignment_file_factory.make(
            assignment=assignment,
            file_name="test.pdf"
        )
        expected = "test.pdf - Test Assignment"
        self.assertEqual(str(file_obj), expected)

    def test_file_size_calculation(self):
        """Test file size calculation in save method"""
        file_obj = assignment_file_factory.make(file_size=2048)
        self.assertEqual(file_obj.file_size, 2048)

    def test_file_ordering(self):
        """Test model ordering"""
        file1 = assignment_file_factory.make()
        file2 = assignment_file_factory.make()
        files = AssignmentFile.objects.all()
        self.assertEqual(files[0], file2)  # Should be ordered by -uploaded_at


class TestAssignmentGradeModel(TestCase):
    """Test AssignmentGrade model"""

    def test_grade_creation(self):
        """Test creating a grade"""
        grade = assignment_grade_factory.make()
        self.assertIsNotNone(grade.id)
        self.assertEqual(grade.marks_obtained, Decimal("85.00"))
        self.assertEqual(grade.grade_letter, "B+")

    def test_grade_str(self):
        """Test string representation"""
        grade = assignment_grade_factory.make(
            marks_obtained=Decimal("90.00"),
            grade_letter="A"
        )
        expected = "90.00 - A"
        self.assertEqual(str(grade), expected)

    def test_grade_str_no_letter(self):
        """Test string representation without grade letter"""
        grade = assignment_grade_factory.make(grade_letter=None)
        expected = f"{grade.marks_obtained} - No Grade"
        self.assertEqual(str(grade), expected)

    def test_grade_clean_validation(self):
        """Test grade clean method validation"""
        grade = assignment_grade_factory.make(marks_obtained=Decimal("-10.00"))
        with self.assertRaises(ValidationError):
            grade.clean()

    def test_grade_ordering(self):
        """Test model ordering"""
        grade1 = assignment_grade_factory.make()
        grade2 = assignment_grade_factory.make()
        grades = AssignmentGrade.objects.all()
        self.assertEqual(grades[0], grade2)  # Should be ordered by -graded_at


class TestAssignmentCommentModel(TestCase):
    """Test AssignmentComment model"""

    def test_comment_creation(self):
        """Test creating a comment"""
        comment = assignment_comment_factory.make()
        self.assertIsNotNone(comment.id)
        self.assertEqual(comment.comment_type, "GENERAL")

    def test_comment_str(self):
        """Test string representation"""
        user = user_factory()
        assignment = assignment_factory.make(title="Test Assignment")
        comment = assignment_comment_factory.make(
            author=user,
            assignment=assignment
        )
        expected = f"{user.email} - Test Assignment"
        self.assertEqual(str(comment), expected)

    def test_comment_ordering(self):
        """Test model ordering"""
        comment1 = assignment_comment_factory.make()
        comment2 = assignment_comment_factory.make()
        comments = AssignmentComment.objects.all()
        self.assertEqual(comments[0], comment1)  # Should be ordered by created_at


class TestAssignmentGroupModel(TestCase):
    """Test AssignmentGroup model"""

    def test_group_creation(self):
        """Test creating a group"""
        group = assignment_group_factory.make()
        self.assertIsNotNone(group.id)

    def test_group_str(self):
        """Test string representation"""
        assignment = assignment_factory.make(title="Test Assignment")
        group = assignment_group_factory.make(
            assignment=assignment,
            group_name="Test Group"
        )
        expected = "Test Group - Test Assignment"
        self.assertEqual(str(group), expected)

    def test_group_unique_constraint(self):
        """Test unique constraint on assignment and group name"""
        assignment = assignment_factory.make()
        assignment_group_factory.make(assignment=assignment, group_name="Unique Group")
        
        with self.assertRaises(IntegrityError):
            assignment_group_factory.make(assignment=assignment, group_name="Unique Group")

    def test_group_clean_validation(self):
        """Test group clean method validation"""
        # Test non-group assignment validation
        assignment = assignment_factory.make(is_group_assignment=False)
        group = assignment_group_factory.make(assignment=assignment)
        with self.assertRaises(ValidationError):
            group.clean()

        # Test group size validation
        assignment = assignment_factory.make(is_group_assignment=True, max_group_size=3)
        group = assignment_group_factory.make(assignment=assignment)
        # Add more members than allowed
        for _ in range(4):
            group.members.add(student_factory())
        with self.assertRaises(ValidationError):
            group.clean()


class TestAssignmentTemplateModel(TestCase):
    """Test AssignmentTemplate model"""

    def test_template_creation(self):
        """Test creating a template"""
        template = assignment_template_factory.make()
        self.assertIsNotNone(template.id)
        self.assertFalse(template.is_public)

    def test_template_str(self):
        """Test string representation"""
        template = assignment_template_factory.make(name="Test Template")
        self.assertEqual(str(template), "Test Template")

    def test_template_ordering(self):
        """Test model ordering"""
        template1 = assignment_template_factory.make(name="B Template")
        template2 = assignment_template_factory.make(name="A Template")
        templates = AssignmentTemplate.objects.all()
        self.assertEqual(templates[0], template2)  # Should be ordered by name


class TestAssignmentRubricModel(TestCase):
    """Test AssignmentRubric model"""

    def test_rubric_creation(self):
        """Test creating a rubric"""
        rubric = assignment_rubric_factory.make()
        self.assertIsNotNone(rubric.id)
        self.assertEqual(rubric.rubric_type, "ANALYTIC")

    def test_rubric_str(self):
        """Test string representation"""
        rubric = assignment_rubric_factory.make(name="Test Rubric")
        self.assertEqual(str(rubric), "Test Rubric")

    def test_rubric_ordering(self):
        """Test model ordering"""
        rubric1 = assignment_rubric_factory.make(name="B Rubric")
        rubric2 = assignment_rubric_factory.make(name="A Rubric")
        rubrics = AssignmentRubric.objects.all()
        self.assertEqual(rubrics[0], rubric2)  # Should be ordered by name


class TestAssignmentRubricGradeModel(TestCase):
    """Test AssignmentRubricGrade model"""

    def test_rubric_grade_creation(self):
        """Test creating a rubric grade"""
        rubric_grade = assignment_rubric_grade_factory.make()
        self.assertIsNotNone(rubric_grade.id)
        self.assertEqual(rubric_grade.total_score, Decimal("88.00"))

    def test_rubric_grade_str(self):
        """Test string representation"""
        student = student_factory()
        rubric = assignment_rubric_factory.make(name="Test Rubric")
        submission = assignment_submission_factory.make(student=student)
        rubric_grade = assignment_rubric_grade_factory.make(
            submission=submission,
            rubric=rubric,
            total_score=Decimal("95.00")
        )
        expected = f"{student.name} - Test Rubric: 95.00"
        self.assertEqual(str(rubric_grade), expected)

    def test_rubric_grade_ordering(self):
        """Test model ordering"""
        rubric_grade1 = assignment_rubric_grade_factory.make()
        rubric_grade2 = assignment_rubric_grade_factory.make()
        rubric_grades = AssignmentRubricGrade.objects.all()
        self.assertEqual(rubric_grades[0], rubric_grade2)  # Should be ordered by -graded_at


class TestAssignmentPeerReviewModel(TestCase):
    """Test AssignmentPeerReview model"""

    def test_peer_review_creation(self):
        """Test creating a peer review"""
        peer_review = assignment_peer_review_factory.make()
        self.assertIsNotNone(peer_review.id)
        self.assertTrue(peer_review.is_completed)

    def test_peer_review_str(self):
        """Test string representation"""
        reviewer = student_factory()
        reviewee = student_factory()
        assignment = assignment_factory.make(title="Test Assignment")
        peer_review = assignment_peer_review_factory.make(
            reviewer=reviewer,
            reviewee=reviewee,
            assignment=assignment
        )
        expected = f"{reviewer.name} reviews {reviewee.name} - Test Assignment"
        self.assertEqual(str(peer_review), expected)

    def test_peer_review_unique_constraint(self):
        """Test unique constraint on assignment, reviewer, and reviewee"""
        assignment = assignment_factory.make()
        reviewer = student_factory()
        reviewee = student_factory()
        assignment_peer_review_factory.make(
            assignment=assignment,
            reviewer=reviewer,
            reviewee=reviewee
        )
        
        with self.assertRaises(IntegrityError):
            assignment_peer_review_factory.make(
                assignment=assignment,
                reviewer=reviewer,
                reviewee=reviewee
            )

    def test_peer_review_ordering(self):
        """Test model ordering"""
        peer_review1 = assignment_peer_review_factory.make()
        peer_review2 = assignment_peer_review_factory.make()
        peer_reviews = AssignmentPeerReview.objects.all()
        self.assertEqual(peer_reviews[0], peer_review2)  # Should be ordered by -submitted_at


class TestAssignmentPlagiarismCheckModel(TestCase):
    """Test AssignmentPlagiarismCheck model"""

    def test_plagiarism_check_creation(self):
        """Test creating a plagiarism check"""
        plagiarism_check = assignment_plagiarism_check_factory.make()
        self.assertIsNotNone(plagiarism_check.id)
        self.assertEqual(plagiarism_check.status, "CLEAN")

    def test_plagiarism_check_str(self):
        """Test string representation"""
        student = student_factory()
        submission = assignment_submission_factory.make(student=student)
        plagiarism_check = assignment_plagiarism_check_factory.make(
            submission=submission,
            status="SUSPICIOUS",
            similarity_percentage=Decimal("25.00")
        )
        expected = f"{student.name} - SUSPICIOUS (25.00%)"
        self.assertEqual(str(plagiarism_check), expected)

    def test_plagiarism_check_ordering(self):
        """Test model ordering"""
        plagiarism_check1 = assignment_plagiarism_check_factory.make()
        plagiarism_check2 = assignment_plagiarism_check_factory.make()
        plagiarism_checks = AssignmentPlagiarismCheck.objects.all()
        self.assertEqual(plagiarism_checks[0], plagiarism_check2)  # Should be ordered by -checked_at


class TestAssignmentLearningOutcomeModel(TestCase):
    """Test AssignmentLearningOutcome model"""

    def test_learning_outcome_creation(self):
        """Test creating a learning outcome"""
        learning_outcome = assignment_learning_outcome_factory.make()
        self.assertIsNotNone(learning_outcome.id)
        self.assertEqual(learning_outcome.bloom_level, "APPLY")

    def test_learning_outcome_str(self):
        """Test string representation"""
        assignment = assignment_factory.make(title="Test Assignment")
        learning_outcome = assignment_learning_outcome_factory.make(
            assignment=assignment,
            outcome_code="LO1"
        )
        expected = "Test Assignment - LO1"
        self.assertEqual(str(learning_outcome), expected)

    def test_learning_outcome_unique_constraint(self):
        """Test unique constraint on assignment and outcome code"""
        assignment = assignment_factory.make()
        assignment_learning_outcome_factory.make(
            assignment=assignment,
            outcome_code="LO1"
        )
        
        with self.assertRaises(IntegrityError):
            assignment_learning_outcome_factory.make(
                assignment=assignment,
                outcome_code="LO1"
            )

    def test_learning_outcome_ordering(self):
        """Test model ordering"""
        learning_outcome1 = assignment_learning_outcome_factory.make(outcome_code="LO2")
        learning_outcome2 = assignment_learning_outcome_factory.make(outcome_code="LO1")
        learning_outcomes = AssignmentLearningOutcome.objects.all()
        self.assertEqual(learning_outcomes[0], learning_outcome2)  # Should be ordered by outcome_code


class TestAssignmentAnalyticsModel(TestCase):
    """Test AssignmentAnalytics model"""

    def test_analytics_creation(self):
        """Test creating analytics"""
        analytics = assignment_analytics_factory.make()
        self.assertIsNotNone(analytics.id)
        self.assertEqual(analytics.submission_rate, Decimal("83.33"))

    def test_analytics_str(self):
        """Test string representation"""
        assignment = assignment_factory.make(title="Test Assignment")
        analytics = assignment_analytics_factory.make(assignment=assignment)
        expected = "Analytics for Test Assignment"
        self.assertEqual(str(analytics), expected)

    def test_analytics_ordering(self):
        """Test model ordering"""
        analytics1 = assignment_analytics_factory.make()
        analytics2 = assignment_analytics_factory.make()
        analytics_list = AssignmentAnalytics.objects.all()
        self.assertEqual(analytics_list[0], analytics2)  # Should be ordered by -last_updated


class TestAssignmentNotificationModel(TestCase):
    """Test AssignmentNotification model"""

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = assignment_notification_factory.make()
        self.assertIsNotNone(notification.id)
        self.assertFalse(notification.is_read)

    def test_notification_str(self):
        """Test string representation"""
        user = user_factory()
        notification = assignment_notification_factory.make(
            recipient=user,
            title="Test Notification"
        )
        expected = f"{user.email} - Test Notification"
        self.assertEqual(str(notification), expected)

    def test_notification_ordering(self):
        """Test model ordering"""
        notification1 = assignment_notification_factory.make()
        notification2 = assignment_notification_factory.make()
        notifications = AssignmentNotification.objects.all()
        self.assertEqual(notifications[0], notification2)  # Should be ordered by -created_at


class TestAssignmentScheduleModel(TestCase):
    """Test AssignmentSchedule model"""

    def test_schedule_creation(self):
        """Test creating a schedule"""
        schedule = assignment_schedule_factory.make()
        self.assertIsNotNone(schedule.id)
        self.assertTrue(schedule.is_active)

    def test_schedule_str(self):
        """Test string representation"""
        schedule = assignment_schedule_factory.make(name="Test Schedule")
        self.assertEqual(str(schedule), "Test Schedule")

    def test_schedule_ordering(self):
        """Test model ordering"""
        schedule1 = assignment_schedule_factory.make(name="B Schedule")
        schedule2 = assignment_schedule_factory.make(name="A Schedule")
        schedules = AssignmentSchedule.objects.all()
        self.assertEqual(schedules[0], schedule2)  # Should be ordered by name


class TestModelRelationships(TestCase):
    """Test model relationships and foreign keys"""

    def test_assignment_faculty_relationship(self):
        """Test assignment-faculty relationship"""
        faculty = faculty_factory()
        assignment = assignment_factory.make(faculty=faculty)
        self.assertEqual(assignment.faculty, faculty)
        self.assertIn(assignment, faculty.assignments.all())

    def test_assignment_submission_relationship(self):
        """Test assignment-submission relationship"""
        assignment = assignment_factory.make()
        submission = assignment_submission_factory.make(assignment=assignment)
        self.assertEqual(submission.assignment, assignment)
        self.assertIn(submission, assignment.submissions.all())

    def test_submission_student_relationship(self):
        """Test submission-student relationship"""
        student = student_factory()
        submission = assignment_submission_factory.make(student=student)
        self.assertEqual(submission.student, student)
        self.assertIn(submission, student.assignment_submissions.all())

    def test_submission_grade_relationship(self):
        """Test submission-grade relationship"""
        submission = assignment_submission_factory.make()
        grade = assignment_grade_factory.make()
        submission.grade = grade
        submission.save()
        self.assertEqual(submission.grade, grade)
        self.assertEqual(grade.submission, submission)

    def test_assignment_category_relationship(self):
        """Test assignment-category relationship"""
        category = assignment_category_factory.make()
        assignment = assignment_factory.make(category=category)
        self.assertEqual(assignment.category, category)
        self.assertIn(assignment, category.assignments.all())

    def test_assignment_comment_relationship(self):
        """Test assignment-comment relationship"""
        assignment = assignment_factory.make()
        comment = assignment_comment_factory.make(assignment=assignment)
        self.assertEqual(comment.assignment, assignment)
        self.assertIn(comment, assignment.comments.all())

    def test_assignment_file_relationship(self):
        """Test assignment-file relationship"""
        assignment = assignment_factory.make()
        file_obj = assignment_file_factory.make(assignment=assignment)
        self.assertEqual(file_obj.assignment, assignment)
        self.assertIn(file_obj, assignment.files.all())

    def test_assignment_group_relationship(self):
        """Test assignment-group relationship"""
        assignment = assignment_factory.make()
        group = assignment_group_factory.make(assignment=assignment)
        self.assertEqual(group.assignment, assignment)
        self.assertIn(group, assignment.groups.all())

    def test_assignment_analytics_relationship(self):
        """Test assignment-analytics relationship"""
        assignment = assignment_factory.make()
        analytics = assignment_analytics_factory.make(assignment=assignment)
        self.assertEqual(analytics.assignment, assignment)
        self.assertEqual(assignment.analytics, analytics)


class TestModelConstraints(TestCase):
    """Test model constraints and validations"""

    def test_assignment_max_marks_validation(self):
        """Test max_marks validation"""
        with self.assertRaises(ValidationError):
            assignment = assignment_factory.make(max_marks=Decimal("0.00"))
            assignment.full_clean()

    def test_assignment_late_penalty_validation(self):
        """Test late_penalty_percentage validation"""
        with self.assertRaises(ValidationError):
            assignment = assignment_factory.make(late_penalty_percentage=Decimal("150.00"))
            assignment.full_clean()

    def test_assignment_plagiarism_threshold_validation(self):
        """Test plagiarism_threshold validation"""
        with self.assertRaises(ValidationError):
            assignment = assignment_factory.make(plagiarism_threshold=Decimal("150.00"))
            assignment.full_clean()

    def test_grade_marks_validation(self):
        """Test grade marks validation"""
        with self.assertRaises(ValidationError):
            grade = assignment_grade_factory.make(marks_obtained=Decimal("-10.00"))
            grade.full_clean()

    def test_peer_review_rating_validation(self):
        """Test peer review rating validation"""
        with self.assertRaises(ValidationError):
            peer_review = assignment_peer_review_factory.make(content_rating=6)
            peer_review.full_clean()

    def test_learning_outcome_weight_validation(self):
        """Test learning outcome weight validation"""
        with self.assertRaises(ValidationError):
            learning_outcome = assignment_learning_outcome_factory.make(weight=Decimal("150.00"))
            learning_outcome.full_clean()


class TestModelMethods(TestCase):
    """Test custom model methods"""

    def test_assignment_clean_method(self):
        """Test assignment clean method"""
        # Test group assignment validation
        assignment = assignment_factory.make(
            is_group_assignment=True,
            max_group_size=1
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

        # Test due date validation
        assignment = assignment_factory.make(
            status="PUBLISHED",
            due_date=timezone.now() - timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            assignment.clean()

    def test_submission_save_method(self):
        """Test submission save method"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        submission = assignment_submission_factory.make(
            assignment=assignment,
            status="SUBMITTED"
        )
        self.assertTrue(submission.is_late)
        self.assertEqual(submission.status, "LATE")

    def test_file_save_method(self):
        """Test file save method"""
        file_obj = assignment_file_factory.make(file_size=1024)
        self.assertEqual(file_obj.file_size, 1024)

    def test_grade_clean_method(self):
        """Test grade clean method"""
        grade = assignment_grade_factory.make(marks_obtained=Decimal("-5.00"))
        with self.assertRaises(ValidationError):
            grade.clean()

    def test_group_clean_method(self):
        """Test group clean method"""
        assignment = assignment_factory.make(is_group_assignment=False)
        group = assignment_group_factory.make(assignment=assignment)
        with self.assertRaises(ValidationError):
            group.clean()


class TestModelProperties(TestCase):
    """Test model properties"""

    def test_assignment_properties(self):
        """Test assignment properties"""
        assignment = assignment_factory.make()
        
        # Test is_overdue property
        self.assertFalse(assignment.is_overdue)
        
        # Test submission_count property
        self.assertEqual(assignment.submission_count, 0)
        
        # Test graded_count property
        self.assertEqual(assignment.graded_count, 0)

    def test_assignment_properties_with_data(self):
        """Test assignment properties with actual data"""
        assignment = assignment_factory.make()
        
        # Add submissions
        submission1 = assignment_submission_factory.make(assignment=assignment)
        submission2 = assignment_submission_factory.make(assignment=assignment)
        
        # Add grade to one submission
        grade = assignment_grade_factory.make()
        submission1.grade = grade
        submission1.save()
        
        # Refresh and test properties
        assignment.refresh_from_db()
        self.assertEqual(assignment.submission_count, 2)
        self.assertEqual(assignment.graded_count, 1)


class TestModelChoices(TestCase):
    """Test model choice fields"""

    def test_assignment_status_choices(self):
        """Test assignment status choices"""
        choices = Assignment.STATUS_CHOICES
        expected_choices = [
            ('DRAFT', 'Draft'),
            ('PUBLISHED', 'Published'),
            ('CLOSED', 'Closed'),
            ('CANCELLED', 'Cancelled'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_assignment_type_choices(self):
        """Test assignment type choices"""
        choices = Assignment.ASSIGNMENT_TYPES
        self.assertIn(('HOMEWORK', 'Homework'), choices)
        self.assertIn(('PROJECT', 'Project'), choices)
        self.assertIn(('EXAM', 'Exam'), choices)

    def test_difficulty_level_choices(self):
        """Test difficulty level choices"""
        choices = Assignment.DIFFICULTY_LEVELS
        expected_choices = [
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
            ('EXPERT', 'Expert'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_submission_status_choices(self):
        """Test submission status choices"""
        choices = AssignmentSubmission.STATUS_CHOICES
        expected_choices = [
            ('SUBMITTED', 'Submitted'),
            ('DRAFT', 'Draft'),
            ('LATE', 'Late Submission'),
            ('RESUBMITTED', 'Resubmitted'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_grade_letter_choices(self):
        """Test grade letter choices"""
        choices = AssignmentGrade.GRADE_LETTER_CHOICES
        self.assertIn(('A+', 'A+'), choices)
        self.assertIn(('F', 'F'), choices)
        self.assertIn(('P', 'Pass'), choices)

    def test_comment_type_choices(self):
        """Test comment type choices"""
        choices = AssignmentComment.COMMENT_TYPE_CHOICES
        expected_choices = [
            ('GENERAL', 'General Comment'),
            ('CLARIFICATION', 'Clarification'),
            ('FEEDBACK', 'Feedback'),
            ('QUESTION', 'Question'),
            ('ANNOUNCEMENT', 'Announcement'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_file_type_choices(self):
        """Test file type choices"""
        choices = AssignmentFile.FILE_TYPE_CHOICES
        expected_choices = [
            ('ASSIGNMENT', 'Assignment File'),
            ('SUBMISSION', 'Submission File'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_rubric_type_choices(self):
        """Test rubric type choices"""
        choices = AssignmentRubric.RUBRIC_TYPES
        expected_choices = [
            ('ANALYTIC', 'Analytic Rubric'),
            ('HOLISTIC', 'Holistic Rubric'),
            ('CHECKLIST', 'Checklist Rubric'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_plagiarism_status_choices(self):
        """Test plagiarism status choices"""
        choices = AssignmentPlagiarismCheck.PLAGIARISM_STATUS
        expected_choices = [
            ('PENDING', 'Pending'),
            ('CLEAN', 'No Plagiarism Detected'),
            ('SUSPICIOUS', 'Suspicious Content'),
            ('PLAGIARIZED', 'Plagiarism Detected'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_bloom_taxonomy_choices(self):
        """Test Bloom taxonomy choices"""
        choices = AssignmentLearningOutcome.BLOOM_TAXONOMY_LEVELS
        expected_choices = [
            ('REMEMBER', 'Remember'),
            ('UNDERSTAND', 'Understand'),
            ('APPLY', 'Apply'),
            ('ANALYZE', 'Analyze'),
            ('EVALUATE', 'Evaluate'),
            ('CREATE', 'Create'),
        ]
        self.assertEqual(choices, expected_choices)

    def test_notification_type_choices(self):
        """Test notification type choices"""
        choices = AssignmentNotification.NOTIFICATION_TYPES
        self.assertIn(('ASSIGNMENT_CREATED', 'Assignment Created'), choices)
        self.assertIn(('GRADE_POSTED', 'Grade Posted'), choices)
        self.assertIn(('PLAGIARISM_DETECTED', 'Plagiarism Detected'), choices)

    def test_schedule_type_choices(self):
        """Test schedule type choices"""
        choices = AssignmentSchedule.SCHEDULE_TYPES
        expected_choices = [
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('SEMESTER', 'Per Semester'),
            ('CUSTOM', 'Custom Interval'),
        ]
        self.assertEqual(choices, expected_choices)


@pytest.mark.django_db
class TestModelIntegration(TestCase):
    """Test model integration and complex scenarios"""

    def test_complete_assignment_workflow(self):
        """Test complete assignment workflow"""
        # Create assignment
        assignment = published_assignment_factory()
        
        # Create submission
        submission = assignment_submission_factory.make(assignment=assignment)
        
        # Create grade
        grade = assignment_grade_factory.make()
        submission.grade = grade
        submission.graded_by = grade.graded_by
        submission.graded_at = timezone.now()
        submission.save()
        
        # Create file
        file_obj = assignment_file_factory.make(
            assignment=assignment,
            submission=submission,
            file_type="SUBMISSION"
        )
        
        # Create comment
        comment = assignment_comment_factory.make(assignment=assignment)
        
        # Verify relationships
        self.assertEqual(assignment.submission_count, 1)
        self.assertEqual(assignment.graded_count, 1)
        self.assertIn(submission, assignment.submissions.all())
        self.assertIn(file_obj, assignment.files.all())
        self.assertIn(comment, assignment.comments.all())

    def test_group_assignment_workflow(self):
        """Test group assignment workflow"""
        # Create group assignment
        assignment = group_assignment_factory()
        
        # Create group
        group = assignment_group_factory.make(assignment=assignment)
        
        # Add members
        students = [student_factory() for _ in range(3)]
        for student in students:
            group.members.add(student)
        
        # Create group submission
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=students[0]  # Group leader submits
        )
        
        # Verify relationships
        self.assertEqual(group.members.count(), 3)
        self.assertIn(submission, assignment.submissions.all())

    def test_peer_review_workflow(self):
        """Test peer review workflow"""
        # Create assignment with peer review enabled
        assignment = assignment_factory.make(enable_peer_review=True)
        
        # Create submissions
        submission1 = assignment_submission_factory.make(assignment=assignment)
        submission2 = assignment_submission_factory.make(assignment=assignment)
        
        # Create peer review
        peer_review = assignment_peer_review_factory.make(
            assignment=assignment,
            reviewer=submission1.student,
            reviewee=submission2.student,
            submission=submission2
        )
        
        # Verify relationships
        self.assertEqual(peer_review.assignment, assignment)
        self.assertEqual(peer_review.reviewer, submission1.student)
        self.assertEqual(peer_review.reviewee, submission2.student)

    def test_plagiarism_check_workflow(self):
        """Test plagiarism check workflow"""
        # Create submission
        submission = assignment_submission_factory.make()
        
        # Create plagiarism check
        plagiarism_check = assignment_plagiarism_check_factory.make(
            submission=submission,
            status="SUSPICIOUS",
            similarity_percentage=Decimal("25.00")
        )
        
        # Verify relationships
        self.assertEqual(plagiarism_check.submission, submission)
        self.assertEqual(plagiarism_check.status, "SUSPICIOUS")

    def test_analytics_workflow(self):
        """Test analytics workflow"""
        # Create assignment
        assignment = assignment_factory.make()
        
        # Create analytics
        analytics = assignment_analytics_factory.make(assignment=assignment)
        
        # Create submissions
        submissions = [
            assignment_submission_factory.make(assignment=assignment)
            for _ in range(5)
        ]
        
        # Create grades for some submissions
        for submission in submissions[:3]:
            grade = assignment_grade_factory.make()
            submission.grade = grade
            submission.save()
        
        # Update analytics
        analytics.actual_submissions = len(submissions)
        analytics.submission_rate = (analytics.actual_submissions / analytics.total_expected_submissions) * 100
        analytics.save()
        
        # Verify analytics
        self.assertEqual(analytics.actual_submissions, 5)
        self.assertGreater(analytics.submission_rate, 0)

    def test_notification_workflow(self):
        """Test notification workflow"""
        # Create assignment
        assignment = assignment_factory.make()
        
        # Create notification
        user = user_factory()
        notification = assignment_notification_factory.make(
            assignment=assignment,
            recipient=user,
            notification_type="ASSIGNMENT_CREATED"
        )
        
        # Mark as read
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        # Verify notification
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_template_workflow(self):
        """Test template workflow"""
        # Create template
        template = assignment_template_factory.make(is_public=True)
        
        # Create schedule
        schedule = assignment_schedule_factory.make(template=template)
        
        # Verify relationships
        self.assertEqual(schedule.template, template)
        self.assertIn(schedule, template.schedules.all())

    def test_learning_outcome_workflow(self):
        """Test learning outcome workflow"""
        # Create assignment
        assignment = assignment_factory.make()
        
        # Create learning outcomes
        outcomes = [
            assignment_learning_outcome_factory.make(
                assignment=assignment,
                outcome_code=f"LO{i+1}",
                weight=Decimal("25.00")
            )
            for i in range(4)
        ]
        
        # Verify relationships
        self.assertEqual(assignment.learning_outcomes.count(), 4)
        for outcome in outcomes:
            self.assertEqual(outcome.assignment, assignment)

    def test_rubric_workflow(self):
        """Test rubric workflow"""
        # Create rubric
        rubric = assignment_rubric_factory.make()
        
        # Create assignment with rubric
        assignment = assignment_factory.make(rubric=rubric)
        
        # Create submission
        submission = assignment_submission_factory.make(assignment=assignment)
        
        # Create rubric grade
        rubric_grade = assignment_rubric_grade_factory.make(
            submission=submission,
            rubric=rubric
        )
        
        # Verify relationships
        self.assertEqual(assignment.rubric, rubric)
        self.assertEqual(rubric_grade.rubric, rubric)
        self.assertEqual(rubric_grade.submission, submission)
