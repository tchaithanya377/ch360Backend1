import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_course_section_capacity_edge_cases(faculty, department):
    # max_students None means unlimited
    program = baker.make('academics.AcademicProgram', department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make('academics.Course', department=department)
    from academics.models import CourseSection
    section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty, max_students=None, current_enrollment=999)
    assert section.get_available_seats() is None
    assert not section.is_full()
    # Zero capacity
    # Create a separate section with distinct batch to avoid unique constraint
    other_batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    from academics.models import CourseSection
    section2 = CourseSection.objects.create(course=course, student_batch=other_batch, faculty=faculty, max_students=0, current_enrollment=0)
    assert section2.get_available_seats() == 0
    assert section2.is_full()


@pytest.mark.django_db
def test_batch_enrollment_get_or_create_section_returns_none_when_not_assignable(department):
    program = baker.make('academics.AcademicProgram', department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make('academics.Course', department=department)
    bce = baker.make('academics.BatchCourseEnrollment', student_batch=batch, course=course, course_section=None)
    assert bce._get_or_create_course_section() is None


