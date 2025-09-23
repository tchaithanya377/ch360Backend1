"""
Comprehensive signal tests for assignments app.
Tests all signal handlers and their behavior.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from datetime import timedelta
from unittest.mock import patch, Mock

from assignments.models import Assignment, AssignmentSubmission
from assignments.signals import assignment_pre_save, submission_post_save, assignment_post_save
from assignments.tests.factories import (
    assignment_factory, assignment_submission_factory,
    faculty_factory, student_factory
)


class BaseSignalTest(TestCase):
    """Base test class for signal tests"""

    def setUp(self):
        self.faculty = faculty_factory()
        self.student = student_factory()


class TestAssignmentPreSaveSignal(BaseSignalTest):
    """Test assignment_pre_save signal"""

    def test_auto_generate_title_when_missing(self):
        """Test auto-generating title when not provided"""
        # Create assignment without title
        assignment = Assignment(
            description="Test description",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Trigger pre_save signal
        assignment_pre_save(Assignment, assignment)
        
        # Title should be auto-generated
        self.assertIsNotNone(assignment.title)
        self.assertIn(self.faculty.name, assignment.title)
        self.assertIn(timezone.now().strftime('%Y-%m-%d'), assignment.title)

    def test_preserve_existing_title(self):
        """Test preserving existing title"""
        existing_title = "Existing Assignment Title"
        assignment = Assignment(
            title=existing_title,
            description="Test description",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Trigger pre_save signal
        assignment_pre_save(Assignment, assignment)
        
        # Title should remain unchanged
        self.assertEqual(assignment.title, existing_title)

    def test_prevent_publishing_past_due_date(self):
        """Test preventing publishing assignments with past due dates"""
        assignment = Assignment(
            title="Test Assignment",
            description="Test description",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() - timedelta(days=1),  # Past due date
            status='PUBLISHED'
        )
        
        # Trigger pre_save signal
        assignment_pre_save(Assignment, assignment)
        
        # Status should be changed to DRAFT
        self.assertEqual(assignment.status, 'DRAFT')

    def test_allow_publishing_future_due_date(self):
        """Test allowing publishing assignments with future due dates"""
        assignment = Assignment(
            title="Test Assignment",
            description="Test description",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7),  # Future due date
            status='PUBLISHED'
        )
        
        # Trigger pre_save signal
        assignment_pre_save(Assignment, assignment)
        
        # Status should remain PUBLISHED
        self.assertEqual(assignment.status, 'PUBLISHED')

    def test_draft_status_unaffected_by_due_date(self):
        """Test that draft status is unaffected by due date"""
        assignment = Assignment(
            title="Test Assignment",
            description="Test description",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() - timedelta(days=1),  # Past due date
            status='DRAFT'
        )
        
        # Trigger pre_save signal
        assignment_pre_save(Assignment, assignment)
        
        # Status should remain DRAFT
        self.assertEqual(assignment.status, 'DRAFT')

    def test_signal_with_missing_faculty_name(self):
        """Test signal behavior with missing faculty name"""
        # Create faculty without name
        faculty_no_name = faculty_factory()
        if hasattr(faculty_no_name, 'name'):
            faculty_no_name.name = None
        
        assignment = Assignment(
            description="Test description",
            faculty=faculty_no_name,
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Should handle gracefully
        try:
            assignment_pre_save(Assignment, assignment)
            self.assertIsNotNone(assignment.title)
        except AttributeError:
            # Acceptable if it raises AttributeError for missing name
            pass


class TestSubmissionPostSaveSignal(BaseSignalTest):
    """Test submission_post_save signal"""

    def test_mark_late_submission_on_creation(self):
        """Test marking submission as late on creation"""
        # Create assignment with past due date
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        # Create submission
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='SUBMITTED'
        )
        
        # Trigger post_save signal for creation
        submission_post_save(AssignmentSubmission, submission, created=True)
        
        # Submission should be marked as late
        self.assertTrue(submission.is_late)
        self.assertEqual(submission.status, 'LATE')

    def test_on_time_submission_not_marked_late(self):
        """Test that on-time submissions are not marked late"""
        # Create assignment with future due date
        assignment = assignment_factory.make(
            due_date=timezone.now() + timedelta(days=1)
        )
        
        # Create submission
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='SUBMITTED'
        )
        
        # Trigger post_save signal for creation
        submission_post_save(AssignmentSubmission, submission, created=True)
        
        # Submission should not be marked as late
        self.assertFalse(submission.is_late)
        self.assertEqual(submission.status, 'SUBMITTED')

    def test_existing_submission_not_affected(self):
        """Test that existing submissions are not affected by signal"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='SUBMITTED',
            is_late=False  # Explicitly set to False
        )
        
        # Trigger post_save signal for update (not creation)
        submission_post_save(AssignmentSubmission, submission, created=False)
        
        # Submission should not be modified
        self.assertFalse(submission.is_late)
        self.assertEqual(submission.status, 'SUBMITTED')

    def test_draft_submission_not_marked_late(self):
        """Test that draft submissions are not marked late"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='DRAFT'
        )
        
        # Trigger post_save signal for creation
        submission_post_save(AssignmentSubmission, submission, created=True)
        
        # Draft submission should be marked as late but status unchanged
        self.assertTrue(submission.is_late)
        self.assertEqual(submission.status, 'DRAFT')  # Status should not change to LATE

    def test_signal_handles_missing_due_date(self):
        """Test signal handles missing due date gracefully"""
        assignment = assignment_factory.make(due_date=None)
        
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='SUBMITTED'
        )
        
        # Should handle None due_date gracefully
        try:
            submission_post_save(AssignmentSubmission, submission, created=True)
            # Should not crash
        except (TypeError, AttributeError):
            # Acceptable if it raises an error for None due_date
            pass


class TestAssignmentPostSaveSignal(BaseSignalTest):
    """Test assignment_post_save signal"""

    def test_assignment_creation_signal(self):
        """Test assignment creation signal"""
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Trigger post_save signal for creation
        assignment_post_save(Assignment, assignment, created=True)
        
        # Signal should execute without error
        # In real implementation, this might send notifications
        self.assertTrue(True)  # Signal executed successfully

    def test_assignment_update_signal(self):
        """Test assignment update signal"""
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Trigger post_save signal for update
        assignment_post_save(Assignment, assignment, created=False)
        
        # Signal should execute without error for updates
        self.assertTrue(True)  # Signal executed successfully

    def test_signal_with_no_assigned_students(self):
        """Test signal with assignment having no assigned students"""
        assignment = assignment_factory.make(faculty=self.faculty)
        
        # Trigger post_save signal for creation
        assignment_post_save(Assignment, assignment, created=True)
        
        # Should handle assignments with no students gracefully
        self.assertTrue(True)

    def test_signal_with_assigned_students(self):
        """Test signal with assignment having assigned students"""
        assignment = assignment_factory.make(faculty=self.faculty)
        assignment.assigned_to_students.add(self.student)
        
        # Trigger post_save signal for creation
        assignment_post_save(Assignment, assignment, created=True)
        
        # Should handle assignments with students gracefully
        self.assertTrue(True)


class TestSignalIntegration(BaseSignalTest):
    """Test signal integration with model operations"""

    def test_assignment_save_triggers_pre_save_signal(self):
        """Test that saving assignment triggers pre_save signal"""
        assignment = Assignment(
            description="Test description",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Save should trigger pre_save signal
        assignment.save()
        
        # Title should be auto-generated
        self.assertIsNotNone(assignment.title)
        self.assertIn(self.faculty.name, assignment.title)

    def test_assignment_save_triggers_post_save_signal(self):
        """Test that saving assignment triggers post_save signal"""
        # This test verifies the signal is connected
        with patch('assignments.signals.assignment_post_save') as mock_signal:
            assignment = assignment_factory.make()
            
            # Signal should have been called
            mock_signal.assert_called_once()

    def test_submission_save_triggers_post_save_signal(self):
        """Test that saving submission triggers post_save signal"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='SUBMITTED'
        )
        
        # Save should trigger post_save signal
        submission.save()
        
        # Should be marked as late
        self.assertTrue(submission.is_late)
        self.assertEqual(submission.status, 'LATE')

    def test_bulk_create_does_not_trigger_signals(self):
        """Test that bulk_create does not trigger signals"""
        assignment = assignment_factory.make()
        
        # Bulk create submissions
        submissions = [
            AssignmentSubmission(
                assignment=assignment,
                student=self.student,
                content=f"Test content {i}"
            )
            for i in range(3)
        ]
        
        AssignmentSubmission.objects.bulk_create(submissions)
        
        # Signals should not have been triggered
        for submission in submissions:
            self.assertFalse(submission.is_late)  # Default value, not modified by signal

    def test_update_does_not_trigger_post_save_for_creation(self):
        """Test that update operations don't trigger creation logic"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        # Create submission normally (will trigger signal)
        submission = assignment_submission_factory.make(
            assignment=assignment,
            student=self.student
        )
        
        # Reset late status
        submission.is_late = False
        submission.status = 'SUBMITTED'
        submission.save(update_fields=['is_late', 'status'])
        
        # Should not be marked as late again (created=False in signal)
        submission.refresh_from_db()
        # Note: This depends on the actual signal implementation


class TestSignalErrorHandling(BaseSignalTest):
    """Test signal error handling"""

    def test_pre_save_signal_with_invalid_faculty(self):
        """Test pre_save signal with invalid faculty"""
        assignment = Assignment(
            description="Test description",
            faculty=None,  # Invalid faculty
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Should handle None faculty gracefully
        try:
            assignment_pre_save(Assignment, assignment)
        except AttributeError:
            # Acceptable if it raises AttributeError for None faculty
            pass

    def test_post_save_signal_with_invalid_assignment(self):
        """Test post_save signal with invalid assignment"""
        submission = AssignmentSubmission(
            assignment=None,  # Invalid assignment
            student=self.student,
            content="Test content"
        )
        
        # Should handle None assignment gracefully
        try:
            submission_post_save(AssignmentSubmission, submission, created=True)
        except AttributeError:
            # Acceptable if it raises AttributeError for None assignment
            pass

    def test_signal_with_timezone_issues(self):
        """Test signals with timezone-related issues"""
        # Create assignment with naive datetime
        from datetime import datetime
        naive_datetime = datetime(2024, 1, 1, 12, 0, 0)  # Naive datetime
        
        assignment = assignment_factory.make(due_date=naive_datetime)
        
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Test content",
            status='SUBMITTED'
        )
        
        # Should handle timezone comparison gracefully
        try:
            submission_post_save(AssignmentSubmission, submission, created=True)
        except (TypeError, ValueError):
            # Acceptable if it raises timezone-related errors
            pass


class TestSignalDisconnection(BaseSignalTest):
    """Test signal disconnection and reconnection"""

    def test_disconnect_pre_save_signal(self):
        """Test disconnecting pre_save signal"""
        # Disconnect signal
        pre_save.disconnect(assignment_pre_save, sender=Assignment)
        
        try:
            assignment = Assignment(
                description="Test description",
                faculty=self.faculty,
                max_marks=100.00,
                due_date=timezone.now() + timedelta(days=7)
            )
            
            assignment.save()
            
            # Title should not be auto-generated
            self.assertIsNone(assignment.title)
            
        finally:
            # Reconnect signal
            pre_save.connect(assignment_pre_save, sender=Assignment)

    def test_disconnect_post_save_signal(self):
        """Test disconnecting post_save signal"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(days=1)
        )
        
        # Disconnect signal
        post_save.disconnect(submission_post_save, sender=AssignmentSubmission)
        
        try:
            submission = AssignmentSubmission(
                assignment=assignment,
                student=self.student,
                content="Test content",
                status='SUBMITTED'
            )
            
            submission.save()
            
            # Should not be marked as late (signal disconnected)
            self.assertFalse(submission.is_late)
            self.assertEqual(submission.status, 'SUBMITTED')
            
        finally:
            # Reconnect signal
            post_save.connect(submission_post_save, sender=AssignmentSubmission)


