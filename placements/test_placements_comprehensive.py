"""
Comprehensive test suite for the enhanced placements module.
Tests all API endpoints, models, and functionality.
"""

import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal

from placements.models import (
    Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer,
    PlacementStatistics, CompanyFeedback, PlacementDocument, AlumniPlacement
)
from students.models import Student
from departments.models import Department
from academics.models import AcademicProgram

User = get_user_model()


class PlacementsTestCase(TestCase):
    """Base test case with common setup for all placement tests."""
    
    def setUp(self):
        """Set up test data for all tests."""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test department and program
        self.department = Department.objects.create(
            name='Computer Science',
            code='CS',
            description='Computer Science Department'
        )
        
        self.program = AcademicProgram.objects.create(
            name='B.Tech Computer Science',
            code='BTECH_CS',
            department=self.department,
            duration_years=4,
            level='UG'
        )
        
        # Create test student
        self.student = Student.objects.create(
            roll_number='CS2024001',
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='9876543210'
        )
        
        # Create test company
        self.company = Company.objects.create(
            name='Tech Corp',
            industry='Technology',
            company_size='LARGE',
            headquarters='Bangalore',
            contact_email='hr@techcorp.com',
            contact_phone='080-12345678'
        )
        
        # Create test job posting
        self.job_posting = JobPosting.objects.create(
            company=self.company,
            title='Software Engineer',
            description='Full-stack development role',
            location='Bangalore',
            work_mode='HYBRID',
            job_type='FULL_TIME',
            salary_min=Decimal('800000.00'),
            salary_max=Decimal('1200000.00'),
            currency='INR',
            skills=['Python', 'Django', 'React'],
            eligibility_criteria='B.Tech in CS/IT',
            openings=5,
            posted_by=self.user
        )
        
        # Create test placement drive
        self.placement_drive = PlacementDrive.objects.create(
            company=self.company,
            title='Tech Corp Campus Drive 2024',
            description='Campus recruitment drive',
            drive_type='CAMPUS',
            venue='Main Auditorium',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=8),
            min_cgpa=Decimal('7.00'),
            max_backlogs_allowed=2,
            batch_year='2024-2025',
            created_by=self.user
        )
        
        # Create test application
        self.application = Application.objects.create(
            student=self.student,
            job=self.job_posting,
            drive=self.placement_drive,
            cover_letter='I am interested in this position',
            status='APPLIED'
        )
        
        # Create test offer
        self.offer = Offer.objects.create(
            application=self.application,
            offered_role='Software Engineer',
            package_annual_ctc=Decimal('1000000.00'),
            joining_location='Bangalore',
            joining_date=date.today() + timedelta(days=30),
            status='PENDING'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)


