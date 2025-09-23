import pytest
from model_bakery import baker


@pytest.fixture
def department():
	# Ensure phone passes regex
	return baker.make('departments.Department', phone='+911234567890')


@pytest.fixture
def program(department):
	return baker.make('academics.AcademicProgram', department=department)


@pytest.fixture
def faculty_user(django_user_model):
	# Create a valid user with required email for faculty linkage
	return django_user_model.objects.create_user(
		email='faculty@example.com', password='pass', username='faculty_user'
	)


@pytest.fixture
def faculty(faculty_user):
	# Faculty model auto-creates user if not provided; pass the user explicitly to avoid creating without email
	return baker.make('faculty.Faculty', user=faculty_user)