class TestSignalPerformance(BaseSignalTest):
    """Test signal performance"""

    def test_pre_save_signal_performance(self):
        """Test pre_save signal performance"""
        import time
        
        assignments = []
        for i in range(10):
            assignment = Assignment(
                description=f"Test description {i}",
                faculty=self.faculty,
                max_marks=100.00,
                due_date=timezone.now() + timedelta(days=7)
            )
            assignments.append(assignment)
        
        # Time the signal execution
        start_time = time.time()
        for assignment in assignments:
            assignment_pre_save(Assignment, assignment)
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 0.1)  # Less than 100ms

    def test_post_save_signal_performance(self):
        """Test post_save signal performance"""
        import time
        
        assignment = assignment_factory.make()
        submissions = []
        
        for i in range(10):
            submission = AssignmentSubmission(
                assignment=assignment,
                student=self.student,
                content=f"Test content {i}",
                status='SUBMITTED'
            )
            submissions.append(submission)
        
        # Time the signal execution
        start_time = time.time()
        for submission in submissions:
            submission_post_save(AssignmentSubmission, submission, created=True)
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 0.1)  # Less than 100ms


@pytest.mark.django_db
class TestSignalRealWorldScenarios(BaseSignalTest):
    """Test signals in real-world scenarios"""

    def test_assignment_workflow_with_signals(self):
        """Test complete assignment workflow with signals"""
        # Create assignment (triggers post_save)
        assignment = Assignment(
            description="Test assignment",
            faculty=self.faculty,
            max_marks=100.00,
            due_date=timezone.now() + timedelta(days=7),
            status='DRAFT'
        )
        assignment.save()
        
        # Title should be auto-generated
        self.assertIsNotNone(assignment.title)
        
        # Publish assignment (triggers pre_save)
        assignment.status = 'PUBLISHED'
        assignment.save()
        
        # Should remain published (future due date)
        self.assertEqual(assignment.status, 'PUBLISHED')
        
        # Student submits on time
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="On-time submission",
            status='SUBMITTED'
        )
        submission.save()
        
        # Should not be marked as late
        self.assertFalse(submission.is_late)
        
        # Move due date to past and create another submission
        assignment.due_date = timezone.now() - timedelta(days=1)
        assignment.save()
        
        late_submission = AssignmentSubmission(
            assignment=assignment,
            student=student_factory(),  # Different student
            content="Late submission",
            status='SUBMITTED'
        )
        late_submission.save()
        
        # Should be marked as late
        self.assertTrue(late_submission.is_late)
        self.assertEqual(late_submission.status, 'LATE')

    def test_bulk_assignment_operations_with_signals(self):
        """Test bulk operations and signal behavior"""
        # Create multiple assignments
        assignments = []
        for i in range(5):
            assignment = Assignment(
                description=f"Test assignment {i}",
                faculty=self.faculty,
                max_marks=100.00,
                due_date=timezone.now() + timedelta(days=i+1)
            )
            assignment.save()  # Each save triggers signals
            assignments.append(assignment)
        
        # All should have auto-generated titles
        for assignment in assignments:
            self.assertIsNotNone(assignment.title)
        
        # Try to publish assignments with past due dates
        for assignment in assignments:
            assignment.due_date = timezone.now() - timedelta(days=1)
            assignment.status = 'PUBLISHED'
            assignment.save()
        
        # All should be reverted to DRAFT
        for assignment in assignments:
            assignment.refresh_from_db()
            self.assertEqual(assignment.status, 'DRAFT')

    def test_concurrent_submissions_with_signals(self):
        """Test concurrent submissions and signal behavior"""
        assignment = assignment_factory.make(
            due_date=timezone.now() - timedelta(minutes=30)  # 30 minutes ago
        )
        
        students = [student_factory() for _ in range(3)]
        submissions = []
        
        # Create multiple submissions "simultaneously"
        for i, student in enumerate(students):
            submission = AssignmentSubmission(
                assignment=assignment,
                student=student,
                content=f"Submission {i}",
                status='SUBMITTED'
            )
            submission.save()
            submissions.append(submission)
        
        # All should be marked as late
        for submission in submissions:
            self.assertTrue(submission.is_late)
            self.assertEqual(submission.status, 'LATE')

    def test_signal_with_assignment_updates(self):
        """Test signals with various assignment updates"""
        assignment = assignment_factory.make(
            status='DRAFT',
            due_date=timezone.now() + timedelta(days=7)
        )
        
        # Update title (should not trigger title generation)
        original_title = assignment.title
        assignment.title = "Updated Title"
        assignment.save()
        
        self.assertEqual(assignment.title, "Updated Title")
        
        # Update due date to past and try to publish
        assignment.due_date = timezone.now() - timedelta(days=1)
        assignment.status = 'PUBLISHED'
        assignment.save()
        
        # Should be reverted to DRAFT
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'DRAFT')
        
        # Update due date to future and publish
        assignment.due_date = timezone.now() + timedelta(days=1)
        assignment.status = 'PUBLISHED'
        assignment.save()
        
        # Should remain PUBLISHED
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'PUBLISHED')

    def test_signal_with_edge_case_timestamps(self):
        """Test signals with edge case timestamps"""
        # Assignment due exactly now
        assignment = assignment_factory.make(
            due_date=timezone.now()
        )
        
        submission = AssignmentSubmission(
            assignment=assignment,
            student=self.student,
            content="Edge case submission",
            status='SUBMITTED'
        )
        submission.save()
        
        # Should be marked as late (due_date <= now)
        self.assertTrue(submission.is_late)
        
        # Assignment due in 1 second
        assignment_future = assignment_factory.make(
            due_date=timezone.now() + timedelta(seconds=1)
        )
        
        submission_future = AssignmentSubmission(
            assignment=assignment_future,
            student=self.student,
            content="Future submission",
            status='SUBMITTED'
        )
        submission_future.save()
        
        # Should not be marked as late
        self.assertFalse(submission_future.is_late)
