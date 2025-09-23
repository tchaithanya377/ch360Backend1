import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_course_signals_toggle_status_updates_timetable(department):
	course = baker.make('academics.Course', department=department, status='ACTIVE')
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	from academics.models import CourseSection, Timetable
	section = CourseSection.objects.create(course=course, student_batch=batch, faculty=baker.make('faculty.Faculty', user=baker.make('accounts.User', email='f@example.com')))
	tt = baker.make(Timetable, course_section=section, is_active=True)
	# Flip course to INACTIVE triggers timetable update to inactive via post_save
	course.status = 'INACTIVE'
	course.save()
	tt.refresh_from_db()
	assert tt.is_active is False


@pytest.mark.django_db
def test_timetable_post_save_conflict_path(department):
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	from academics.models import CourseSection, Timetable
	section = CourseSection.objects.create(course=course, student_batch=batch, faculty=baker.make('faculty.Faculty', user=baker.make('accounts.User', email='f2@example.com')))
	# Create two active timetables same room/time/day to exercise conflict loop
	baker.make(Timetable, course_section=section, day_of_week='MON', start_time='09:00', end_time='10:00', room='R1', is_active=True)
	baker.make(Timetable, course_section=section, day_of_week='MON', start_time='09:30', end_time='10:30', room='R1', is_active=True)
	# Saving one again triggers signal; ensure no exceptions and conflicts code path executes
	obj = Timetable.objects.filter(course_section=section).first()
	obj.save()
	assert Timetable.objects.filter(course_section=section).count() == 2


@pytest.mark.django_db
def test_batch_enrollment_post_save_auto_enroll_and_history_paths(monkeypatch, department):
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department, is_active=True)
	course = baker.make('academics.Course', department=department)
	obj = baker.make('academics.BatchCourseEnrollment', student_batch=batch, course=course, status='ACTIVE', auto_enroll_new_students=True)
	# Monkeypatch enroll to return success to traverse success branch
	monkeypatch.setattr(obj.__class__, 'enroll_batch_students', lambda self=obj: {'success': True, 'enrolled_count': 0, 'total_students': 0, 'errors': [], 'message': ''})
	# Trigger post_save by saving
	obj.save()
	assert obj.status == 'ACTIVE'


