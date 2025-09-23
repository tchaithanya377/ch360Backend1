from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from students.models import (
    Student, StudentRepresentative, StudentRepresentativeActivity,
    StudentFeedback, StudentRepresentativeType, AcademicYear, StudentBatch
)
from departments.models import Department
from academics.models import AcademicProgram
from django.utils import timezone

User = get_user_model()


class StudentPortalAuthenticationTestCase(APITestCase):
    """Test cases for student portal authentication"""
    
    def setUp(self):
        # Create Student group
        self.student_group = Group.objects.create(name='Student')
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=timezone.now().date(),
            end_date=timezone.now().date().replace(year=timezone.now().year + 1),
            is_current=True,
            is_active=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            is_active=True
        )
        
        # Create academic program
        self.academic_program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH-CS',
            department=self.department,
            is_active=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.academic_program,
            academic_year=self.academic_year,
            semester='5',
            year_of_study='3',
            section='A',
            batch_name='CS-2024-3-A',
            batch_code='CS-2024-3-A',
            max_capacity=70,
            current_count=0,
            is_active=True
        )
        
        # Create test student
        self.student = Student.objects.create(
            roll_number='22CS001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            date_of_birth='2000-01-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        # Get the auto-created user
        self.user = self.student.user
        
    def test_student_login_with_roll_number(self):
        """Test student login using roll number"""
        url = '/api/student-portal/auth/login/'
        data = {
            'username': '22CS001',
            'password': 'Campus@360'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('student_profile', response.data)
        self.assertEqual(response.data['student_profile']['roll_number'], '22CS001')
        self.assertIn('Student', response.data['roles'])
    
    def test_student_login_with_email(self):
        """Test student login using email"""
        url = '/api/student-portal/auth/login/'
        data = {
            'email': 'john.doe@example.com',
            'password': 'Campus@360'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('student_profile', response.data)
    
    def test_non_student_login_denied(self):
        """Test that non-student users cannot login via student portal"""
        # Create a regular user without Student role
        regular_user = User.objects.create_user(
            email='regular@example.com',
            username='regular',
            password='password123'
        )
        
        url = '/api/student-portal/auth/login/'
        data = {
            'username': 'regular',
            'password': 'password123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Access denied', str(response.data))
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = '/api/student-portal/auth/login/'
        data = {
            'username': '22CS001',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid credentials', str(response.data))


class StudentPortalDashboardTestCase(APITestCase):
    """Test cases for student portal dashboard"""
    
    def setUp(self):
        # Create Student group
        self.student_group = Group.objects.create(name='Student')
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=timezone.now().date(),
            end_date=timezone.now().date().replace(year=timezone.now().year + 1),
            is_current=True,
            is_active=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            is_active=True
        )
        
        # Create academic program
        self.academic_program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH-CS',
            department=self.department,
            is_active=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.academic_program,
            academic_year=self.academic_year,
            semester='5',
            year_of_study='3',
            section='A',
            batch_name='CS-2024-3-A',
            batch_code='CS-2024-3-A',
            max_capacity=70,
            current_count=0,
            is_active=True
        )
        
        # Create test student
        self.student = Student.objects.create(
            roll_number='22CS001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            date_of_birth='2000-01-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        # Get the auto-created user
        self.user = self.student.user
        
    def test_student_dashboard_access(self):
        """Test student dashboard access"""
        # Login as student
        self.client.force_authenticate(user=self.user)
        
        url = '/api/student-portal/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('student', response.data)
        self.assertIn('academic_summary', response.data)
        self.assertIn('stats', response.data)
        self.assertIn('recent_activities', response.data)
        self.assertIn('announcements', response.data)
        self.assertIn('upcoming_events', response.data)
        self.assertIn('feedback_summary', response.data)
    
    def test_unauthorized_dashboard_access(self):
        """Test unauthorized access to dashboard"""
        url = '/api/student-portal/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_academic_summary(self):
        """Test dashboard academic summary data"""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/student-portal/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        academic_summary = response.data['academic_summary']
        self.assertEqual(academic_summary['current_semester'], '5')
        self.assertEqual(academic_summary['year_of_study'], '3')
        self.assertEqual(academic_summary['department'], 'Computer Science')
        self.assertEqual(academic_summary['section'], 'A')


class StudentRepresentativeTestCase(APITestCase):
    """Test cases for student representatives"""
    
    def setUp(self):
        # Create Student group
        self.student_group = Group.objects.create(name='Student')
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=timezone.now().date(),
            end_date=timezone.now().date().replace(year=timezone.now().year + 1),
            is_current=True,
            is_active=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            is_active=True
        )
        
        # Create academic program
        self.academic_program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH-CS',
            department=self.department,
            is_active=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.academic_program,
            academic_year=self.academic_year,
            semester='5',
            year_of_study='3',
            section='A',
            batch_name='CS-2024-3-A',
            batch_code='CS-2024-3-A',
            max_capacity=70,
            current_count=0,
            is_active=True
        )
        
        # Create test students
        self.student1 = Student.objects.create(
            roll_number='22CS001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            date_of_birth='2000-01-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        self.student2 = Student.objects.create(
            roll_number='22CS002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            date_of_birth='2000-02-15',
            gender='F',
            student_batch=self.student_batch
        )
        
        # Get the auto-created users
        self.user1 = self.student1.user
        self.user2 = self.student2.user
        
        # Create Class Representative
        self.cr_representative = StudentRepresentative.objects.create(
            student=self.student1,
            representative_type=StudentRepresentativeType.CR,
            academic_year=self.academic_year,
            semester='5',
            department=self.department,
            academic_program=self.academic_program,
            year_of_study='3',
            section='A',
            is_active=True,
            start_date=timezone.now().date(),
            responsibilities='Represent class in academic matters',
            contact_email=self.student1.email,
            contact_phone=self.student1.student_mobile
        )
        
        # Create Ladies Representative
        self.lr_representative = StudentRepresentative.objects.create(
            student=self.student2,
            representative_type=StudentRepresentativeType.LR,
            academic_year=self.academic_year,
            semester='5',
            department=self.department,
            academic_program=self.academic_program,
            year_of_study='3',
            section='A',
            is_active=True,
            start_date=timezone.now().date(),
            responsibilities='Represent female students',
            contact_email=self.student2.email,
            contact_phone=self.student2.student_mobile
        )
    
    def test_cr_dashboard_access(self):
        """Test Class Representative dashboard access"""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/student-portal/representative/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('representative', response.data)
        self.assertIn('represented_students_count', response.data)
        self.assertIn('recent_activities', response.data)
        self.assertIn('pending_feedback', response.data)
        self.assertIn('feedback_stats', response.data)
    
    def test_lr_dashboard_access(self):
        """Test Ladies Representative dashboard access"""
        self.client.force_authenticate(user=self.user2)
        
        url = '/api/student-portal/representative/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('representative', response.data)
        self.assertEqual(response.data['representative']['representative_type'], 'LR')
    
    def test_regular_student_cannot_access_representative_dashboard(self):
        """Test that regular students cannot access representative dashboard"""
        # Create a regular student without representative role
        regular_student = Student.objects.create(
            roll_number='22CS003',
            first_name='Bob',
            last_name='Johnson',
            email='bob.johnson@example.com',
            date_of_birth='2000-03-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        self.client.force_authenticate(user=regular_student.user)
        
        url = '/api/student-portal/representative/dashboard/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_representatives_list(self):
        """Test listing representatives"""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/student-portal/representatives/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # CR and LR
    
    def test_my_representatives(self):
        """Test getting representatives for current student's class"""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/student-portal/representatives/my_representatives/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # CR and LR for the same class


class StudentFeedbackTestCase(APITestCase):
    """Test cases for student feedback system"""
    
    def setUp(self):
        # Create Student group
        self.student_group = Group.objects.create(name='Student')
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=timezone.now().date(),
            end_date=timezone.now().date().replace(year=timezone.now().year + 1),
            is_current=True,
            is_active=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            is_active=True
        )
        
        # Create academic program
        self.academic_program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH-CS',
            department=self.department,
            is_active=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.academic_program,
            academic_year=self.academic_year,
            semester='5',
            year_of_study='3',
            section='A',
            batch_name='CS-2024-3-A',
            batch_code='CS-2024-3-A',
            max_capacity=70,
            current_count=0,
            is_active=True
        )
        
        # Create test students
        self.student1 = Student.objects.create(
            roll_number='22CS001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            date_of_birth='2000-01-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        self.student2 = Student.objects.create(
            roll_number='22CS002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            date_of_birth='2000-02-15',
            gender='F',
            student_batch=self.student_batch
        )
        
        # Get the auto-created users
        self.user1 = self.student1.user
        self.user2 = self.student2.user
        
        # Create Class Representative
        self.cr_representative = StudentRepresentative.objects.create(
            student=self.student1,
            representative_type=StudentRepresentativeType.CR,
            academic_year=self.academic_year,
            semester='5',
            department=self.department,
            academic_program=self.academic_program,
            year_of_study='3',
            section='A',
            is_active=True,
            start_date=timezone.now().date(),
            responsibilities='Represent class in academic matters',
            contact_email=self.student1.email,
            contact_phone=self.student1.student_mobile
        )
    
    def test_student_can_submit_feedback(self):
        """Test that students can submit feedback"""
        self.client.force_authenticate(user=self.user2)
        
        url = '/api/student-portal/feedback/'
        data = {
            'feedback_type': 'ACADEMIC',
            'title': 'Library Issue',
            'description': 'Library computers are not working properly',
            'priority': 'MEDIUM'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Library Issue')
        self.assertEqual(response.data['student'], str(self.student2.id))
    
    def test_representative_can_handle_feedback(self):
        """Test that representatives can handle feedback"""
        # First, create feedback
        feedback = StudentFeedback.objects.create(
            student=self.student2,
            feedback_type='ACADEMIC',
            title='Test Feedback',
            description='Test description',
            priority='MEDIUM'
        )
        
        # Login as representative
        self.client.force_authenticate(user=self.user1)
        
        # Assign feedback to representative
        url = f'/api/student-portal/feedback/{feedback.id}/assign_representative/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['representative'], str(self.cr_representative.id))
        self.assertEqual(response.data['status'], 'UNDER_REVIEW')
    
    def test_representative_can_update_feedback_status(self):
        """Test that representatives can update feedback status"""
        # Create feedback and assign to representative
        feedback = StudentFeedback.objects.create(
            student=self.student2,
            representative=self.cr_representative,
            feedback_type='ACADEMIC',
            title='Test Feedback',
            description='Test description',
            priority='MEDIUM',
            status='UNDER_REVIEW'
        )
        
        # Login as representative
        self.client.force_authenticate(user=self.user1)
        
        # Update feedback status
        url = f'/api/student-portal/feedback/{feedback.id}/update_status/'
        data = {
            'status': 'RESOLVED',
            'resolution_notes': 'Issue has been resolved'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'RESOLVED')
        self.assertEqual(response.data['resolution_notes'], 'Issue has been resolved')
    
    def test_student_can_only_see_own_feedback(self):
        """Test that students can only see their own feedback"""
        # Create feedback for student2
        feedback = StudentFeedback.objects.create(
            student=self.student2,
            feedback_type='ACADEMIC',
            title='Test Feedback',
            description='Test description',
            priority='MEDIUM'
        )
        
        # Login as student1
        self.client.force_authenticate(user=self.user1)
        
        # Try to access feedback
        url = f'/api/student-portal/feedback/{feedback.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StudentPortalProfileTestCase(APITestCase):
    """Test cases for student profile management"""
    
    def setUp(self):
        # Create Student group
        self.student_group = Group.objects.create(name='Student')
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=timezone.now().date(),
            end_date=timezone.now().date().replace(year=timezone.now().year + 1),
            is_current=True,
            is_active=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            is_active=True
        )
        
        # Create academic program
        self.academic_program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH-CS',
            department=self.department,
            is_active=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.academic_program,
            academic_year=self.academic_year,
            semester='5',
            year_of_study='3',
            section='A',
            batch_name='CS-2024-3-A',
            batch_code='CS-2024-3-A',
            max_capacity=70,
            current_count=0,
            is_active=True
        )
        
        # Create test student
        self.student = Student.objects.create(
            roll_number='22CS001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            date_of_birth='2000-01-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        # Get the auto-created user
        self.user = self.student.user
    
    def test_student_can_view_profile(self):
        """Test that students can view their profile"""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/student-portal/profile/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['roll_number'], '22CS001')
        self.assertEqual(response.data['full_name'], 'John Doe')
        self.assertIn('academic_info', response.data)
        self.assertIn('contact_info', response.data)
    
    def test_student_can_update_profile(self):
        """Test that students can update their profile"""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/student-portal/profile/'
        data = {
            'student_mobile': '+919876543210',
            'address_line1': '123 Main Street',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'postal_code': '500001'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_mobile'], '+919876543210')
        self.assertEqual(response.data['contact_info']['address_line1'], '123 Main Street')
        self.assertEqual(response.data['contact_info']['city'], 'Hyderabad')
    
    def test_unauthorized_profile_access(self):
        """Test unauthorized access to profile"""
        url = '/api/student-portal/profile/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_update_validation(self):
        """Test profile update validation"""
        self.client.force_authenticate(user=self.user)
        
        url = '/api/student-portal/profile/'
        data = {
            'student_mobile': 'invalid_phone'  # Invalid phone number
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StudentPortalStatsTestCase(APITestCase):
    """Test cases for student portal statistics"""
    
    def setUp(self):
        # Create Student group
        self.student_group = Group.objects.create(name='Student')
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=timezone.now().date(),
            end_date=timezone.now().date().replace(year=timezone.now().year + 1),
            is_current=True,
            is_active=True
        )
        
        # Create department
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            is_active=True
        )
        
        # Create academic program
        self.academic_program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH-CS',
            department=self.department,
            is_active=True
        )
        
        # Create student batch
        self.student_batch = StudentBatch.objects.create(
            department=self.department,
            academic_program=self.academic_program,
            academic_year=self.academic_year,
            semester='5',
            year_of_study='3',
            section='A',
            batch_name='CS-2024-3-A',
            batch_code='CS-2024-3-A',
            max_capacity=70,
            current_count=2,
            is_active=True
        )
        
        # Create test students
        self.student1 = Student.objects.create(
            roll_number='22CS001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            date_of_birth='2000-01-15',
            gender='M',
            student_batch=self.student_batch
        )
        
        self.student2 = Student.objects.create(
            roll_number='22CS002',
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            date_of_birth='2000-02-15',
            gender='F',
            student_batch=self.student_batch
        )
        
        # Get the auto-created users
        self.user1 = self.student1.user
        self.user2 = self.student2.user
        
        # Create some feedback
        StudentFeedback.objects.create(
            student=self.student1,
            feedback_type='ACADEMIC',
            title='Test Feedback 1',
            description='Test description 1',
            priority='MEDIUM',
            status='SUBMITTED'
        )
        
        StudentFeedback.objects.create(
            student=self.student1,
            feedback_type='INFRASTRUCTURE',
            title='Test Feedback 2',
            description='Test description 2',
            priority='HIGH',
            status='RESOLVED'
        )
    
    def test_student_stats_access(self):
        """Test student statistics access"""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/student-portal/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('academic_stats', response.data)
        self.assertIn('feedback_stats', response.data)
        self.assertIn('representative_stats', response.data)
        self.assertIn('class_stats', response.data)
    
    def test_stats_data_accuracy(self):
        """Test that statistics data is accurate"""
        self.client.force_authenticate(user=self.user1)
        
        url = '/api/student-portal/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check academic stats
        academic_stats = response.data['academic_stats']
        self.assertEqual(academic_stats['current_semester'], '5')
        self.assertEqual(academic_stats['year_of_study'], '3')
        self.assertEqual(academic_stats['department'], 'Computer Science')
        
        # Check feedback stats
        feedback_stats = response.data['feedback_stats']
        self.assertEqual(feedback_stats['total_submitted'], 2)
        self.assertEqual(feedback_stats['by_status']['SUBMITTED'], 1)
        self.assertEqual(feedback_stats['by_status']['RESOLVED'], 1)
        
        # Check class stats
        class_stats = response.data['class_stats']
        self.assertEqual(class_stats['total_students'], 2)
        self.assertEqual(class_stats['male_students'], 1)
        self.assertEqual(class_stats['female_students'], 1)
