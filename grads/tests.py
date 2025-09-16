"""
Tests for the grads app API endpoints
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

from grads.models import GradeScale, MidTermGrade, SemesterGrade, SemesterGPA, CumulativeGPA
from students.models import Student, Semester
from academics.models import CourseSection, Course, AcademicYear

User = get_user_model()


class GradesAPITestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            is_staff=True
        )
        
        # Create academic year
        self.academic_year = AcademicYear.objects.create(
            year=2024,
            is_active=True
        )
        
        # Create semester
        self.semester = Semester.objects.create(
            name='Semester 1',
            academic_year=self.academic_year,
            is_active=True
        )
        
        # Create course
        self.course = Course.objects.create(
            code='CS101',
            title='Computer Science 101',
            credits=4
        )
        
        # Create course section
        self.course_section = CourseSection.objects.create(
            course=self.course,
            semester=self.semester,
            section_name='A',
            faculty=self.user
        )
        
        # Create student
        self.student = Student.objects.create(
            roll_number='CS2024001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com'
        )
        
        # Create grade scale
        self.grade_scale = GradeScale.objects.create(
            letter='A+',
            description='Excellent',
            min_score=80.00,
            max_score=89.00,
            grade_points=9.00,
            is_active=True
        )
        
        # Create midterm grade
        self.midterm_grade = MidTermGrade.objects.create(
            student=self.student,
            course_section=self.course_section,
            semester=self.semester,
            midterm_marks=28,
            total_marks=30
        )
        
        # Create semester grade
        self.semester_grade = SemesterGrade.objects.create(
            student=self.student,
            course_section=self.course_section,
            semester=self.semester,
            final_marks=85,
            total_marks=100
        )

    def test_health_endpoint(self):
        """Test health endpoint"""
        response = self.client.get('/api/v1/grads/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['app'], 'grads')
        print("✅ Health endpoint working")

    def test_grade_scales_api(self):
        """Test grade scales API"""
        # Login
        self.client.force_login(self.user)
        
        # Test GET all grade scales
        response = self.client.get('/api/v1/grads/grade-scales/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        print("✅ Grade Scales GET API working")
        
        # Test GET specific grade scale
        response = self.client.get(f'/api/v1/grads/grade-scales/{self.grade_scale.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['letter'], 'A+')
        self.assertEqual(data['description'], 'Excellent')
        print("✅ Grade Scale Detail API working")
        
        # Test POST new grade scale
        new_grade_data = {
            'letter': 'A',
            'description': 'Very Good',
            'min_score': 70.00,
            'max_score': 79.00,
            'grade_points': 8.00,
            'is_active': True
        }
        response = self.client.post('/api/v1/grads/grade-scales/', 
                                  data=json.dumps(new_grade_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        print("✅ Grade Scale POST API working")

    def test_midterm_grades_api(self):
        """Test midterm grades API"""
        # Login
        self.client.force_login(self.user)
        
        # Test GET all midterm grades
        response = self.client.get('/api/v1/grads/midterm-grades/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        print("✅ Midterm Grades GET API working")
        
        # Test GET specific midterm grade
        response = self.client.get(f'/api/v1/grads/midterm-grades/{self.midterm_grade.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['midterm_marks'], 28)
        self.assertEqual(data['total_marks'], 30)
        print("✅ Midterm Grade Detail API working")

    def test_semester_grades_api(self):
        """Test semester grades API"""
        # Login
        self.client.force_login(self.user)
        
        # Test GET all semester grades
        response = self.client.get('/api/v1/grads/semester-grades/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        print("✅ Semester Grades GET API working")
        
        # Test GET specific semester grade
        response = self.client.get(f'/api/v1/grads/semester-grades/{self.semester_grade.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['final_marks'], 85)
        self.assertEqual(data['total_marks'], 100)
        print("✅ Semester Grade Detail API working")

    def test_sgpa_api(self):
        """Test SGPA API"""
        # Login
        self.client.force_login(self.user)
        
        # Test GET all SGPA records
        response = self.client.get('/api/v1/grads/semester-gpas/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        print("✅ SGPA GET API working")
        
        # Test student filter
        response = self.client.get(f'/api/v1/grads/semester-gpas/?student={self.student.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        print("✅ SGPA Student Filter API working")

    def test_cgpa_api(self):
        """Test CGPA API"""
        # Login
        self.client.force_login(self.user)
        
        # Test GET all CGPA records
        response = self.client.get('/api/v1/grads/cumulative-gpas/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        print("✅ CGPA GET API working")
        
        # Test student filter
        response = self.client.get(f'/api/v1/grads/cumulative-gpas/?student={self.student.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        print("✅ CGPA Student Filter API working")

    def test_academic_transcript_api(self):
        """Test academic transcript API"""
        # Login
        self.client.force_login(self.user)
        
        # Create a CGPA record
        cgpa = CumulativeGPA.objects.create(student=self.student)
        cgpa.recalculate()
        
        # Test academic transcript
        response = self.client.get(f'/api/v1/grads/cumulative-gpas/{cgpa.id}/academic_transcript/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('student', data)
        self.assertIn('cgpa', data)
        self.assertIn('semesters', data)
        print("✅ Academic Transcript API working")

    def test_bulk_operations(self):
        """Test bulk operations"""
        # Login
        self.client.force_login(self.user)
        
        # Test bulk upsert midterm grades
        bulk_data = {
            'grades': [
                {
                    'student': self.student.id,
                    'course_section': self.course_section.id,
                    'semester': self.semester.id,
                    'midterm_marks': 25,
                    'total_marks': 30
                }
            ]
        }
        response = self.client.post('/api/v1/grads/midterm-grades/bulk_upsert/',
                                  data=json.dumps(bulk_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('created', data)
        self.assertIn('updated', data)
        print("✅ Bulk Upsert Midterm Grades API working")
        
        # Test bulk upsert semester grades
        bulk_data = {
            'grades': [
                {
                    'student': self.student.id,
                    'course_section': self.course_section.id,
                    'semester': self.semester.id,
                    'final_marks': 90,
                    'total_marks': 100
                }
            ]
        }
        response = self.client.post('/api/v1/grads/semester-grades/bulk_upsert/',
                                  data=json.dumps(bulk_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('created', data)
        self.assertIn('updated', data)
        print("✅ Bulk Upsert Semester Grades API working")

    def test_error_handling(self):
        """Test error handling"""
        # Login
        self.client.force_login(self.user)
        
        # Test 404 for non-existent grade scale
        response = self.client.get('/api/v1/grads/grade-scales/99999/')
        self.assertEqual(response.status_code, 404)
        print("✅ 404 Error Handling working")
        
        # Test 404 for non-existent midterm grade
        response = self.client.get('/api/v1/grads/midterm-grades/99999/')
        self.assertEqual(response.status_code, 404)
        print("✅ 404 Error Handling for Midterm Grades working")

    def test_authentication_required(self):
        """Test that authentication is required"""
        # Test without authentication
        response = self.client.get('/api/v1/grads/grade-scales/')
        self.assertEqual(response.status_code, 401)
        print("✅ Authentication required for Grade Scales")
        
        response = self.client.get('/api/v1/grads/midterm-grades/')
        self.assertEqual(response.status_code, 401)
        print("✅ Authentication required for Midterm Grades")

    def test_grade_calculation(self):
        """Test automatic grade calculation"""
        # Login
        self.client.force_login(self.user)
        
        # Create a new semester grade with marks that should calculate to A+
        new_grade = SemesterGrade.objects.create(
            student=self.student,
            course_section=self.course_section,
            semester=self.semester,
            final_marks=85,  # 85% should be A+ based on our grade scale
            total_marks=100
        )
        
        # Check if grade was calculated correctly
        self.assertEqual(new_grade.percentage, 85.00)
        self.assertEqual(new_grade.final_grade, 'A+')
        self.assertEqual(new_grade.final_grade_points, 9.00)
        self.assertTrue(new_grade.passed)
        print("✅ Grade calculation working correctly")

    def test_sgpa_calculation(self):
        """Test SGPA calculation"""
        # Create semester GPA record
        sgpa = SemesterGPA.objects.create(
            student=self.student,
            semester=self.semester
        )
        sgpa.recalculate()
        
        # Check if SGPA was calculated
        self.assertIsNotNone(sgpa.sgpa)
        self.assertGreater(sgpa.sgpa, 0)
        self.assertIsNotNone(sgpa.academic_standing)
        print("✅ SGPA calculation working correctly")

    def test_cgpa_calculation(self):
        """Test CGPA calculation"""
        # Create CGPA record
        cgpa = CumulativeGPA.objects.create(student=self.student)
        cgpa.recalculate()
        
        # Check if CGPA was calculated
        self.assertIsNotNone(cgpa.cgpa)
        self.assertGreater(cgpa.cgpa, 0)
        self.assertIsNotNone(cgpa.classification)
        print("✅ CGPA calculation working correctly")
