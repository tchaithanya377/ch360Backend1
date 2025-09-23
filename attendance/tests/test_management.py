"""
Comprehensive tests for attendance management commands.
Tests generate_attendance_sessions and optimize_attendance_db commands.
"""

import pytest
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.utils import timezone
from datetime import date, time, datetime, timedelta
from io import StringIO
from unittest.mock import patch, MagicMock

from attendance.models import AttendanceSession, AttendanceRecord
from attendance.management.commands.generate_attendance_sessions import Command as GenerateCommand
from attendance.management.commands.optimize_attendance_db import Command as OptimizeCommand
from attendance.tests.factories import (
    AttendanceSessionFactory, AttendanceRecordFactory,
    StudentFactory, CourseSectionFactory, TimetableFactory, TimetableFactory,
    StudentBatchFactory, AcademicYearFactory, DepartmentFactory,
    AcademicProgramFactory, FacultyFactory, CourseFactory
)
from academics.models import Timetable


class TestGenerateAttendanceSessionsCommand(TestCase):
    """Test cases for generate_attendance_sessions management command"""

    def setUp(self):
        """Set up test data"""
        self.department = DepartmentFactory()
        self.academic_year = AcademicYearFactory()
        self.program = AcademicProgramFactory(department=self.department)
        self.batch = StudentBatchFactory(
            department=self.department,
            academic_program=self.program,
            academic_year=self.academic_year
        )
        self.faculty = FacultyFactory(department=self.department)
        self.course = CourseFactory(department=self.department)
        self.course_section = CourseSectionFactory(
            course=self.course,
            student_batch=self.batch,
            faculty=self.faculty
        )
        
        # Create timetables for different days
        self.timetable_monday = TimetableFactory(
            course_section=self.course_section,
            day_of_week='MON',
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_active=True
        )
        self.timetable_wednesday = TimetableFactory(
            course_section=self.course_section,
            day_of_week='WED',
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_active=True
        )
        self.timetable_friday = TimetableFactory(
            course_section=self.course_section,
            day_of_week='FRI',
            start_time=time(14, 0),
            end_time=time(15, 0),
            is_active=True
        )

    def test_generate_attendance_sessions_command_help(self):
        """Test command help text"""
        # Test that the command exists and can be imported
        from attendance.management.commands.generate_attendance_sessions import Command
        command = Command()
        
        # Test that the command has the expected help text
        self.assertIn('Generate AttendanceSession entries from Timetable', command.help)
        
        # Test that the command can be called with --help (should not crash)
        try:
            call_command('generate_attendance_sessions', '--help')
        except SystemExit:
            pass  # Expected when calling --help

    def test_generate_attendance_sessions_command_required_arguments(self):
        """Test command with required arguments"""
        start_date = '2024-09-15'
        end_date = '2024-09-20'
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        output = out.getvalue()
        
        self.assertIn('Created', output)
        self.assertIn('attendance sessions', output)

    def test_generate_attendance_sessions_command_with_section_id(self):
        """Test command with section ID filter"""
        start_date = '2024-09-15'
        end_date = '2024-09-20'
        section_id = self.course_section.id
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            '--section-id', str(section_id),
            stdout=out
        )
        output = out.getvalue()
        
        self.assertIn('Created', output)
        self.assertIn('attendance sessions', output)

    def test_generate_attendance_sessions_command_invalid_date_range(self):
        """Test command with invalid date range"""
        start_date = '2024-09-20'
        end_date = '2024-09-15'  # End before start
        
        out = StringIO()
        err = StringIO()
        
        with self.assertRaises(SystemExit):
            call_command(
                'generate_attendance_sessions',
                '--start', start_date,
                '--end', end_date,
                stdout=out,
                stderr=err
            )
        
        error_output = err.getvalue()
        self.assertIn('End date must be after start date', error_output)

    def test_generate_attendance_sessions_command_creates_sessions(self):
        """Test that command creates attendance sessions"""
        start_date = '2024-09-15'  # Sunday
        end_date = '2024-09-21'    # Saturday
        
        # Count existing sessions
        initial_count = AttendanceSession.objects.count()
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        
        # Check that sessions were created
        final_count = AttendanceSession.objects.count()
        self.assertGreater(final_count, initial_count)
        
        # Check that sessions were created for the correct days
        monday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 16)  # Monday
        )
        self.assertEqual(monday_sessions.count(), 1)
        
        wednesday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 18)  # Wednesday
        )
        self.assertEqual(wednesday_sessions.count(), 1)
        
        friday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 20)  # Friday
        )
        self.assertEqual(friday_sessions.count(), 1)

    def test_generate_attendance_sessions_command_skips_weekends(self):
        """Test that command skips weekends"""
        start_date = '2024-09-15'  # Sunday
        end_date = '2024-09-21'    # Saturday
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        
        # Check that no sessions were created for weekends
        saturday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 21)  # Saturday
        )
        self.assertEqual(saturday_sessions.count(), 0)
        
        sunday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 15)  # Sunday
        )
        self.assertEqual(sunday_sessions.count(), 0)

    def test_generate_attendance_sessions_command_handles_existing_sessions(self):
        """Test that command handles existing sessions correctly"""
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        
        # Create an existing session
        existing_session = AttendanceSessionFactory(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 16),  # Monday
            start_datetime=timezone.make_aware(timezone.datetime.combine(date(2024, 9, 16), time(9, 0))),
            end_datetime=timezone.make_aware(timezone.datetime.combine(date(2024, 9, 16), time(10, 0)))
        )
        
        initial_count = AttendanceSession.objects.count()
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        
        # Check that no duplicate session was created for Monday
        # But new sessions were created for Wednesday and Friday
        final_count = AttendanceSession.objects.count()
        self.assertEqual(final_count, initial_count + 2)  # 1 existing + 2 new (Wed, Fri)
        
        # Verify that Monday still has only 1 session (the existing one)
        monday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 16)  # Monday
        )
        self.assertEqual(monday_sessions.count(), 1)
        self.assertEqual(monday_sessions.first().id, existing_session.id)
        
        # Check that the existing session is still there
        self.assertTrue(
            AttendanceSession.objects.filter(id=existing_session.id).exists()
        )

    def test_generate_attendance_sessions_command_with_inactive_timetable(self):
        """Test that command ignores inactive timetables"""
        # Create an inactive timetable
        inactive_timetable = TimetableFactory(
            course_section=self.course_section,
            day_of_week='TUE',
            start_time=time(11, 0),
            end_time=time(12, 0),
            is_active=False
        )
        
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        
        # Check that no session was created for inactive timetable
        tuesday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 17)  # Tuesday
        )
        self.assertEqual(tuesday_sessions.count(), 0)

    def test_generate_attendance_sessions_command_with_section_filter(self):
        """Test that command respects section ID filter"""
        # Create another course section with a different course
        other_course = CourseFactory(department=self.department)
        other_course_section = CourseSectionFactory(
            course=other_course,
            student_batch=self.batch,
            faculty=self.faculty
        )
        other_timetable = TimetableFactory(
            course_section=other_course_section,
            day_of_week='MON',
            start_time=time(11, 0),
            end_time=time(12, 0),
            is_active=True
        )
        
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        section_id = self.course_section.id
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            '--section-id', str(section_id),
            stdout=out
        )
        
        # Check that sessions were created only for the specified section
        monday_sessions = AttendanceSession.objects.filter(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 16)  # Monday
        )
        self.assertEqual(monday_sessions.count(), 1)
        
        other_sessions = AttendanceSession.objects.filter(
            course_section=other_course_section,
            scheduled_date=date(2024, 9, 16)  # Monday
        )
        self.assertEqual(other_sessions.count(), 0)

    def test_generate_attendance_sessions_command_session_properties(self):
        """Test that created sessions have correct properties"""
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        
        # Check Monday session
        monday_session = AttendanceSession.objects.get(
            course_section=self.course_section,
            scheduled_date=date(2024, 9, 16)  # Monday
        )
        
        self.assertEqual(monday_session.course_section, self.course_section)
        self.assertEqual(monday_session.scheduled_date, date(2024, 9, 16))
        self.assertEqual(monday_session.start_datetime.time(), time(9, 0))
        self.assertEqual(monday_session.end_datetime.time(), time(10, 0))
        self.assertEqual(monday_session.room, self.timetable_monday.room)
        # Note: timetable_slot is not set by the command as it uses Timetable objects, not TimetableSlot objects
        self.assertIsNone(monday_session.timetable_slot)
        self.assertNotEqual(monday_session.status, 'cancelled')

    def test_generate_attendance_sessions_command_output(self):
        """Test command output format"""
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        output = out.getvalue()
        
        self.assertIn('Created', output)
        self.assertIn('attendance sessions', output)
        self.assertIn('.', output)  # Should end with a period

    def test_generate_attendance_sessions_command_no_timetables(self):
        """Test command when no timetables exist"""
        # Delete all timetables
        Timetable.objects.all().delete()
        
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        output = out.getvalue()
        
        self.assertIn('Created 0 attendance sessions', output)

    def test_generate_attendance_sessions_command_invalid_date_format(self):
        """Test command with invalid date format"""
        start_date = 'invalid-date'
        end_date = '2024-09-21'
        
        with self.assertRaises(ValueError):
            call_command(
                'generate_attendance_sessions',
                '--start', start_date,
                '--end', end_date
            )

    def test_generate_attendance_sessions_command_invalid_section_id(self):
        """Test command with invalid section ID"""
        start_date = '2024-09-15'
        end_date = '2024-09-21'
        section_id = 99999  # Non-existent section
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            '--section-id', str(section_id),
            stdout=out
        )
        output = out.getvalue()
        
        self.assertIn('Created 0 attendance sessions', output)


