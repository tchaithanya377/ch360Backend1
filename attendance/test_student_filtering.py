"""
Test script to verify that student filtering works correctly in the attendance admin form.
This is a simple test to ensure the logic works as expected.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from students.models import Student, StudentBatch, AcademicYear
from academics.models import Course, CourseSection, AcademicProgram
from departments.models import Department
from faculty.models import Faculty
from attendance.models import AttendanceSession
from attendance.views import get_students_for_session

User = get_user_model()


class AttendanceStudentFilteringTest(TestCase):
    """Test student filtering functionality for attendance records"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            description='Computer Science Department'
        )
        
        # Create academic program
        self.program = AcademicProgram.objects.create(
            name='Bachelor of Computer Science',
            code='BCS',
            level='UG',
            department=self.department,
            total_credits=120
        )
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date='2024-08-01',
            end_date='2025-07-31',
            is_current=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.program,
            academic_year=self.academic_year,
            semester='1',
            year_of_study='1',
            section='A',
            batch_name='CS-2024-1-A',
            batch_code='CS-2024-1-A-001'
        )
        
        # Create faculty
        self.faculty = Faculty.objects.create(
            employee_id='F001',
            first_name='John',
            last_name='Doe',
            email='john.doe@test.com',
            department=self.department
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            title='Introduction to Programming',
            description='Basic programming concepts',
            level='UG',
            credits=3,
            department=self.department
        )
        
        # Create course section
        self.course_section = CourseSection.objects.create(
            course=self.course,
            student_batch=self.student_batch,
            section_type='LECTURE',
            faculty=self.faculty
        )
        
        # Create students
        self.student1 = Student.objects.create(
            roll_number='CS2024001',
            first_name='Alice',
            last_name='Smith',
            student_batch=self.student_batch
        )
        
        self.student2 = Student.objects.create(
            roll_number='CS2024002',
            first_name='Bob',
            last_name='Johnson',
            student_batch=self.student_batch
        )
        
        # Create a student from a different batch
        self.other_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.program,
            academic_year=self.academic_year,
            semester='1',
            year_of_study='1',
            section='B',
            batch_name='CS-2024-1-B',
            batch_code='CS-2024-1-B-001'
        )
        
        self.other_student = Student.objects.create(
            roll_number='CS2024003',
            first_name='Charlie',
            last_name='Brown',
            student_batch=self.other_batch
        )
        
        # Create attendance session
        self.attendance_session = AttendanceSession.objects.create(
            course_section=self.course_section,
            date='2024-09-15',
            start_time='09:00:00',
            end_time='10:00:00',
            room='A101'
        )
        
        self.client = Client()
        self.client.login(username='testadmin', password='testpass123')
    
    def test_get_students_for_session(self):
        """Test that the AJAX view returns correct students for a session"""
        # Test with valid session
        response = self.client.get(
            '/admin/attendance/attendance-record/get-students-for-session/',
            {'session_id': self.attendance_session.id}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return only students from the same batch
        student_ids = [student['id'] for student in data['students']]
        self.assertIn(str(self.student1.id), student_ids)
        self.assertIn(str(self.student2.id), student_ids)
        self.assertNotIn(str(self.other_student.id), student_ids)
        
        # Verify the student data format
        if data['students']:
            student = data['students'][0]
            self.assertIn('id', student)
            self.assertIn('roll_number', student)
            self.assertIn('full_name', student)
        
        # Test with invalid session
        response = self.client.get(
            '/admin/attendance/attendance-record/get-students-for-session/',
            {'session_id': 99999}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['students'], [])
        
        # Test with no session
        response = self.client.get(
            '/admin/attendance/attendance-record/get-students-for-session/',
            {}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['students'], [])
    
    def test_attendance_record_form_filtering(self):
        """Test that the admin form correctly filters students"""
        from attendance.admin import AttendanceRecordForm
        
        # Test form with session
        form_data = {
            'session': self.attendance_session.id,
            'student': self.student1.id,
            'status': 'PRESENT'
        }
        
        form = AttendanceRecordForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Check that the student queryset is filtered correctly
        student_queryset = form.fields['student'].queryset
        student_ids = list(student_queryset.values_list('id', flat=True))
        
        self.assertIn(self.student1.id, student_ids)
        self.assertIn(self.student2.id, student_ids)
        self.assertNotIn(self.other_student.id, student_ids)
    
    def test_student_display_format(self):
        """Test that students are displayed in the correct format"""
        response = self.client.get(
            '/admin/attendance/attendance-record/get-students-for-session/',
            {'session_id': self.attendance_session.id}
        )
        
        data = response.json()
        student = data['students'][0]
        
        # Check that the student data has the expected format
        self.assertIn('id', student)
        self.assertIn('roll_number', student)
        self.assertIn('full_name', student)
        self.assertEqual(student['roll_number'], 'CS2024001')
        self.assertEqual(student['full_name'], 'Alice Smith')
