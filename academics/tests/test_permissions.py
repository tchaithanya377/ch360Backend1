import pytest
from django.urls import reverse
from rest_framework.test import APIClient


def api(name):
    return reverse(f"academics:{name}")


@pytest.mark.django_db
def test_unauthenticated_access_is_blocked():
    client = APIClient()
    for name in [
        'course-list', 'course-section-list', 'syllabus-list', 'timetable-list',
        'enrollment-list', 'batch-enrollment-list', 'course-prerequisite-list', 'academic-calendar-list'
    ]:
        url = api(name)
        res = client.get(url)
        assert res.status_code == 401


@pytest.mark.django_db
def test_authenticated_access_allowed(django_user_model):
    client = APIClient()
    user = django_user_model.objects.create_user(username='a', email='a@example.com', password='p')
    client.force_authenticate(user=user)
    res = client.get(api('course-list'))
    assert res.status_code == 200


@pytest.mark.parametrize('role_setup', ['student', 'faculty', 'hod', 'admin'])
@pytest.mark.django_db
def test_role_based_access_smoke(role_setup, django_user_model):
    client = APIClient()
    is_staff = role_setup in ('hod', 'admin')
    is_superuser = role_setup == 'admin'
    user = django_user_model.objects.create_user(
        username=f'user-{role_setup}', email=f'{role_setup}@example.com', password='p', is_staff=is_staff, is_superuser=is_superuser
    )
    client.force_authenticate(user=user)
    # All roles should access list endpoints due to IsAuthenticated
    for name in [
        'course-list', 'course-section-list', 'syllabus-list', 'timetable-list',
        'enrollment-list', 'batch-enrollment-list', 'course-prerequisite-list', 'academic-calendar-list'
    ]:
        assert client.get(api(name)).status_code == 200


