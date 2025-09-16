from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from accounts.models import User
from departments.models import Department
from faculty.models import Faculty
from students.models import Student
from mentoring.models import Mentorship, ActionItem


class MentoringApiTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create admin user and authenticate
        self.admin = User.objects.create_user(email='admin+mentoring@example.com', password='AdminPass123!', username='admin_mentoring', is_staff=True, is_superuser=True)
        self.client.force_authenticate(user=self.admin)

        # Department
        self.department = Department.objects.create(name='Computer Science', code='CSE')

        # Faculty mentor
        self.mentor = Faculty.objects.create(
            name='Dr. Mentor One',
            apaar_faculty_id='APAAR-M-0001',
            email='mentor1@example.com',
            department_ref=self.department,
            is_mentor=True,
            currently_associated=True,
            status='ACTIVE',
        )

        # Student
        self.student = Student.objects.create(
            roll_number='21CSE001',
            first_name='Student',
            last_name='One',
            date_of_birth=timezone.now().date(),
            gender='M',
            email='student1@example.com',
        )

    def test_create_list_mentorship(self):
        url = reverse('mentoring:mentorship-list')
        payload = {
            'mentor': str(self.mentor.id),
            'student': str(self.student.id),
            'start_date': str(timezone.now().date()),
            'is_active': True,
            'objective': 'Test mentorship',
            'department_ref': str(self.department.id),
            'academic_year': '2024-2025',
            'grade_level': '1',
            'section': 'A',
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        list_resp = self.client.get(url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_resp.data), 1)

    def test_action_item_crud(self):
        # Create mentorship
        m = Mentorship.objects.create(
            mentor=self.mentor,
            student=self.student,
            start_date=timezone.now().date(),
            is_active=True,
            department_ref=self.department,
            academic_year='2024-2025',
            grade_level='1',
            section='A',
        )
        url = reverse('mentoring:actionitem-list')
        payload = {
            'mentorship': str(m.id),
            'title': 'Prepare PPT',
            'priority': 'HIGH',
            'status': 'OPEN',
        }
        create_resp = self.client.post(url, payload, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED, create_resp.data)
        action_id = create_resp.data['id']

        detail_url = reverse('mentoring:actionitem-detail', args=[action_id])
        patch_resp = self.client.patch(detail_url, {'status': 'DONE'}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_resp.data['status'], 'DONE')

        list_resp = self.client.get(url)
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(any(ai['id'] == action_id for ai in list_resp.data))

    def test_compute_risk_and_analytics(self):
        # Create mentorship
        m = Mentorship.objects.create(
            mentor=self.mentor,
            student=self.student,
            start_date=timezone.now().date(),
            is_active=True,
            department_ref=self.department,
            academic_year='2024-2025',
            grade_level='1',
            section='A',
        )
        compute_url = reverse('mentoring:mentorship-compute-risk', args=[m.id])
        resp = self.client.post(compute_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertIn('risk_score', resp.data)

        analytics_url = reverse('mentoring:mentorship-analytics-summary')
        aresp = self.client.get(analytics_url, {'department': str(self.department.id), 'academic_year': '2024-2025'})
        self.assertEqual(aresp.status_code, status.HTTP_200_OK)
        self.assertIn('total', aresp.data)


