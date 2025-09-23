import types
import pytest
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from academics import admin as academics_admin


class DummyRequest:
	def __init__(self, user):
		self.user = user


@pytest.mark.django_db
def test_academic_program_admin_defaults_and_save(department, django_user_model):
	user = django_user_model.objects.create_user(username='admin', email='a@example.com', password='x', is_staff=True)
	request = DummyRequest(user)
	apa = academics_admin.AcademicProgramAdmin(academics_admin.AcademicProgram, AdminSite())
	form = apa.get_form(request)
	assert form.base_fields['status'].initial == 'ACTIVE'
	obj = baker.prepare('academics.AcademicProgram', department=department, status='')
	apa.save_model(request, obj, form, change=False)
	assert obj.status == 'ACTIVE'


@pytest.mark.django_db
def test_course_admin_get_total_sections_uses_model_method(faculty, department):
	course = baker.make('academics.Course', department=department)
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	from academics.models import CourseSection
	CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
	CourseSection.objects.create(course=course, student_batch=baker.make('students.StudentBatch', academic_program=program, department=department), faculty=faculty)
	ca = academics_admin.CourseAdmin(academics_admin.Course, AdminSite())
	assert ca.get_total_sections(course) == course.get_total_sections()


@pytest.mark.django_db
def test_course_section_admin_available_seats_display_cases(faculty, department):
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	section_admin = academics_admin.CourseSectionAdmin(academics_admin.CourseSection, AdminSite())
	from academics.models import CourseSection
	# unlimited
	s1 = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty, max_students=None, current_enrollment=10)
	html1 = section_admin.available_seats_display(s1)
	assert 'Unlimited' in str(html1)
	# green
	s2 = CourseSection.objects.create(course=course, student_batch=baker.make('students.StudentBatch', academic_program=program, department=department), faculty=faculty, max_students=30, current_enrollment=10)
	html2 = section_admin.available_seats_display(s2)
	assert 'green' in str(html2)
	# red
	s3 = CourseSection.objects.create(course=course, student_batch=baker.make('students.StudentBatch', academic_program=program, department=department), faculty=faculty, max_students=0, current_enrollment=0)
	html3 = section_admin.available_seats_display(s3)
	assert 'Full' in str(html3)


@pytest.mark.django_db
def test_course_section_admin_save_model_sets_default_current_enrollment(faculty, department):
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	obj = baker.prepare('academics.CourseSection', course=course, student_batch=batch, faculty=faculty, current_enrollment=None)
	admin_obj = academics_admin.CourseSectionAdmin(academics_admin.CourseSection, AdminSite())
	admin_obj.save_model(DummyRequest(baker.make('accounts.User', email='x@example.com')), obj, form=None, change=False)
	assert obj.current_enrollment == 0


@pytest.mark.django_db
def test_syllabus_admin_save_sets_approved_by_when_missing(department, django_user_model):
	user = django_user_model.objects.create_user(username='u', email='u@example.com', password='x')
	sadmin = academics_admin.SyllabusAdmin(academics_admin.Syllabus, AdminSite())
	course = baker.make('academics.Course', department=department)
	syllabus = baker.prepare('academics.Syllabus', course=course, status='APPROVED', approved_by=None)
	sadmin.save_model(DummyRequest(user), syllabus, form=None, change=False)
	assert syllabus.approved_by == user


@pytest.mark.django_db
def test_timetable_admin_queryset_uses_select_related(faculty, department):
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	from academics.models import CourseSection, Timetable
	section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
	baker.make(Timetable, course_section=section)
	qs = academics_admin.TimetableAdmin(academics_admin.Timetable, AdminSite()).get_queryset(DummyRequest(baker.make('accounts.User', email='a@b.com')))
	# ensure no errors and queryset is evaluable
	assert qs.count() >= 1


@pytest.mark.django_db
def test_course_enrollment_admin_displays_and_queryset(faculty, department):
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	from academics.models import CourseSection, CourseEnrollment
	section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
	student = baker.make('students.Student', student_batch=batch)
	enr = baker.make(CourseEnrollment, student=student, course_section=section)
	admin_cls = academics_admin.CourseEnrollmentAdmin(academics_admin.CourseEnrollment, AdminSite())
	assert batch.batch_name in str(admin_cls.student_batch_display(enr))
	assert 'Section' in str(admin_cls.section_batch_display(enr))
	assert 'Year of Study' in str(admin_cls.student_batch_info(enr))
	assert 'Section Batch' in str(admin_cls.section_batch_info(enr))
	qs = admin_cls.get_queryset(DummyRequest(baker.make('accounts.User', email='q@w.e')))
	assert qs.filter(id=enr.id).exists()


@pytest.mark.django_db
def test_batch_course_enrollment_admin_form_choices_and_clean_save(department, django_user_model):
	# Setup AY/Sem for choices
	ay = baker.make('students.AcademicYear', year='2024-2025', is_active=True, is_current=True)
	baker.make('students.Semester', academic_year=ay, name='Fall', is_active=True, is_current=True, semester_type='ODD')
	user = django_user_model.objects.create_user(username='staff', email='s@example.com', password='x', is_staff=True)
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	form = academics_admin.BatchCourseEnrollmentForm(data={
		'student_batch': batch.id,
		'course': course.id,
		'academic_year': '2024-2025',
		'semester': 'Fall',
		'status': 'ACTIVE',
		'auto_enroll_new_students': True,
	})
	assert form.is_valid(), form.errors
	obj = form.save(commit=False)
	assert obj.academic_year == '2024-2025'
	assert obj.semester == 'Fall'
	admin_obj = academics_admin.BatchCourseEnrollmentAdmin(academics_admin.BatchCourseEnrollment, AdminSite())
	admin_obj.save_model(DummyRequest(user), obj, form=form, change=False)
	assert obj.created_by == user


@pytest.mark.django_db
def test_batch_course_enrollment_admin_actions_messages(django_user_model, department, monkeypatch):
	user = django_user_model.objects.create_superuser(username='su', email='su@example.com', password='x')
	request = DummyRequest(user)
	program = baker.make('academics.AcademicProgram', department=department)
	batch = baker.make('students.StudentBatch', academic_program=program, department=department)
	course = baker.make('academics.Course', department=department)
	obj = baker.make('academics.BatchCourseEnrollment', student_batch=batch, course=course, status='INACTIVE')
	admin_cls = academics_admin.BatchCourseEnrollmentAdmin(academics_admin.BatchCourseEnrollment, AdminSite())
	# Monkeypatch message_user to capture output
	messages = []
	admin_cls.message_user = lambda req, msg: messages.append(msg)
	# Activate
	admin_cls.activate_enrollments(request, academics_admin.BatchCourseEnrollment.objects.filter(id=obj.id))
	assert 'activated' in messages[-1]
	# Deactivate
	admin_cls.deactivate_enrollments(request, academics_admin.BatchCourseEnrollment.objects.filter(id=obj.id))
	assert 'deactivated' in messages[-1]
	# Enroll students (simulate success)
	def fake_enroll(self):
		return {'success': True, 'enrolled_count': 0, 'total_students': 0, 'errors': [], 'message': ''}
	monkeypatch.setattr(obj.__class__, 'enroll_batch_students', lambda self=obj: fake_enroll(obj))
	# Ensure object is ACTIVE so the queryset within action executes the enroll path
	academics_admin.BatchCourseEnrollment.objects.filter(id=obj.id).update(status='ACTIVE')
	admin_cls.enroll_students(request, academics_admin.BatchCourseEnrollment.objects.filter(id=obj.id))
	assert 'Successfully enrolled' in messages[-1]


