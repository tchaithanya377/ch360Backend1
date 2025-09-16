import uuid
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from students.models import Student, StudentBatch, AcademicYear
from departments.models import Department


User = get_user_model()


class AchievementsAPITest(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='tester', password='Passw0rd!')
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)

		# Minimal Department and AcademicYear to create a StudentBatch and Student
		self.department = Department.objects.create(
			name='Computer Science', short_name='CSE', code='CS', email='cse@example.com',
			phone='+911234567890', building='Main', established_date='2000-01-01',
			description='Dept', created_by=self.user
		)
		self.academic_year = AcademicYear.objects.create(year='2025-2026', start_date='2025-06-01', end_date='2026-05-31', is_current=True)
		self.batch = StudentBatch.objects.create(
			department=self.department,
			academic_program=None,
			academic_year=self.academic_year,
			semester='1', year_of_study='1', section='A',
			batch_name='CSE-2025-1-A', batch_code='CSE-2025-1-A', created_by=self.user
		)
		self.student = Student.objects.create(
			roll_number='CS250001', first_name='Ada', last_name='Lovelace', date_of_birth='2005-01-01', gender='F',
			student_batch=self.batch, status='ACTIVE', created_by=self.user
		)

	def test_create_and_list_achievement_for_student(self):
		url = '/api/v1/achievements/achievements/'
		payload = {
			'owner_type': 'students.student',
			'owner_id': str(self.student.id),
			'title': 'Hackathon Winner',
			'category': 'AWARD',
			'issuer_or_organizer': 'ACM',
			'achieved_on': '2025-08-10',
			'is_public': True
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

		list_res = self.client.get(url, {'owner_type': 'students.student'})
		self.assertEqual(list_res.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(len(list_res.data.get('results', list_res.data)), 1)

	def test_skill_unique_per_owner(self):
		url = '/api/v1/achievements/skills/'
		payload = {
			'owner_type': 'students.student',
			'owner_id': str(self.student.id),
			'name': 'Python',
			'proficiency': 80,
			'is_core': True
		}
		res1 = self.client.post(url, payload, format='json')
		self.assertEqual(res1.status_code, status.HTTP_201_CREATED, res1.data)
		res2 = self.client.post(url, payload, format='json')
		self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

	def test_publication_crud(self):
		url = '/api/v1/achievements/publications/'
		payload = {
			'owner_type': 'students.student',
			'owner_id': str(self.student.id),
			'title': 'On Analytical Engines',
			'authors': 'A. Lovelace',
			'year': 2025
		}
		create_res = self.client.post(url, payload, format='json')
		self.assertEqual(create_res.status_code, status.HTTP_201_CREATED, create_res.data)
		pub_id = create_res.data['id']

		# Retrieve and update
		detail = self.client.get(f'{url}{pub_id}/')
		self.assertEqual(detail.status_code, status.HTTP_200_OK)
		patch = self.client.patch(f'{url}{pub_id}/', {'year': 2026}, format='json')
		self.assertEqual(patch.status_code, status.HTTP_200_OK)

		# Delete
		delete_res = self.client.delete(f'{url}{pub_id}/')
		self.assertEqual(delete_res.status_code, status.HTTP_204_NO_CONTENT)

	def test_search_projects(self):
		url = '/api/v1/achievements/projects/'
		# create a project
		payload = {
			'owner_type': 'students.student',
			'owner_id': str(self.student.id),
			'title': 'CampusHub Resume Builder',
			'description': 'Build resume from achievements',
		}
		self.client.post(url, payload, format='json')
		# search
		res = self.client.get(url + '?search=Resume')
		self.assertEqual(res.status_code, status.HTTP_200_OK)
		self.assertTrue(len(res.data.get('results', res.data)) >= 1)

from django.test import TestCase

# Create your tests here.
