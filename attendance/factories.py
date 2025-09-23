import factory
from django.utils import timezone
from faker import Faker
from datetime import date

from attendance.models import (
    AcademicCalendarHoliday, TimetableSlot, AttendanceSession, AttendanceRecord,
    AttendanceCorrectionRequest, LeaveApplication, StudentSnapshot, AttendanceConfiguration,
    AttendanceAuditLog
)
from academics.models import CourseSection, Course
from students.models import Student, StudentBatch, AcademicYear
from faculty.models import Faculty
from departments.models import Department
from django.contrib.auth import get_user_model

fake = Faker("en_IN")
User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    is_active = True


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department
    
    name = factory.Faker('company')
    short_name = factory.Sequence(lambda n: f"DEP{n:02d}")
    code = factory.Sequence(lambda n: f"DEP{n:03d}")
    department_type = 'ACADEMIC'
    status = 'ACTIVE'
    is_active = True
    email = factory.Faker('email')
    phone = factory.Faker('numerify', text='+91##########')
    building = factory.Faker('building_number')
    established_date = factory.Faker('date_between', start_date='-50y', end_date='-1y')
    description = factory.Faker('text', max_nb_chars=200)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle unique constraint violations"""
        import uuid
        unique_suffix = uuid.uuid4().hex[:6].upper()
        
        # Ensure all unique fields are unique from the start
        kwargs['name'] = f"Department {unique_suffix}"
        kwargs['code'] = f"DEP{unique_suffix}"
        kwargs['short_name'] = f"DEP{unique_suffix[:3]}"
        
        try:
            return super()._create(model_class, *args, **kwargs)
        except Exception as e:
            if 'already exists' in str(e):
                # If any unique field already exists, generate new ones
                unique_suffix = uuid.uuid4().hex[:6].upper()
                kwargs['name'] = f"Department {unique_suffix}"
                kwargs['code'] = f"DEP{unique_suffix}"
                kwargs['short_name'] = f"DEP{unique_suffix[:3]}"
                return super()._create(model_class, *args, **kwargs)
            raise


class FacultyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Faculty
    
    user = factory.SubFactory(UserFactory)
    employee_id = factory.Sequence(lambda n: f"FAC{n:04d}")
    apaar_faculty_id = factory.Sequence(lambda n: f"APAAR{n:06d}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: f"faculty{n}@example.com")
    department = factory.SubFactory(DepartmentFactory)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle unique constraint violations"""
        import uuid
        unique_suffix = uuid.uuid4().hex[:6].upper()
        
        # Ensure unique values from the start
        kwargs['apaar_faculty_id'] = f"APAAR{unique_suffix}"
        kwargs['employee_id'] = f"FAC{unique_suffix}"
        
        try:
            return super()._create(model_class, *args, **kwargs)
        except Exception as e:
            if 'apaar_faculty_id' in str(e) or 'employee_id' in str(e) or 'username' in str(e):
                # If any unique field already exists, generate new ones
                unique_suffix = uuid.uuid4().hex[:6].upper()
                kwargs['apaar_faculty_id'] = f"APAAR{unique_suffix}"
                kwargs['employee_id'] = f"FAC{unique_suffix}"
                return super()._create(model_class, *args, **kwargs)
            raise


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course
    
    code = factory.Sequence(lambda n: f"CS{n:03d}")
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=200)
    level = 'UG'
    credits = factory.Faker('random_int', min=1, max=6)
    duration_weeks = 16
    max_students = 50
    status = 'ACTIVE'
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle unique constraint violations"""
        import uuid
        unique_suffix = uuid.uuid4().hex[:6].upper()
        
        # Ensure unique code from the start
        kwargs['code'] = f"CS{unique_suffix}"
        
        try:
            return super()._create(model_class, *args, **kwargs)
        except Exception as e:
            if 'code' in str(e) and 'already exists' in str(e):
                # If code already exists, generate a new one
                unique_suffix = uuid.uuid4().hex[:6].upper()
                kwargs['code'] = f"CS{unique_suffix}"
                return super()._create(model_class, *args, **kwargs)
            raise


class AcademicYearFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AcademicYear
    
    year = factory.Sequence(lambda n: f"202{n % 10}-{202 + (n % 10) + 1}")
    start_date = factory.Faker('date_between', start_date='-1y', end_date='+1y')
    end_date = factory.LazyAttribute(lambda o: o.start_date + timezone.timedelta(days=365))
    is_current = False
    is_active = True


class StudentBatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentBatch
    
    department = factory.SubFactory(DepartmentFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    semester = '1'
    year_of_study = '1'
    section = 'A'
    batch_name = factory.LazyAttribute(lambda o: f"{o.department.name}-{o.academic_year.year}-{o.year_of_study}-{o.section}")
    batch_code = factory.LazyAttribute(lambda o: f"{o.department.name}-{o.academic_year.year}-{o.year_of_study}-{o.section}")
    max_capacity = 70
    current_count = 0
    is_active = True


class CourseSectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CourseSection
    
    course = factory.SubFactory(CourseFactory)
    student_batch = factory.SubFactory(StudentBatchFactory)
    faculty = factory.SubFactory(FacultyFactory)
    section_type = 'LECTURE'
    is_active = True


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student
    
    user = factory.SubFactory(UserFactory)
    roll_number = factory.Sequence(lambda n: f"21BQ1A05{n:02d}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=25)
    gender = factory.Faker('random_element', elements=['M', 'F'])
    student_batch = factory.SubFactory(StudentBatchFactory)
    status = 'ACTIVE'
    email = factory.Faker('email')
    student_mobile = factory.Faker('numerify', text='+91##########')


class AcademicCalendarHolidayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AcademicCalendarHoliday
    
    name = factory.Faker('sentence', nb_words=3)
    date = factory.Faker('date_between', start_date='-1y', end_date='+1y')
    is_full_day = True
    academic_year = factory.Faker('random_element', elements=['2023-2024', '2024-2025', '2025-2026'])
    description = factory.Faker('text', max_nb_chars=200)


class TimetableSlotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimetableSlot
    
    course_section = factory.SubFactory(CourseSectionFactory)
    faculty = factory.SubFactory(FacultyFactory)
    day_of_week = factory.Faker('random_int', min=0, max=6)  # 0=Monday, 6=Sunday
    start_time = factory.Faker('time_object')
    end_time = factory.Faker('time_object')
    room = factory.Faker('random_element', elements=['A-101', 'B-202', 'C-303', 'D-404'])
    is_active = True
    academic_year = factory.Faker('random_element', elements=['2023-2024', '2024-2025'])
    semester = factory.Faker('random_element', elements=['Fall', 'Spring', 'Summer'])


class AttendanceSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttendanceSession
    
    course_section = factory.SubFactory(CourseSectionFactory)
    faculty = factory.SubFactory(FacultyFactory)
    timetable_slot = factory.SubFactory(TimetableSlotFactory)
    scheduled_date = factory.LazyFunction(lambda: timezone.now().date())
    start_datetime = factory.LazyAttribute(lambda o: timezone.datetime.combine(
        o.scheduled_date if isinstance(o.scheduled_date, date) else timezone.datetime.strptime(str(o.scheduled_date), '%Y-%m-%d').date(), 
        o.timetable_slot.start_time
    ).replace(tzinfo=timezone.get_current_timezone()))
    end_datetime = factory.LazyAttribute(lambda o: timezone.datetime.combine(
        o.scheduled_date if isinstance(o.scheduled_date, date) else timezone.datetime.strptime(str(o.scheduled_date), '%Y-%m-%d').date(), 
        o.timetable_slot.end_time
    ).replace(tzinfo=timezone.get_current_timezone()))
    room = factory.LazyAttribute(lambda o: o.timetable_slot.room)
    status = 'scheduled'
    makeup = False
    notes = factory.Faker('text', max_nb_chars=100)


class StudentSnapshotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentSnapshot
    
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    course_section = factory.SelfAttribute('session.course_section')
    student_batch = factory.SelfAttribute('student.student_batch')
    roll_number = factory.SelfAttribute('student.roll_number')
    full_name = factory.LazyAttribute(lambda o: f"{o.student.first_name} {o.student.last_name}")
    email = factory.LazyAttribute(lambda o: o.student.email or "")
    phone = factory.LazyAttribute(lambda o: o.student.student_mobile or "")
    academic_year = factory.LazyAttribute(lambda o: o.student.academic_year or "")
    semester = factory.LazyAttribute(lambda o: o.student.semester or "")
    year_of_study = factory.LazyAttribute(lambda o: o.student.year_of_study or "1")
    section = factory.LazyAttribute(lambda o: o.student.section or "A")


class AttendanceRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttendanceRecord
    
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    mark = 'present'
    source = 'manual'
    reason = factory.Faker('text', max_nb_chars=100)
    marked_by = factory.SubFactory(UserFactory)


class AttendanceCorrectionRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttendanceCorrectionRequest
    
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    requested_by = factory.SubFactory(UserFactory)
    from_mark = factory.Faker('random_element', elements=['present', 'absent', 'late', 'excused'])
    to_mark = factory.Faker('random_element', elements=['present', 'absent', 'late', 'excused'])
    reason = factory.Faker('text', max_nb_chars=200)
    status = 'pending'


class LeaveApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LeaveApplication
    
    student = factory.SubFactory(StudentFactory)
    leave_type = factory.Faker('random_element', elements=['medical', 'maternity', 'on_duty', 'sport', 'personal'])
    start_date = factory.Faker('date_between', start_date='-30d', end_date='+30d')
    end_date = factory.LazyAttribute(lambda o: o.start_date + timezone.timedelta(days=fake.random_int(min=1, max=7)))
    reason = factory.Faker('text', max_nb_chars=200)
    status = 'pending'
    affects_attendance = True


class AttendanceConfigurationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttendanceConfiguration
    
    key = factory.Faker('word')
    value = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=100)
    data_type = 'string'  # Default to string for consistency
    is_active = True
    updated_by = factory.SubFactory(UserFactory)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to ensure data_type matches value type"""
        # If value is provided and data_type is not explicitly set, infer data_type
        if 'value' in kwargs and 'data_type' not in kwargs:
            value = kwargs['value']
            if isinstance(value, str):
                # Try to determine if it's a number
                try:
                    int(value)
                    kwargs['data_type'] = 'integer'
                except ValueError:
                    try:
                        float(value)
                        kwargs['data_type'] = 'float'
                    except ValueError:
                        if value.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
                            kwargs['data_type'] = 'boolean'
                        else:
                            kwargs['data_type'] = 'string'
        return super()._create(model_class, *args, **kwargs)


class AttendanceAuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AttendanceAuditLog
    
    entity_type = factory.Faker('random_element', elements=['AttendanceRecord', 'AttendanceSession', 'LeaveApplication'])
    entity_id = factory.Faker('uuid4')
    action = factory.Faker('random_element', elements=['create', 'update', 'delete', 'approve', 'reject'])
    performed_by = factory.SubFactory(UserFactory)
    before = factory.LazyFunction(lambda: {"status": "old"})
    after = factory.LazyFunction(lambda: {"status": "new"})
    reason = factory.Faker('text', max_nb_chars=100)
    source = factory.Faker('random_element', elements=['system', 'admin', 'api'])


# Specialized factories for specific test scenarios

class PresentAttendanceRecordFactory(AttendanceRecordFactory):
    mark = 'present'
    source = 'manual'


class AbsentAttendanceRecordFactory(AttendanceRecordFactory):
    mark = 'absent'
    source = 'manual'


class QRAttendanceRecordFactory(AttendanceRecordFactory):
    mark = 'present'
    source = 'qr'


class BiometricAttendanceRecordFactory(AttendanceRecordFactory):
    mark = 'present'
    source = 'biometric'
    vendor_event_id = factory.Faker('uuid4')


class OpenAttendanceSessionFactory(AttendanceSessionFactory):
    status = 'open'
    auto_opened = True