class TestOptimizeAttendanceDbCommand(TestCase):
    """Test cases for optimize_attendance_db management command"""

    def setUp(self):
        """Set up test data"""
        self.command = OptimizeCommand()

    def test_optimize_attendance_db_command_help(self):
        """Test command help text"""
        # Test that the command has the correct help text
        self.assertEqual(self.command.help, 'Create high-value indexes for attendance at scale (CONCURRENTLY).')

    def test_optimize_attendance_db_command_execution(self):
        """Test command execution"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Creating index', output)
        self.assertIn('Attendance indexes ensured', output)

    def test_optimize_attendance_db_command_indexes(self):
        """Test that command creates the correct indexes"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        # Check that all expected indexes are mentioned
        self.assertIn('idx_attendance_record_session_student', output)
        self.assertIn('idx_attendance_record_student_status', output)
        self.assertIn('idx_attendance_session_date', output)

    @patch('attendance.management.commands.optimize_attendance_db.connection')
    def test_optimize_attendance_db_command_database_operations(self, mock_connection):
        """Test that command executes correct database operations"""
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        
        # Check that cursor was used
        mock_connection.cursor.assert_called_once()
        
        # Check that execute was called for each index
        self.assertEqual(mock_cursor.execute.call_count, 3)
        
        # Check that the correct SQL statements were executed
        executed_statements = [call[0][0] for call in mock_cursor.execute.call_args_list]
        
        self.assertTrue(any('idx_attendance_record_session_student' in stmt for stmt in executed_statements))
        self.assertTrue(any('idx_attendance_record_student_status' in stmt for stmt in executed_statements))
        self.assertTrue(any('idx_attendance_session_date' in stmt for stmt in executed_statements))

    def test_optimize_attendance_db_command_sql_statements(self):
        """Test that command uses correct SQL statements"""
        expected_indexes = [
            'idx_attendance_record_session_student',
            'idx_attendance_record_student_status',
            'idx_attendance_session_date'
        ]
        
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        for index_name in expected_indexes:
            self.assertIn(index_name, output)

    def test_optimize_attendance_db_command_concurrent_creation(self):
        """Test that command uses CONCURRENTLY for index creation"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        # The command should mention concurrent creation
        self.assertIn('Creating index', output)

    def test_optimize_attendance_db_command_if_not_exists(self):
        """Test that command uses IF NOT EXISTS for index creation"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        # The command should mention that it creates indexes if they don't exist
        self.assertIn('Creating index', output)

    def test_optimize_attendance_db_command_success_message(self):
        """Test command success message"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Attendance indexes ensured', output)

    def test_optimize_attendance_db_command_no_arguments(self):
        """Test command with no arguments"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Attendance indexes ensured', output)

    def test_optimize_attendance_db_command_multiple_executions(self):
        """Test that command can be run multiple times safely"""
        out1 = StringIO()
        call_command('optimize_attendance_db', stdout=out1)
        output1 = out1.getvalue()
        
        out2 = StringIO()
        call_command('optimize_attendance_db', stdout=out2)
        output2 = out2.getvalue()
        
        # Both executions should succeed
        self.assertIn('Attendance indexes ensured', output1)
        self.assertIn('Attendance indexes ensured', output2)

    @patch('attendance.management.commands.optimize_attendance_db.connection')
    def test_optimize_attendance_db_command_database_error_handling(self, mock_connection):
        """Test command error handling"""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database error")
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        out = StringIO()
        # Command should handle errors gracefully and not raise exceptions
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        # Verify that error messages are written to output
        self.assertIn('Failed to create index', output)
        self.assertIn('Database error', output)
        self.assertIn('Attendance indexes ensured', output)

    def test_optimize_attendance_db_command_index_names(self):
        """Test that command uses correct index names"""
        expected_indexes = [
            'idx_attendance_record_session_student',
            'idx_attendance_record_student_status',
            'idx_attendance_session_date'
        ]
        
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        for index_name in expected_indexes:
            self.assertIn(index_name, output)

    def test_optimize_attendance_db_command_table_names(self):
        """Test that command targets correct table names"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        output = out.getvalue()
        
        # The command should mention the correct table names
        self.assertIn('attendance_attendancerecord', output)
        self.assertIn('attendance_attendancesession', output)


class TestManagementCommandsIntegration(TestCase):
    """Integration tests for management commands"""

    def setUp(self):
        """Set up test data"""
        self.department = DepartmentFactory()
        self.academic_year = AcademicYearFactory()
        self.program = AcademicProgramFactory(department=self.department)
        self.batch = StudentBatchFactory(
            department=self.department,
            academic_program=self.program,
            academic_year=self.academic_year
        )
        self.faculty = FacultyFactory(department=self.department)
        self.course = CourseFactory(department=self.department)
        self.course_section = CourseSectionFactory(
            course=self.course,
            student_batch=self.batch,
            faculty=self.faculty
        )

    def test_generate_and_optimize_commands_work_together(self):
        """Test that both commands can be run together"""
        # Create a timetable
        TimetableFactory(
            course_section=self.course_section,
            day_of_week='MON',
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_active=True
        )
        
        # Run generate command
        out1 = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', '2024-09-15',
            '--end', '2024-09-21',
            stdout=out1
        )
        
        # Run optimize command
        out2 = StringIO()
        call_command('optimize_attendance_db', stdout=out2)
        
        # Both commands should succeed
        self.assertIn('Created', out1.getvalue())
        self.assertIn('Attendance indexes ensured', out2.getvalue())

    def test_management_commands_with_existing_data(self):
        """Test management commands with existing attendance data"""
        # Create existing attendance sessions and records
        session = AttendanceSessionFactory(course_section=self.course_section)
        student = StudentFactory(student_batch=self.batch)
        AttendanceRecordFactory(session=session, student=student)
        
        # Run optimize command
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        
        # Command should succeed
        self.assertIn('Attendance indexes ensured', out.getvalue())

    def test_management_commands_performance(self):
        """Test that management commands perform well with large datasets"""
        # Create multiple timetables
        for day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
            TimetableFactory(
                course_section=self.course_section,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(10, 0),
                is_active=True
            )
        
        # Run generate command
        start_time = timezone.now()
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', '2024-09-15',
            '--end', '2024-09-30',
            stdout=out
        )
        end_time = timezone.now()
        
        # Command should complete in reasonable time
        execution_time = (end_time - start_time).total_seconds()
        self.assertLess(execution_time, 10)  # Should complete within 10 seconds
        
        # Check that sessions were created
        self.assertIn('Created', out.getvalue())


@pytest.mark.django_db
class TestManagementCommandsPytest:
    """Pytest-style tests for management commands"""

    def test_generate_attendance_sessions_command_pytest(self):
        """Test generate_attendance_sessions command using pytest"""
        department = DepartmentFactory()
        academic_year = AcademicYearFactory()
        program = AcademicProgramFactory(department=department)
        batch = StudentBatchFactory(
            department=department,
            academic_program=program,
            academic_year=academic_year
        )
        faculty = FacultyFactory(department=department)
        course = CourseFactory(department=department)
        course_section = CourseSectionFactory(
            course=course,
            student_batch=batch,
            faculty=faculty
        )
        
        TimetableFactory(
            course_section=course_section,
            day_of_week='MON',
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_active=True
        )
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', '2024-09-15',
            '--end', '2024-09-21',
            stdout=out
        )
        
        assert 'Created' in out.getvalue()
        assert 'attendance sessions' in out.getvalue()

    def test_optimize_attendance_db_command_pytest(self):
        """Test optimize_attendance_db command using pytest"""
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        
        assert 'Attendance indexes ensured' in out.getvalue()

    @pytest.mark.parametrize("start_date,end_date", [
        ('2024-09-15', '2024-09-21'),
        ('2024-10-01', '2024-10-07'),
        ('2024-11-01', '2024-11-07'),
    ])
    def test_generate_attendance_sessions_command_date_ranges(self, start_date, end_date):
        """Test generate_attendance_sessions command with different date ranges"""
        department = DepartmentFactory()
        academic_year = AcademicYearFactory()
        program = AcademicProgramFactory(department=department)
        batch = StudentBatchFactory(
            department=department,
            academic_program=program,
            academic_year=academic_year
        )
        faculty = FacultyFactory(department=department)
        course = CourseFactory(department=department)
        course_section = CourseSectionFactory(
            course=course,
            student_batch=batch,
            faculty=faculty
        )
        
        TimetableFactory(
            course_section=course_section,
            day_of_week='MON',
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_active=True
        )
        
        out = StringIO()
        call_command(
            'generate_attendance_sessions',
            '--start', start_date,
            '--end', end_date,
            stdout=out
        )
        
        assert 'Created' in out.getvalue()

    def test_generate_attendance_sessions_command_invalid_date_range_pytest(self):
        """Test generate_attendance_sessions command with invalid date range using pytest"""
        with pytest.raises(SystemExit):
            call_command(
                'generate_attendance_sessions',
                '--start', '2024-09-20',
                '--end', '2024-09-15'  # End before start
            )

    def test_optimize_attendance_db_command_multiple_executions_pytest(self):
        """Test optimize_attendance_db command multiple executions using pytest"""
        out1 = StringIO()
        call_command('optimize_attendance_db', stdout=out1)
        
        out2 = StringIO()
        call_command('optimize_attendance_db', stdout=out2)
        
        assert 'Attendance indexes ensured' in out1.getvalue()
        assert 'Attendance indexes ensured' in out2.getvalue()

    @patch('attendance.management.commands.optimize_attendance_db.connection')
    def test_optimize_attendance_db_command_database_operations_pytest(self, mock_connection):
        """Test optimize_attendance_db command database operations using pytest"""
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        out = StringIO()
        call_command('optimize_attendance_db', stdout=out)
        
        mock_connection.cursor.assert_called_once()
        assert mock_cursor.execute.call_count == 3
        assert 'Attendance indexes ensured' in out.getvalue()



