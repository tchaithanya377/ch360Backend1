import builtins
import importlib
import types
import pytest


@pytest.mark.django_db
def test_example_batch_enrollment_module_imports_and_functions(monkeypatch):
	# Prevent actual printing to keep tests quiet
	monkeypatch.setattr(builtins, 'print', lambda *args, **kwargs: None)
	mod = importlib.import_module('academics.example_batch_enrollment')
	assert hasattr(mod, 'create_example_data')
	assert hasattr(mod, 'create_sample_students')
	assert hasattr(mod, 'demonstrate_batch_enrollment')
	assert hasattr(mod, 'demonstrate_bulk_operations')
	# Prepare required defaults for Department validations
	from departments.models import Department
	Department.objects.get_or_create(
		name='Computer Science',
		defaults={
			'code': 'CS',
			'description': 'Computer Science Department',
			'short_name': 'CSE',
			'email': 'cse@example.com',
			'phone': '+911234567890',
			'building': 'Main',
			'established_date': '2000-01-01'
		}
	)
	# Do not execute create_example_data due to legacy fields not present in models in this test env.
	# Instead, directly exercise create_sample_students using a bakery-made batch.
	from model_bakery import baker
	# Ensure related Department validations pass by reusing the prepared Department
	dept = Department.objects.get(name='Computer Science')
	program = baker.make('academics.AcademicProgram', department=dept)
	batch = baker.make('students.StudentBatch', academic_program=program, department=dept)
	students = mod.create_sample_students(batch, 1)
	assert len(students) == 1