class ClosedAttendanceSessionFactory(AttendanceSessionFactory):
    status = 'closed'
    auto_closed = True


class LockedAttendanceSessionFactory(AttendanceSessionFactory):
    status = 'locked'


class MakeupAttendanceSessionFactory(AttendanceSessionFactory):
    makeup = True
    notes = 'Makeup class for missed session'


class PendingCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    status = 'pending'
    from_mark = 'absent'
    to_mark = 'present'


class ApprovedCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    status = 'approved'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)


class RejectedCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    status = 'rejected'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = factory.Faker('text', max_nb_chars=100)


class PendingLeaveApplicationFactory(LeaveApplicationFactory):
    status = 'pending'
    leave_type = 'medical'


class ApprovedLeaveApplicationFactory(LeaveApplicationFactory):
    status = 'approved'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)


class RejectedLeaveApplicationFactory(LeaveApplicationFactory):
    status = 'rejected'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = factory.Faker('text', max_nb_chars=100)


# Factory for creating complete attendance scenarios

class AttendanceScenarioFactory:
    """Factory for creating complete attendance scenarios with related data"""
    
    @staticmethod
    def create_session_with_students(num_students=5, session_status='open'):
        """Create an attendance session with enrolled students and their records"""
        session = AttendanceSessionFactory(status=session_status)
        
        # Create students and enroll them
        students = StudentFactory.create_batch(num_students)
        for student in students:
            # Create student snapshot
            StudentSnapshotFactory(session=session, student=student)
            
            # Create attendance record
            AttendanceRecordFactory(session=session, student=student)
        
        return session, students
    
    @staticmethod
    def create_correction_workflow():
        """Create a complete correction request workflow"""
        # Create session with absent student
        session = AttendanceSessionFactory(status='closed')
        student = StudentFactory()
        StudentSnapshotFactory(session=session, student=student)
        record = AbsentAttendanceRecordFactory(session=session, student=student)
        
        # Create correction request
        correction_request = PendingCorrectionRequestFactory(
            session=session,
            student=student,
            from_mark='absent',
            to_mark='present'
        )
        
        return session, student, record, correction_request
    
    @staticmethod
    def create_leave_workflow():
        """Create a complete leave application workflow"""
        student = StudentFactory()
        leave_application = PendingLeaveApplicationFactory(student=student)
        
        return student, leave_application
    
    @staticmethod
    def create_biometric_scenario():
        """Create a biometric attendance scenario"""
        session = OpenAttendanceSessionFactory()
        student = StudentFactory()
        StudentSnapshotFactory(session=session, student=student)
        
        # Create biometric record
        biometric_record = BiometricAttendanceRecordFactory(
            session=session,
            student=student,
            vendor_event_id=fake.uuid4()
        )
        
        return session, student, biometric_record



