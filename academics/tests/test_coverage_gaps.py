import types
import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_academic_program_model_save_sets_default_status(department):
	# status blank should default to ACTIVE in model.save
	ap = baker.prepare('academics.AcademicProgram', department=department, status='')
	ap.save()
	assert ap.status == 'ACTIVE'


@pytest.mark.django_db
def test_course_section_str_without_batch_shows_no_batch(faculty):
	course = baker.make('academics.Course')
	# Create section without student_batch to hit __str__ else branch
	section = baker.make('academics.CourseSection', course=course, student_batch=None, faculty=faculty)
	assert 'No Batch Assigned' in str(section)


@pytest.mark.django_db
def test_course_serializer_enrolled_students_count_exception(monkeypatch, department, faculty):
	from academics.models import CourseSection
	from academics.serializers import CourseSerializer
	course = baker.make('academics.Course', department=department)
	# Create one section and make its get_enrolled_students_count raise to trigger serializer except path
	section = baker.make(CourseSection, course=course, student_batch=None, faculty=faculty)
	orig = CourseSection.get_enrolled_students_count
	def boom(*args, **kwargs):
		raise Exception('boom')
	monkeypatch.setattr(CourseSection, 'get_enrolled_students_count', boom)
	try:
		data = CourseSerializer(course).data
		assert data.get('enrolled_students_count') == 0
	finally:
		monkeypatch.setattr(CourseSection, 'get_enrolled_students_count', orig)


@pytest.mark.django_db
def test_timetable_serializer_handles_missing_relations_and_duration_errors(faculty):
	from academics.models import Timetable, CourseSection, Course
	from academics.serializers import TimetableSerializer
	# Timetable with no course_section triggers None in get_course/get_faculty
	t = baker.make(Timetable, course_section=None)
	# Also make duration method raise to hit except branch
	orig = Timetable.get_duration_minutes
	def bad_duration(self):
		raise Exception('bad')
	try:
		Timetable.get_duration_minutes = bad_duration
		data = TimetableSerializer(t).data
		assert data.get('course') is None
		assert data.get('faculty') is None
		assert data.get('duration_minutes') is None
	finally:
		# Restore original to avoid side effects on other tests
		Timetable.get_duration_minutes = orig


@pytest.mark.django_db
def test_course_enrollment_serializer_handles_missing_nested():
	from academics.models import CourseEnrollment
	from academics.serializers import CourseEnrollmentSerializer
	# Prepare unsaved instance to avoid signals
	enrollment = baker.prepare(CourseEnrollment, course_section=None)
	ser = CourseEnrollmentSerializer()
	# Call helper getters directly to avoid date field serialization nuances
	assert ser.get_course(enrollment) is None
	assert ser.get_student_batch(enrollment) is None
	assert ser.get_section_number(enrollment) is None


@pytest.mark.django_db
def test_fixture_usage_program(program):
	# Ensure the 'program' fixture (conftest.py:13) is executed at least once
	assert program.code and program.department is not None


