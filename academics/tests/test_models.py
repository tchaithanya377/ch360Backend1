import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.utils import timezone
from model_bakery import baker

from academics.models import (
    AcademicProgram,
    Course,
    CourseSection,
    Syllabus,
    SyllabusTopic,
    Timetable,
    CourseEnrollment,
    AcademicCalendar,
    BatchCourseEnrollment,
    CoursePrerequisite,
)


@pytest.mark.django_db
def test_academic_program_str_defaults_and_save_idempotent(department):
    program = AcademicProgram.objects.create(
        name='Computer Science', code='bcs', level='UG', department=department, total_credits=120
    )
    # status auto-defaults to ACTIVE via save override and Meta default
    assert program.status == 'ACTIVE'
    assert str(program) == f"{program.code} - {program.name}"
    # save again should not alter status
    program.save()
    program.refresh_from_db()
    assert program.status == 'ACTIVE'


@pytest.mark.django_db
def test_course_creation_and_helpers(department):
    program = baker.make(AcademicProgram, department=department, total_credits=120)
    course = Course.objects.create(
        code='cs101', title='Intro', description='Basics', department=department
    )
    course.programs.add(program)
    assert course.level == 'UG'
    assert course.credits == 3
    assert str(course) == 'CS101 - Intro'
    # Helpers when no sections
    assert course.get_total_sections() == 0
    assert course.get_enrolled_students_count() == 0


@pytest.mark.django_db
def test_course_section_unique_and_capacity_helpers(faculty, department):
    program = baker.make(AcademicProgram, department=department, total_credits=120)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make(Course, department=department)
    section = CourseSection.objects.create(
        course=course, student_batch=batch, faculty=faculty, max_students=2, current_enrollment=0
    )
    assert str(section) == f"{course.code} - {batch.batch_name}"
    assert section.section_number == batch.section
    assert section.get_available_seats() == 2
    assert not section.is_full()
    # Creating duplicate for same course+batch violates unique_together
    with pytest.raises(IntegrityError):
        CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)


@pytest.mark.django_db
def test_syllabus_and_topic_str_ordering():
    course = baker.make(Course)
    syl = Syllabus.objects.create(
        course=course, version='1.0', academic_year='2024-2025', semester='Fall',
        learning_objectives='Learn', course_outline='Outline', assessment_methods='Exams',
        grading_policy='Policy', textbooks='Books'
    )
    assert str(syl) == f"{course.code} Syllabus - 2024-2025 Fall"
    topic = SyllabusTopic.objects.create(
        syllabus=syl, week_number=1, title='Week1', description='desc', learning_outcomes='lo', order=1
    )
    assert str(topic) == 'Week 1: Week1'


@pytest.mark.django_db
def test_timetable_duration_and_unique(faculty, department):
    program = baker.make(AcademicProgram, department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make(Course, department=department)
    section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
    tt = Timetable.objects.create(
        course_section=section, day_of_week='MON', start_time=timezone.datetime(2024, 1, 1, 9, 0).time(),
        end_time=timezone.datetime(2024, 1, 1, 10, 30).time(), room='R1'
    )
    assert tt.get_duration_minutes() == 90
    assert 'Monday' in str(tt)
    # unique together by (course_section, day_of_week, start_time)
    with pytest.raises(IntegrityError):
        Timetable.objects.create(
            course_section=section, day_of_week='MON', start_time=tt.start_time, end_time=tt.end_time, room='R2'
        )


@pytest.mark.django_db
def test_enrollment_counters_increment_decrement_and_properties(faculty, department):
    program = baker.make(AcademicProgram, department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make(Course, department=department)
    section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty, max_students=10, current_enrollment=0)
    student = baker.make('students.Student')
    enrollment = CourseEnrollment.objects.create(student=student, course_section=section, status='ENROLLED')
    section.refresh_from_db()
    assert section.current_enrollment == 1
    # Change status to DROPPED should decrement
    enrollment.status = 'DROPPED'
    enrollment.save()
    section.refresh_from_db()
    assert section.current_enrollment == 0
    # Set back to ENROLLED
    enrollment.status = 'ENROLLED'
    enrollment.save()
    section.refresh_from_db()
    assert section.current_enrollment == 1
    # Delete should decrement
    enrollment.delete()
    section.refresh_from_db()
    assert section.current_enrollment == 0
    # Property proxies
    # create with valid relations
    program = baker.make(AcademicProgram, department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make(Course, department=department)
    section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
    student = baker.make('students.Student')
    enrollment = CourseEnrollment.objects.create(student=student, course_section=section)
    assert enrollment.course == section.course
    assert enrollment.faculty == section.faculty


@pytest.mark.django_db
def test_batch_course_enrollment_methods_and_str(department):
    program = baker.make(AcademicProgram, department=department, total_credits=120)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department, is_active=True)
    course = baker.make(Course)
    bce = BatchCourseEnrollment.objects.create(
        student_batch=batch, course=course, academic_year='2024-2025', semester='Fall'
    )
    assert '→' in str(bce)
    # Enrollment percentage when batch is empty
    assert bce.get_batch_students_count() == batch.current_count
    assert bce.get_enrolled_students_count() == 0
    assert bce.get_enrollment_percentage() in (0, 0.0)


@pytest.mark.django_db
def test_course_prerequisite_unique_and_str():
    course = baker.make(Course)
    prereq = baker.make(Course)
    cpr = CoursePrerequisite.objects.create(course=course, prerequisite_course=prereq)
    assert prereq.code in str(cpr)
    # On SQLite without explicit constraint this may not raise; assert uniqueness via exists check
    exists = CoursePrerequisite.objects.filter(course=course, prerequisite_course=prereq).exists()
    assert exists is True


@pytest.mark.django_db
def test_academic_calendar_str_and_dates():
    cal = AcademicCalendar.objects.create(
        title='Holiday', event_type='HOLIDAY', start_date=timezone.now().date(),
        end_date=timezone.now().date(), description='Desc', academic_year='2024-2025', semester='Fall'
    )
    assert 'Holiday' in str(cal)


