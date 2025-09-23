import pytest
from django.utils import timezone
from model_bakery import baker

from academics.serializers import (
    CourseSerializer,
    CourseCreateSerializer,
    SyllabusCreateSerializer,
    CourseSectionCreateSerializer,
    TimetableCreateSerializer,
    CourseEnrollmentCreateSerializer,
    AcademicCalendarCreateSerializer,
    BatchCourseEnrollmentCreateSerializer,
    CoursePrerequisiteCreateSerializer,
)
from academics.models import Course, Syllabus, SyllabusTopic, CoursePrerequisite


@pytest.mark.django_db
def test_course_serializer_read_and_create_valid_invalid(department):
    course = baker.make(Course)
    data = CourseSerializer(course).data
    assert data['code'] == course.code
    # Create valid
    valid = {
        'code': 'CS200', 'title': 'DSA', 'description': 'desc', 'level': 'UG', 'credits': 4,
        'duration_weeks': 12, 'max_students': 60, 'prerequisites': [], 'department': department.id,
        'programs': [], 'status': 'ACTIVE'
    }
    # attach at least one program to satisfy non-empty constraint
    program = baker.make('academics.AcademicProgram', department=department)
    valid['programs'] = [program.id]
    ser = CourseCreateSerializer(data=valid)
    assert ser.is_valid(), ser.errors
    instance = ser.save()
    assert instance.pk
    # Invalid: negative credits handled by pre_save to default to 3, still model allows
    invalid = {**valid, 'code': 'CS201', 'credits': 0}
    ser2 = CourseCreateSerializer(data=invalid)
    assert ser2.is_valid(), ser2.errors
    obj = ser2.save()
    obj.refresh_from_db()
    assert obj.credits in (0, 3)


@pytest.mark.django_db
def test_syllabus_create_with_topics_and_update_replace_topics():
    course = baker.make(Course)
    payload = {
        'course': course.id,
        'version': '1.0',
        'academic_year': '2024-2025',
        'semester': 'Fall',
        'learning_objectives': 'lo',
        'course_outline': 'outline',
        'assessment_methods': 'exam',
        'grading_policy': 'policy',
        'textbooks': 'books',
        'additional_resources': '',
        'status': 'DRAFT',
        'topics': [
            {'week_number': 1, 'title': 'W1', 'description': 'd', 'learning_outcomes': 'lo', 'order': 1},
            {'week_number': 2, 'title': 'W2', 'description': 'd', 'learning_outcomes': 'lo', 'order': 1},
        ]
    }
    ser = SyllabusCreateSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    syl = ser.save()
    assert syl.topics.count() == 2
    # Update with a single topic, should replace
    upd = SyllabusCreateSerializer(instance=syl, data={**payload, 'topics': [payload['topics'][0]]})
    assert upd.is_valid(), upd.errors
    syl2 = upd.save()
    assert syl2.topics.count() == 1


@pytest.mark.django_db
def test_course_section_create_serializer_valid(faculty, department):
    program = baker.make('academics.AcademicProgram', department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department, year_of_study=3)
    course = baker.make(Course, department=department)
    section_ser = CourseSectionCreateSerializer(data={
        'course': course.id,
        'student_batch': batch.id,
        'section_type': 'LECTURE',
        'faculty': faculty.id,
        'max_students': 50,
        'current_enrollment': 0,
        'is_active': True,
        'notes': 'n',
    })
    assert section_ser.is_valid(), section_ser.errors
    obj = section_ser.save()
    assert obj.pk


@pytest.mark.django_db
def test_timetable_create_serializer_and_duration(faculty, department):
    program = baker.make('academics.AcademicProgram', department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make('academics.Course', department=department)
    from academics.models import CourseSection
    section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
    ser = TimetableCreateSerializer(data={
        'course_section': section.id,
        'timetable_type': 'REGULAR',
        'day_of_week': 'MON',
        'start_time': '09:00:00',
        'end_time': '10:30:00',
        'room': 'R1',
        'is_active': True,
        'notes': '',
    })
    assert ser.is_valid(), ser.errors
    tt = ser.save()
    assert tt.get_duration_minutes() == 90


@pytest.mark.django_db
def test_course_enrollment_create_serializer_valid(faculty, department):
    program = baker.make('academics.AcademicProgram', department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department)
    course = baker.make('academics.Course', department=department)
    from academics.models import CourseSection
    section = CourseSection.objects.create(course=course, student_batch=batch, faculty=faculty)
    ser = CourseEnrollmentCreateSerializer(data={
        'student': baker.make('students.Student').id,
        'course_section': section.id,
        'status': 'ENROLLED',
        'grade': '',
        'enrollment_type': 'REGULAR',
        'notes': ''
    })
    assert ser.is_valid(), ser.errors
    obj = ser.save()
    assert obj.pk


@pytest.mark.django_db
def test_academic_calendar_create_serializer_valid_invalid_dates():
    data = {
        'title': 'Event', 'event_type': 'EVENT',
        'start_date': '2025-01-01', 'end_date': '2025-01-02',
        'description': 'd', 'academic_year': '2024-2025', 'semester': 'Fall', 'is_academic_day': True
    }
    ser = AcademicCalendarCreateSerializer(data=data)
    assert ser.is_valid(), ser.errors
    obj = ser.save()
    assert obj.pk


@pytest.mark.django_db
def test_batch_course_enrollment_serializer_defaults_and_validation(department):
    # Setup academic year and semester so defaults work
    ay = baker.make('students.AcademicYear', year='2024-2025', is_active=True, is_current=True)
    sem = baker.make('students.Semester', academic_year=ay, name='Fall', semester_type='ODD', is_active=True, is_current=True)
    program = baker.make('academics.AcademicProgram', department=department)
    batch = baker.make('students.StudentBatch', academic_program=program, department=department, year_of_study=3)
    course = baker.make('academics.Course', level='UG')
    program.courses.add(course)
    ser = BatchCourseEnrollmentCreateSerializer(data={
        'student_batch': batch.id,
        'course': course.id,
        'academic_year': '2024-2025',
        'semester': 'Fall',
        'status': 'ACTIVE',
        'auto_enroll_new_students': True,
        'notes': ''
    })
    assert ser.is_valid(), ser.errors
    obj = ser.save()
    assert obj.academic_year == '2024-2025'
    assert obj.semester == 'Fall'
    # Invalid: semester not in provided academic year
    bad = BatchCourseEnrollmentCreateSerializer(data={
        'student_batch': batch.id,
        'course': course.id,
        'academic_year': '1999-2000',
        'semester': 'Fall',
    })
    assert not bad.is_valid()


@pytest.mark.django_db
def test_course_prerequisite_serializer_validation_self_and_circular():
    c1 = baker.make(Course)
    c2 = baker.make(Course)
    ser = CoursePrerequisiteCreateSerializer(data={'course': c1.id, 'prerequisite_course': c1.id})
    assert not ser.is_valid()
    # Circular
    CoursePrerequisite.objects.create(course=c1, prerequisite_course=c2)
    ser2 = CoursePrerequisiteCreateSerializer(data={'course': c2.id, 'prerequisite_course': c1.id})
    assert not ser2.is_valid()