class CompanyAPITest(PlacementsTestCase):
    """Test Company API endpoints."""
    
    def test_company_list(self):
        """Test GET /api/companies/ endpoint."""
        response = self.client.get('/api/v1/placements/api/companies/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Tech Corp')
    
    def test_company_create(self):
        """Test POST /api/companies/ endpoint."""
        company_data = {
            'name': 'New Tech Company',
            'industry': 'Software',
            'company_size': 'MEDIUM',
            'headquarters': 'Hyderabad',
            'contact_email': 'contact@newtech.com',
            'contact_phone': '040-98765432'
        }
        response = self.client.post('/api/v1/placements/api/companies/', 
                                  json.dumps(company_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Company.objects.filter(name='New Tech Company').exists())
    
    def test_company_detail(self):
        """Test GET /api/companies/{id}/ endpoint."""
        response = self.client.get(f'/api/v1/placements/api/companies/{self.company.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Tech Corp')
    
    def test_company_update(self):
        """Test PUT /api/companies/{id}/ endpoint."""
        update_data = {
            'name': 'Tech Corp Updated',
            'industry': 'Technology',
            'company_size': 'LARGE',
            'headquarters': 'Bangalore',
            'contact_email': 'hr@techcorp.com',
            'contact_phone': '080-12345678'
        }
        response = self.client.put(f'/api/v1/placements/api/companies/{self.company.id}/',
                                 json.dumps(update_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.company.refresh_from_db()
        self.assertEqual(self.company.name, 'Tech Corp Updated')
    
    def test_company_statistics(self):
        """Test GET /api/companies/{id}/statistics/ endpoint."""
        response = self.client.get(f'/api/v1/placements/api/companies/{self.company.id}/statistics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('statistics', data)
        self.assertIn('total_drives', data['statistics'])
        self.assertIn('total_applications', data['statistics'])
        self.assertIn('conversion_rate', data['statistics'])


class JobPostingAPITest(PlacementsTestCase):
    """Test Job Posting API endpoints."""
    
    def test_job_posting_list(self):
        """Test GET /api/jobs/ endpoint."""
        response = self.client.get('/api/v1/placements/api/jobs/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'Software Engineer')
    
    def test_job_posting_create(self):
        """Test POST /api/jobs/ endpoint."""
        job_data = {
            'company_id': self.company.id,
            'title': 'Data Scientist',
            'description': 'Machine learning and data analysis',
            'location': 'Mumbai',
            'work_mode': 'REMOTE',
            'job_type': 'FULL_TIME',
            'salary_min': '1000000.00',
            'salary_max': '1500000.00',
            'currency': 'INR',
            'skills': ['Python', 'Machine Learning', 'Statistics'],
            'eligibility_criteria': 'M.Tech in CS/Data Science',
            'openings': 3
        }
        response = self.client.post('/api/v1/placements/api/jobs/',
                                  json.dumps(job_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(JobPosting.objects.filter(title='Data Scientist').exists())
    
    def test_job_posting_applications(self):
        """Test GET /api/jobs/{id}/applications/ endpoint."""
        response = self.client.get(f'/api/v1/placements/api/jobs/{self.job_posting.id}/applications/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['student']['roll_number'], 'CS2024001')


class ApplicationAPITest(PlacementsTestCase):
    """Test Application API endpoints."""
    
    def test_application_list(self):
        """Test GET /api/applications/ endpoint."""
        response = self.client.get('/api/v1/placements/api/applications/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['status'], 'APPLIED')
    
    def test_application_create(self):
        """Test POST /api/applications/ endpoint."""
        # Create another job posting for testing
        job2 = JobPosting.objects.create(
            company=self.company,
            title='DevOps Engineer',
            description='DevOps and cloud infrastructure',
            location='Pune',
            work_mode='ONSITE',
            job_type='FULL_TIME',
            salary_min=Decimal('900000.00'),
            salary_max=Decimal('1300000.00'),
            currency='INR',
            skills=['AWS', 'Docker', 'Kubernetes'],
            eligibility_criteria='B.Tech in CS/IT',
            openings=2,
            posted_by=self.user
        )
        
        application_data = {
            'student_id': self.student.id,
            'job_id': job2.id,
            'drive_id': self.placement_drive.id,
            'cover_letter': 'I am interested in DevOps role',
            'status': 'APPLIED'
        }
        response = self.client.post('/api/v1/placements/api/applications/',
                                  json.dumps(application_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Application.objects.filter(job=job2).exists())
    
    def test_application_update_status(self):
        """Test updating application status."""
        update_data = {
            'student_id': self.student.id,
            'job_id': self.job_posting.id,
            'drive_id': self.placement_drive.id,
            'cover_letter': 'I am interested in this position',
            'status': 'INTERVIEW'
        }
        response = self.client.put(f'/api/v1/placements/api/applications/{self.application.id}/',
                                 json.dumps(update_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'INTERVIEW')


class PlacementDriveAPITest(PlacementsTestCase):
    """Test Placement Drive API endpoints."""
    
    def test_placement_drive_list(self):
        """Test GET /api/drives/ endpoint."""
        response = self.client.get('/api/v1/placements/api/drives/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'Tech Corp Campus Drive 2024')
    
    def test_placement_drive_create(self):
        """Test POST /api/drives/ endpoint."""
        drive_data = {
            'company_id': self.company.id,
            'title': 'New Campus Drive 2024',
            'description': 'Another campus recruitment drive',
            'drive_type': 'POOL',
            'venue': 'Conference Hall',
            'start_date': (date.today() + timedelta(days=14)).isoformat(),
            'end_date': (date.today() + timedelta(days=15)).isoformat(),
            'min_cgpa': '7.50',
            'max_backlogs_allowed': 1,
            'batch_year': '2024-2025'
        }
        response = self.client.post('/api/v1/placements/api/drives/',
                                  json.dumps(drive_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PlacementDrive.objects.filter(title='New Campus Drive 2024').exists())


class OfferAPITest(PlacementsTestCase):
    """Test Offer API endpoints."""
    
    def test_offer_list(self):
        """Test GET /api/offers/ endpoint."""
        response = self.client.get('/api/v1/placements/api/offers/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['offered_role'], 'Software Engineer')
    
    def test_offer_create(self):
        """Test POST /api/offers/ endpoint."""
        # Create another application for testing
        job2 = JobPosting.objects.create(
            company=self.company,
            title='Product Manager',
            description='Product management role',
            location='Delhi',
            work_mode='HYBRID',
            job_type='FULL_TIME',
            salary_min=Decimal('1200000.00'),
            salary_max=Decimal('1800000.00'),
            currency='INR',
            skills=['Product Management', 'Analytics', 'Leadership'],
            eligibility_criteria='MBA or B.Tech with experience',
            openings=1,
            posted_by=self.user
        )
        
        app2 = Application.objects.create(
            student=self.student,
            job=job2,
            drive=self.placement_drive,
            cover_letter='I am interested in product management',
            status='INTERVIEW'
        )
        
        offer_data = {
            'application': app2.id,
            'offered_role': 'Product Manager',
            'package_annual_ctc': '1500000.00',
            'joining_location': 'Delhi',
            'joining_date': (date.today() + timedelta(days=45)).isoformat(),
            'status': 'PENDING'
        }
        response = self.client.post('/api/v1/placements/api/offers/',
                                  json.dumps(offer_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Offer.objects.filter(offered_role='Product Manager').exists())
    
    def test_offer_accept(self):
        """Test accepting an offer."""
        update_data = {
            'application': self.application.id,
            'offered_role': 'Software Engineer',
            'package_annual_ctc': '1000000.00',
            'joining_location': 'Bangalore',
            'joining_date': (date.today() + timedelta(days=30)).isoformat(),
            'status': 'ACCEPTED'
        }
        response = self.client.put(f'/api/v1/placements/api/offers/{self.offer.id}/',
                                 json.dumps(update_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, 'ACCEPTED')


class PlacementStatisticsAPITest(PlacementsTestCase):
    """Test Placement Statistics API endpoints."""
    
    def setUp(self):
        super().setUp()
        # Create placement statistics
        self.placement_stats = PlacementStatistics.objects.create(
            academic_year='2024-2025',
            department=self.department,
            program=self.program,
            total_students=100,
            eligible_students=95,
            placed_students=80,
            placement_percentage=Decimal('84.21'),
            average_salary=Decimal('950000.00'),
            highest_salary=Decimal('1500000.00'),
            lowest_salary=Decimal('600000.00'),
            total_companies_visited=25,
            total_job_offers=120,
            students_higher_studies=10,
            students_entrepreneurship=5
        )
    
    def test_placement_statistics_list(self):
        """Test GET /api/statistics/ endpoint."""
        response = self.client.get('/api/v1/placements/api/statistics/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['academic_year'], '2024-2025')
    
    def test_placement_statistics_create(self):
        """Test POST /api/statistics/ endpoint."""
        stats_data = {
            'academic_year': '2023-2024',
            'department_id': self.department.id,
            'program_id': self.program.id,
            'total_students': 80,
            'eligible_students': 75,
            'placed_students': 65,
            'average_salary': '850000.00',
            'highest_salary': '1200000.00',
            'lowest_salary': '500000.00',
            'total_companies_visited': 20,
            'total_job_offers': 90,
            'students_higher_studies': 8,
            'students_entrepreneurship': 2
        }
        response = self.client.post('/api/v1/placements/api/statistics/',
                                  json.dumps(stats_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(PlacementStatistics.objects.filter(academic_year='2023-2024').exists())
    
    def test_placement_overview(self):
        """Test GET /api/statistics/overview/ endpoint."""
        response = self.client.get('/api/v1/placements/api/statistics/overview/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('academic_year', data)
        self.assertIn('overview', data)
        self.assertIn('department_wise', data)
        self.assertEqual(data['overview']['total_students'], 100)
        self.assertEqual(data['overview']['placed_students'], 80)


class CompanyFeedbackAPITest(PlacementsTestCase):
    """Test Company Feedback API endpoints."""
    
    def test_company_feedback_create(self):
        """Test POST /api/feedbacks/ endpoint."""
        feedback_data = {
            'company_id': self.company.id,
            'drive_id': self.placement_drive.id,
            'overall_rating': 4,
            'student_quality_rating': 5,
            'process_rating': 4,
            'infrastructure_rating': 3,
            'positive_feedback': 'Students were well prepared and knowledgeable',
            'areas_for_improvement': 'Could improve on communication skills',
            'suggestions': 'More industry exposure for students',
            'would_visit_again': True,
            'feedback_by': 'John Smith',
            'feedback_by_designation': 'HR Manager'
        }
        response = self.client.post('/api/v1/placements/api/feedbacks/',
                                  json.dumps(feedback_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(CompanyFeedback.objects.filter(company=self.company).exists())
    
    def test_company_feedback_list(self):
        """Test GET /api/feedbacks/ endpoint."""
        # Create a feedback first
        CompanyFeedback.objects.create(
            company=self.company,
            drive=self.placement_drive,
            overall_rating=4,
            student_quality_rating=5,
            process_rating=4,
            infrastructure_rating=3,
            positive_feedback='Great students',
            would_visit_again=True,
            feedback_by='HR Manager'
        )
        
        response = self.client.get('/api/v1/placements/api/feedbacks/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['overall_rating'], 4)


class AlumniPlacementAPITest(PlacementsTestCase):
    """Test Alumni Placement API endpoints."""
    
    def test_alumni_placement_create(self):
        """Test POST /api/alumni/ endpoint."""
        alumni_data = {
            'student_id': self.student.id,
            'current_company': 'Google',
            'current_designation': 'Senior Software Engineer',
            'current_salary': '2000000.00',
            'current_location': 'Mountain View',
            'total_experience_years': '3.5',
            'job_changes': 1,
            'pursuing_higher_studies': False,
            'is_entrepreneur': False,
            'linkedin_profile': 'https://linkedin.com/in/johndoe',
            'email': 'john.doe@google.com',
            'phone': '9876543210',
            'willing_to_mentor': True,
            'willing_to_recruit': True
        }
        response = self.client.post('/api/v1/placements/api/alumni/',
                                  json.dumps(alumni_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(AlumniPlacement.objects.filter(student=self.student).exists())
    
    def test_alumni_network(self):
        """Test GET /api/alumni/alumni-network/ endpoint."""
        # Create alumni data first
        AlumniPlacement.objects.create(
            student=self.student,
            current_company='Google',
            current_designation='Senior Software Engineer',
            current_salary=Decimal('2000000.00'),
            willing_to_mentor=True,
            willing_to_recruit=True
        )
        
        response = self.client.get('/api/v1/placements/api/alumni/alumni-network/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('statistics', data)
        self.assertIn('top_companies', data)
        self.assertIn('alumni_list', data)
        self.assertEqual(data['statistics']['total_alumni'], 1)
        self.assertEqual(data['statistics']['willing_mentors'], 1)


class AnalyticsAPITest(PlacementsTestCase):
    """Test Analytics API endpoints."""
    
    def setUp(self):
        super().setUp()
        # Create multiple years of statistics for trend testing
        for year in range(2020, 2025):
            PlacementStatistics.objects.create(
                academic_year=f'{year}-{year+1}',
                department=self.department,
                program=self.program,
                total_students=100 + (year - 2020) * 10,
                eligible_students=95 + (year - 2020) * 10,
                placed_students=80 + (year - 2020) * 15,
                placement_percentage=Decimal('80.00') + Decimal(str((year - 2020) * 2)),
                average_salary=Decimal('800000.00') + Decimal(str((year - 2020) * 50000)),
                highest_salary=Decimal('1200000.00') + Decimal(str((year - 2020) * 100000)),
                lowest_salary=Decimal('500000.00') + Decimal(str((year - 2020) * 25000)),
                total_companies_visited=20 + (year - 2020) * 2,
                total_job_offers=90 + (year - 2020) * 10,
                students_higher_studies=8 + (year - 2020),
                students_entrepreneurship=2 + (year - 2020)
            )
    
    def test_placement_trends(self):
        """Test GET /api/analytics/trends/ endpoint."""
        response = self.client.get('/api/v1/placements/api/analytics/trends/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('trends', data)
        self.assertEqual(len(data['trends']), 5)  # 5 years of data
        
        # Check trend data structure
        trend = data['trends'][0]
        self.assertIn('academic_year', trend)
        self.assertIn('total_students', trend)
        self.assertIn('placed_students', trend)
        self.assertIn('placement_percentage', trend)
        self.assertIn('average_salary', trend)
    
    def test_nirf_report(self):
        """Test GET /api/analytics/nirf-report/ endpoint."""
        response = self.client.get('/api/v1/placements/api/analytics/nirf-report/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('academic_year', data)
        self.assertIn('nirf_metrics', data)
        self.assertIn('department_wise_data', data)
        
        # Check NIRF metrics
        nirf_metrics = data['nirf_metrics']
        self.assertIn('total_students', nirf_metrics)
        self.assertIn('placed_students', nirf_metrics)
        self.assertIn('placement_percentage', nirf_metrics)
        self.assertIn('students_higher_studies', nirf_metrics)
        self.assertIn('entrepreneurs', nirf_metrics)


class EdgeCasesAndErrorHandlingTest(PlacementsTestCase):
    """Test edge cases and error handling."""
    
    def test_duplicate_application(self):
        """Test that duplicate applications are not allowed."""
        # Try to create another application for the same student and job
        application_data = {
            'student_id': self.student.id,
            'job_id': self.job_posting.id,
            'drive_id': self.placement_drive.id,
            'cover_letter': 'Another application',
            'status': 'APPLIED'
        }
        response = self.client.post('/api/v1/placements/api/applications/',
                                  json.dumps(application_data),
                                  content_type='application/json')
        # Should return 400 due to unique constraint
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_company_rating(self):
        """Test that company rating is within valid range."""
        company_data = {
            'name': 'Test Company',
            'industry': 'Technology',
            'rating': '6.00'  # Invalid rating > 5
        }
        response = self.client.post('/api/v1/placements/api/companies/',
                                  json.dumps(company_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
    
    def test_missing_required_fields(self):
        """Test that required fields are validated."""
        job_data = {
            'title': 'Test Job',
            # Missing required fields like company_id, description
        }
        response = self.client.post('/api/v1/placements/api/jobs/',
                                  json.dumps(job_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_date_format(self):
        """Test invalid date format handling."""
        drive_data = {
            'company_id': self.company.id,
            'title': 'Test Drive',
            'description': 'Test description',
            'drive_type': 'CAMPUS',
            'start_date': 'invalid-date',  # Invalid date format
            'min_cgpa': '7.00'
        }
        response = self.client.post('/api/v1/placements/api/drives/',
                                  json.dumps(drive_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access endpoints."""
        # Create a new client without authentication
        unauth_client = Client()
        response = unauth_client.get('/api/v1/placements/api/companies/')
        self.assertEqual(response.status_code, 401)  # Unauthorized
    
    def test_nonexistent_resource(self):
        """Test accessing non-existent resources."""
        response = self.client.get('/api/v1/placements/api/companies/99999/')
        self.assertEqual(response.status_code, 404)
    
    def test_large_data_handling(self):
        """Test handling of large data sets."""
        # Create multiple companies
        for i in range(50):
            Company.objects.create(
                name=f'Company {i}',
                industry='Technology',
                company_size='MEDIUM'
            )
        
        response = self.client.get('/api/v1/placements/api/companies/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should handle pagination properly
        self.assertIn('results', data)
        self.assertIn('count', data)


class ModelRelationshipsTest(PlacementsTestCase):
    """Test model relationships and constraints."""
    
    def test_company_job_relationship(self):
        """Test Company-JobPosting relationship."""
        self.assertEqual(self.job_posting.company, self.company)
        self.assertIn(self.job_posting, self.company.jobs.all())
    
    def test_job_application_relationship(self):
        """Test JobPosting-Application relationship."""
        self.assertEqual(self.application.job, self.job_posting)
        self.assertIn(self.application, self.job_posting.applications.all())
    
    def test_application_offer_relationship(self):
        """Test Application-Offer relationship."""
        self.assertEqual(self.offer.application, self.application)
        self.assertEqual(self.application.offer, self.offer)
    
    def test_placement_drive_relationships(self):
        """Test PlacementDrive relationships."""
        self.assertEqual(self.placement_drive.company, self.company)
        self.assertIn(self.application, self.placement_drive.applications.all())
    
    def test_cascade_deletions(self):
        """Test cascade deletion behavior."""
        # Delete company should cascade to jobs
        company_id = self.company.id
        self.company.delete()
        self.assertFalse(JobPosting.objects.filter(company_id=company_id).exists())
    
    def test_unique_constraints(self):
        """Test unique constraints."""
        # Test unique company name
        with self.assertRaises(Exception):
            Company.objects.create(
                name='Tech Corp',  # Same name as existing company
                industry='Technology'
            )
        
        # Test unique application (student + job)
        with self.assertRaises(Exception):
            Application.objects.create(
                student=self.student,
                job=self.job_posting,
                status='APPLIED'
            )


class PerformanceTest(PlacementsTestCase):
    """Test performance with large datasets."""
    
    def test_large_dataset_performance(self):
        """Test API performance with large datasets."""
        # Create large number of records
        companies = []
        for i in range(100):
            companies.append(Company(
                name=f'Company {i}',
                industry='Technology',
                company_size='MEDIUM'
            ))
        Company.objects.bulk_create(companies)
        
        # Test list endpoint performance
        import time
        start_time = time.time()
        response = self.client.get('/api/v1/placements/api/companies/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(end_time - start_time, 2.0)  # 2 seconds threshold
    
    def test_database_query_optimization(self):
        """Test that queries are optimized (no N+1 problems)."""
        # Create multiple related objects
        for i in range(10):
            job = JobPosting.objects.create(
                company=self.company,
                title=f'Job {i}',
                description=f'Description {i}',
                location='Bangalore',
                work_mode='ONSITE',
                job_type='FULL_TIME',
                posted_by=self.user
            )
            Application.objects.create(
                student=self.student,
                job=job,
                status='APPLIED'
            )
        
        # Test that list endpoint doesn't cause N+1 queries
        with self.assertNumQueries(3):  # Adjust based on actual query count
            response = self.client.get('/api/v1/placements/api/applications/')
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['placements.test_placements_comprehensive'])
