"""
Comprehensive Factory classes for creating test data for the attendance app.
Uses factory_boy for generating test instances with proper relationships.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from datetime import date, time, datetime, timedelta
from django.utils import timezone
import uuid

from attendance.models import (
    AcademicPeriod, AttendanceConfiguration, AcademicCalendarHoliday,
    TimetableSlot, AttendanceSession, StudentSnapshot, AttendanceRecord,
    LeaveApplication, AttendanceCorrectionRequest, AttendanceAuditLog,
    AttendanceStatistics, BiometricDevice, BiometricTemplate
)
from students.models import Student, StudentBatch, AcademicYear, Semester
from academics.models import Course, CourseSection, AcademicProgram, Timetable
from departments.models import Department
from faculty.models import Faculty

User = get_user_model()


# =============================================================================
# BASE FACTORIES
# =============================================================================

class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    is_active = True
    is_staff = False


class AdminUserFactory(UserFactory):
    """Factory for creating admin User instances"""
    is_staff = True
    is_superuser = True


class DepartmentFactory(DjangoModelFactory):
    """Factory for creating Department instances"""
    class Meta:
        model = Department

    name = factory.Faker('company')
    short_name = factory.Sequence(lambda n: f"DEP{n:02d}")
    code = factory.Sequence(lambda n: f"DEP{n:03d}")
    department_type = 'ACADEMIC'
    status = 'ACTIVE'
    is_active = True
    description = factory.Faker('text', max_nb_chars=200)
    email = factory.Faker('email')
    phone = factory.Faker('numerify', text='+91##########')
    building = factory.Faker('building_number')
    established_date = factory.Faker('date_between', start_date='-50y', end_date='-1y')
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle unique constraint violations"""
        try:
            return super()._create(model_class, *args, **kwargs)
        except Exception as e:
            if 'already exists' in str(e):
                # If code or short_name already exists, generate new ones
                import uuid
                unique_suffix = uuid.uuid4().hex[:6].upper()
                kwargs['code'] = f"DEP{unique_suffix}"
                kwargs['short_name'] = f"DEP{unique_suffix[:3]}"
                return super()._create(model_class, *args, **kwargs)
            raise


class AcademicYearFactory(DjangoModelFactory):
    """Factory for creating AcademicYear instances"""
    class Meta:
        model = AcademicYear

    year = factory.Sequence(lambda n: f"{2030 + n}-{2031 + n}")
    start_date = factory.LazyFunction(lambda: date.today().replace(month=8, day=1))
    end_date = factory.LazyFunction(lambda: date.today().replace(month=7, day=31, year=date.today().year + 1))
    is_current = False  # Default to False to avoid constraint violations
    is_active = True
    description = factory.Faker('text', max_nb_chars=100)  # Required field in database
    status = 'ACTIVE'  # Required field in database
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle uniqueness and database differences"""
        from django.db import connection
        import random

        # Remove fields that don't exist in the Django model
        kwargs.pop('description', None)
        kwargs.pop('status', None)
        
        # Handle uniqueness for year field
        year = kwargs.get('year')
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Use the standard Django ORM with only model-defined fields
                kwargs['year'] = year
                return super()._create(model_class, *args, **kwargs)
            except Exception as e:
                if ('UNIQUE constraint failed' in str(e) or 'duplicate key value' in str(e)) and 'year' in str(e):
                    # Generate new unique year
                    base_year = 2030 + attempt + random.randint(1, 1000)
                    year = f"{base_year}-{base_year + 1}"
                    continue
                else:
                    raise
        else:
            raise Exception(f"Failed to create unique AcademicYear after {max_attempts} attempts")
    
    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        """Override _build to handle database differences"""
        # Remove fields that don't exist in the Django model
        kwargs.pop('description', None)
        kwargs.pop('status', None)
        
        return super()._build(model_class, *args, **kwargs)


class SemesterFactory(DjangoModelFactory):
    """Factory for creating Semester instances"""
    class Meta:
        model = Semester

    academic_year = factory.SubFactory(AcademicYearFactory)
    name = factory.LazyAttribute(lambda obj: f"Fall {obj.academic_year.year.split('-')[0]}")
    semester_type = factory.Iterator(['ODD', 'EVEN', 'SUMMER'])
    start_date = factory.LazyAttribute(lambda obj: obj.academic_year.start_date)
    end_date = factory.LazyAttribute(lambda obj: obj.academic_year.end_date)
    is_current = factory.Iterator([True, False])
    is_active = True


class AcademicProgramFactory(DjangoModelFactory):
    """Factory for creating AcademicProgram instances"""
    class Meta:
        model = AcademicProgram

    name = factory.Faker('sentence', nb_words=4)
    code = factory.Sequence(lambda n: f"PROG{n:03d}")
    level = factory.Iterator(['UG', 'PG', 'PHD'])
    department = factory.SubFactory(DepartmentFactory)
    duration_years = 4
    total_credits = 120
    description = factory.Faker('text', max_nb_chars=500)
    is_active = True
    status = 'ACTIVE'


class StudentBatchFactory(DjangoModelFactory):
    """Factory for creating StudentBatch instances"""
    class Meta:
        model = StudentBatch

    department = factory.SubFactory(DepartmentFactory)
    academic_program = factory.SubFactory(AcademicProgramFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    semester = factory.Iterator(['1', '2', '3', '4', '5', '6', '7', '8'])
    year_of_study = factory.Iterator(['1', '2', '3', '4'])
    section = factory.Iterator(['A', 'B', 'C', 'D'])
    batch_name = factory.LazyAttribute(lambda obj: f"{obj.department.code}-{obj.academic_year.year.split('-')[0]}-{obj.year_of_study}-{obj.section}")
    batch_code = factory.LazyAttribute(lambda obj: f"{obj.batch_name}-001")
    max_capacity = 70
    current_count = 0
    is_active = True


class FacultyFactory(DjangoModelFactory):
    """Factory for creating Faculty instances"""
    class Meta:
        model = Faculty

    employee_id = factory.Sequence(lambda n: f"F{n:04d}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com")
    apaar_faculty_id = factory.Sequence(lambda n: f"APAAR{n:06d}")
    phone_number = factory.Sequence(lambda n: f"+123456789{n:02d}")
    designation = factory.Iterator(['LECTURER', 'ASSISTANT_PROFESSOR', 'ASSOCIATE_PROFESSOR', 'PROFESSOR'])
    department = 'COMPUTER_SCIENCE'
    department_ref = factory.SubFactory(DepartmentFactory)
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle unique constraint violations"""
        import uuid
        unique_suffix = uuid.uuid4().hex[:6].upper()
        
        # Ensure unique values from the start
        kwargs['apaar_faculty_id'] = f"APAAR{unique_suffix}"
        kwargs['employee_id'] = f"F{unique_suffix}"
        
        try:
            return super()._create(model_class, *args, **kwargs)
        except Exception as e:
            if 'apaar_faculty_id' in str(e) or 'employee_id' in str(e) or 'username' in str(e):
                # If any unique field already exists, generate new ones
                unique_suffix = uuid.uuid4().hex[:6].upper()
                kwargs['apaar_faculty_id'] = f"APAAR{unique_suffix}"
                kwargs['employee_id'] = f"F{unique_suffix}"
                return super()._create(model_class, *args, **kwargs)
            raise


class CourseFactory(DjangoModelFactory):
    """Factory for creating Course instances"""
    class Meta:
        model = Course

    code = factory.Sequence(lambda n: f"CS{n:03d}")
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=200)
    level = 'UG'
    credits = factory.Faker('random_int', min=1, max=6)
    duration_weeks = 16
    max_students = 50
    department = factory.SubFactory(DepartmentFactory)
    status = 'ACTIVE'
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle unique constraint violations"""
        try:
            return super()._create(model_class, *args, **kwargs)
        except Exception as e:
            if 'code' in str(e) and 'already exists' in str(e):
                # If code already exists, generate a new one
                import uuid
                kwargs['code'] = f"CS{uuid.uuid4().hex[:6].upper()}"
                return super()._create(model_class, *args, **kwargs)
            raise


class CourseSectionFactory(DjangoModelFactory):
    """Factory for creating CourseSection instances"""
    class Meta:
        model = CourseSection

    course = factory.SubFactory(CourseFactory)
    student_batch = factory.SubFactory(StudentBatchFactory)
    section_type = factory.Iterator(['LECTURE', 'LAB', 'TUTORIAL'])
    max_students = factory.LazyAttribute(lambda obj: obj.course.max_students)
    current_enrollment = 0
    is_active = True
    faculty = factory.SubFactory(FacultyFactory)


class StudentFactory(DjangoModelFactory):
    """Factory for creating Student instances"""
    class Meta:
        model = Student

    roll_number = factory.Sequence(lambda n: f"STU{n:06d}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    middle_name = factory.Faker('first_name')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=25)
    gender = factory.Iterator(['M', 'F', 'O'])
    student_batch = factory.SubFactory(StudentBatchFactory)
    status = 'ACTIVE'
    email = factory.LazyAttribute(lambda obj: f"{obj.roll_number.lower()}@example.com")
    student_mobile = factory.Sequence(lambda n: f"+123456789{n:02d}")
    father_name = factory.Faker('name_male')
    mother_name = factory.Faker('name_female')
    address_line1 = factory.Faker('street_address')
    address_line2 = factory.Faker('secondary_address')
    city = factory.Faker('city')
    state = factory.Faker('state')
    postal_code = factory.Faker('postcode')
    country = 'India'


# =============================================================================
# ATTENDANCE SPECIFIC FACTORIES
# =============================================================================

class AcademicPeriodFactory(DjangoModelFactory):
    """Factory for creating AcademicPeriod instances"""
    class Meta:
        model = AcademicPeriod

    academic_year = factory.SubFactory(AcademicYearFactory)
    semester = factory.SubFactory(SemesterFactory)
    is_current = False  # Default to False to avoid constraint violations
    is_active = True
    period_start = factory.LazyFunction(lambda: date.today().replace(month=8, day=1))
    period_end = factory.LazyFunction(lambda: date.today().replace(month=7, day=31, year=date.today().year + 1))
    description = factory.Faker('text', max_nb_chars=200)
    created_by = factory.SubFactory(UserFactory)


class AttendanceConfigurationFactory(DjangoModelFactory):
    """Factory for creating AttendanceConfiguration instances"""
    class Meta:
        model = AttendanceConfiguration

    key = factory.Sequence(lambda n: f"CONFIG_KEY_{n}")
    value = "75"  # Default integer value
    description = factory.Faker('text', max_nb_chars=200)
    data_type = "integer"
    is_active = True
    updated_by = factory.SubFactory(UserFactory)


class AcademicCalendarHolidayFactory(DjangoModelFactory):
    """Factory for creating AcademicCalendarHoliday instances"""
    class Meta:
        model = AcademicCalendarHoliday

    name = factory.Faker('sentence', nb_words=3)
    date = factory.Faker('date_between', start_date='-30d', end_date='+30d')
    is_full_day = True
    academic_year = factory.LazyAttribute(lambda obj: f"{date.today().year}-{date.today().year + 1}")
    description = factory.Faker('text', max_nb_chars=200)
    affects_attendance = True


class TimetableSlotFactory(DjangoModelFactory):
    """Factory for creating TimetableSlot instances"""
    class Meta:
        model = TimetableSlot

    academic_period = factory.SubFactory(AcademicPeriodFactory)
    course_section = factory.SubFactory(CourseSectionFactory)
    faculty = factory.SubFactory(FacultyFactory)
    day_of_week = factory.Iterator([0, 1, 2, 3, 4, 5, 6])  # Monday to Sunday
    start_time = factory.Iterator([time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 0)])
    end_time = factory.LazyAttribute(lambda obj: time(obj.start_time.hour + 1, obj.start_time.minute))
    room = factory.Sequence(lambda n: f"R{n:03d}")
    is_active = True
    academic_year = factory.LazyAttribute(lambda obj: obj.academic_period.academic_year.year)
    semester = factory.LazyAttribute(lambda obj: obj.academic_period.semester.name)
    slot_type = factory.Iterator(['LECTURE', 'LAB', 'TUTORIAL', 'SEMINAR'])
    max_students = 50


class TimetableFactory(DjangoModelFactory):
    """Factory for creating Timetable instances"""
    class Meta:
        model = Timetable

    course_section = factory.SubFactory(CourseSectionFactory)
    timetable_type = factory.Iterator(['REGULAR', 'EXAM', 'MAKEUP', 'SPECIAL'])
    day_of_week = factory.Iterator(['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'])
    start_time = factory.Iterator([time(9, 0), time(10, 0), time(11, 0), time(14, 0), time(15, 0)])
    end_time = factory.LazyAttribute(lambda obj: time(obj.start_time.hour + 1, obj.start_time.minute))
    room = factory.Sequence(lambda n: f"R{n:03d}")
    is_active = True
    notes = factory.Faker('sentence', nb_words=6)


class AttendanceSessionFactory(DjangoModelFactory):
    """Factory for creating AttendanceSession instances"""
    class Meta:
        model = AttendanceSession

    academic_period = factory.SubFactory(AcademicPeriodFactory)
    course_section = factory.SubFactory(CourseSectionFactory)
    faculty = factory.SubFactory(FacultyFactory)
    timetable_slot = factory.SubFactory(TimetableSlotFactory)
    scheduled_date = factory.Faker('date_between', start_date='-30d', end_date='+30d')
    start_datetime = factory.LazyAttribute(lambda obj: timezone.make_aware(datetime.combine(obj.scheduled_date, time(9, 0))))
    end_datetime = factory.LazyAttribute(lambda obj: timezone.make_aware(datetime.combine(obj.scheduled_date, time(10, 0))))
    room = factory.Sequence(lambda n: f"R{n:03d}")
    status = factory.Iterator(['scheduled', 'open', 'closed', 'locked', 'cancelled'])
    auto_opened = False
    auto_closed = False
    makeup = False
    notes = factory.Faker('text', max_nb_chars=200)
    qr_token = factory.LazyFunction(lambda: str(uuid.uuid4()))
    qr_expires_at = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=1))
    qr_generated_at = factory.LazyFunction(timezone.now)
    biometric_enabled = False
    biometric_device_id = factory.Sequence(lambda n: f"DEVICE_{n}")
    offline_sync_token = factory.LazyFunction(lambda: str(uuid.uuid4()))
    last_sync_at = factory.LazyFunction(timezone.now)


class StudentSnapshotFactory(DjangoModelFactory):
    """Factory for creating StudentSnapshot instances"""
    class Meta:
        model = StudentSnapshot

    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    course_section = factory.LazyAttribute(lambda obj: obj.session.course_section)
    student_batch = factory.LazyAttribute(lambda obj: obj.student.student_batch)
    roll_number = factory.LazyAttribute(lambda obj: obj.student.roll_number)
    full_name = factory.LazyAttribute(lambda obj: f"{obj.student.first_name} {obj.student.last_name}")
    email = factory.LazyAttribute(lambda obj: obj.student.email)
    phone = factory.LazyAttribute(lambda obj: obj.student.student_mobile)
    academic_year = factory.LazyAttribute(lambda obj: obj.student.student_batch.academic_year.year)
    semester = factory.LazyAttribute(lambda obj: obj.student.student_batch.semester)
    year_of_study = factory.LazyAttribute(lambda obj: obj.student.student_batch.year_of_study)
    section = factory.LazyAttribute(lambda obj: obj.student.student_batch.section)


class AttendanceRecordFactory(DjangoModelFactory):
    """Factory for creating AttendanceRecord instances"""
    class Meta:
        model = AttendanceRecord

    academic_period = factory.LazyAttribute(lambda obj: obj.session.academic_period)
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    mark = factory.Iterator(['present', 'absent', 'late', 'excused'])
    marked_at = factory.LazyFunction(timezone.now)
    source = factory.Iterator(['manual', 'qr', 'biometric', 'rfid', 'offline', 'import', 'system'])
    reason = factory.Faker('text', max_nb_chars=200)
    notes = factory.Faker('text', max_nb_chars=200)
    device_id = factory.Sequence(lambda n: f"DEVICE_{n}")
    device_type = factory.Iterator(['mobile', 'tablet', 'desktop', 'biometric'])
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    location_lat = factory.Faker('latitude')
    location_lng = factory.Faker('longitude')
    client_uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    sync_status = factory.Iterator(['pending', 'synced', 'conflict'])
    vendor_event_id = factory.Sequence(lambda n: f"VENDOR_EVENT_{n}")
    vendor_data = factory.LazyFunction(lambda: {"device_info": "test_device"})
    marked_by = factory.SubFactory(UserFactory)
    last_modified_by = factory.SubFactory(UserFactory)


class LeaveApplicationFactory(DjangoModelFactory):
    """Factory for creating LeaveApplication instances"""
    class Meta:
        model = LeaveApplication

    student = factory.SubFactory(StudentFactory)
    leave_type = factory.Iterator(['medical', 'maternity', 'on_duty', 'sport', 'personal', 'emergency', 'other'])
    start_date = factory.Faker('date_between', start_date='-30d', end_date='+30d')
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=3))
    reason = factory.Faker('text', max_nb_chars=500)
    supporting_document = None
    status = factory.Iterator(['pending', 'approved', 'rejected', 'cancelled'])
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = factory.Faker('text', max_nb_chars=200)
    affects_attendance = True
    auto_apply_to_sessions = True


class AttendanceCorrectionRequestFactory(DjangoModelFactory):
    """Factory for creating AttendanceCorrectionRequest instances"""
    class Meta:
        model = AttendanceCorrectionRequest

    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    from_mark = factory.Iterator(['present', 'absent', 'late', 'excused'])
    to_mark = factory.Iterator(['present', 'absent', 'late', 'excused'])
    reason = factory.Faker('text', max_nb_chars=500)
    supporting_document = None
    requested_by = factory.SubFactory(UserFactory)
    status = factory.Iterator(['pending', 'approved', 'rejected', 'cancelled'])
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = factory.Faker('text', max_nb_chars=200)


class AttendanceAuditLogFactory(DjangoModelFactory):
    """Factory for creating AttendanceAuditLog instances"""
    class Meta:
        model = AttendanceAuditLog

    entity_type = factory.Iterator(['AttendanceSession', 'AttendanceRecord', 'LeaveApplication', 'AttendanceCorrectionRequest'])
    entity_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    action = factory.Iterator(['create', 'update', 'delete', 'approve', 'reject', 'open', 'close'])
    performed_by = factory.SubFactory(UserFactory)
    before = factory.LazyFunction(lambda: {"status": "old_status"})
    after = factory.LazyFunction(lambda: {"status": "new_status"})
    reason = factory.Faker('text', max_nb_chars=200)
    source = factory.Iterator(['system', 'api', 'admin', 'mobile'])
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    student_id = factory.LazyFunction(lambda: str(uuid.uuid4()))


class AttendanceStatisticsFactory(DjangoModelFactory):
    """Factory for creating AttendanceStatistics instances"""
    class Meta:
        model = AttendanceStatistics

    student = factory.SubFactory(StudentFactory)
    course_section = factory.SubFactory(CourseSectionFactory)
    academic_year = factory.LazyAttribute(lambda obj: obj.student.student_batch.academic_year.year)
    semester = factory.LazyAttribute(lambda obj: obj.student.student_batch.semester)
    total_sessions = factory.Iterator([10, 15, 20, 25, 30])
    present_count = factory.Iterator([8, 12, 16, 20, 24])
    absent_count = factory.Iterator([1, 2, 3, 4, 5])
    late_count = factory.Iterator([1, 1, 1, 1, 1])
    excused_count = factory.Iterator([0, 0, 0, 0, 0])
    attendance_percentage = factory.LazyAttribute(lambda obj: round((obj.present_count / obj.total_sessions) * 100, 2))
    is_eligible_for_exam = factory.LazyAttribute(lambda obj: obj.attendance_percentage >= 75)
    period_start = factory.Faker('date_between', start_date='-60d', end_date='-30d')
    period_end = factory.Faker('date_between', start_date='-30d', end_date='today')
    last_calculated = factory.LazyFunction(timezone.now)


class BiometricDeviceFactory(DjangoModelFactory):
    """Factory for creating BiometricDevice instances"""
    class Meta:
        model = BiometricDevice

    device_id = factory.Sequence(lambda n: f"BIOMETRIC_DEVICE_{n}")
    device_name = factory.Faker('sentence', nb_words=3)
    device_type = factory.Iterator(['fingerprint', 'face', 'iris', 'palm'])
    location = factory.Faker('address')
    room = factory.Sequence(lambda n: f"R{n:03d}")
    status = factory.Iterator(['active', 'inactive', 'maintenance', 'error'])
    last_seen = factory.LazyFunction(timezone.now)
    firmware_version = factory.Sequence(lambda n: f"v1.{n}.0")
    is_enabled = True
    auto_sync = True
    sync_interval_minutes = 5
    ip_address = factory.Faker('ipv4')
    port = 80
    api_endpoint = factory.LazyAttribute(lambda obj: f"http://{obj.ip_address}:{obj.port}/api")
    api_key = factory.LazyFunction(lambda: str(uuid.uuid4()))


class BiometricTemplateFactory(DjangoModelFactory):
    """Factory for creating BiometricTemplate instances"""
    class Meta:
        model = BiometricTemplate

    student = factory.SubFactory(StudentFactory)
    device = factory.SubFactory(BiometricDeviceFactory)
    template_data = factory.LazyFunction(lambda: str(uuid.uuid4()))
    template_hash = factory.LazyFunction(lambda: str(uuid.uuid4()))
    quality_score = factory.Faker('pydecimal', left_digits=1, right_digits=2, positive=True, min_value=0.5, max_value=1.0)
    is_active = True
    enrolled_at = factory.LazyFunction(timezone.now)
    last_used = factory.LazyFunction(timezone.now)


# =============================================================================
# SPECIALIZED FACTORIES FOR SPECIFIC TEST SCENARIOS
# =============================================================================

class PresentAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for creating present attendance records"""
    mark = 'present'
    marked_at = factory.LazyFunction(timezone.now)


class AbsentAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for creating absent attendance records"""
    mark = 'absent'
    marked_at = factory.LazyFunction(timezone.now)


class LateAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for creating late attendance records"""
    mark = 'late'
    marked_at = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=15))


class ExcusedAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for creating excused attendance records"""
    mark = 'excused'
    marked_at = factory.LazyFunction(timezone.now)
    reason = factory.Faker('sentence', nb_words=5)


class QRAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for creating QR code attendance records"""
    source = 'qr'
    device_id = 'QR_SCANNER_001'
    device_type = 'mobile'


class BiometricAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for creating biometric attendance records"""
    source = 'biometric'
    device_id = 'BIOMETRIC_DEVICE_001'
    device_type = 'biometric'


class OpenAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for creating open attendance sessions"""
    status = 'open'
    actual_start_datetime = factory.LazyFunction(timezone.now)


class ClosedAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for creating closed attendance sessions"""
    status = 'closed'
    actual_start_datetime = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=1))
    actual_end_datetime = factory.LazyFunction(timezone.now)


class LockedAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for creating locked attendance sessions"""
    status = 'locked'


class CancelledAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for creating cancelled attendance sessions"""
    status = 'cancelled'
    notes = "Class cancelled due to holiday"


class FutureAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for creating future attendance sessions"""
    scheduled_date = factory.Faker('date_between', start_date='+1d', end_date='+30d')
    start_datetime = factory.LazyAttribute(lambda obj: timezone.make_aware(datetime.combine(obj.scheduled_date, time(9, 0))))
    end_datetime = factory.LazyAttribute(lambda obj: timezone.make_aware(datetime.combine(obj.scheduled_date, time(10, 0))))


class PastAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for creating past attendance sessions"""
    scheduled_date = factory.Faker('date_between', start_date='-30d', end_date='-1d')
    start_datetime = factory.LazyAttribute(lambda obj: timezone.make_aware(datetime.combine(obj.scheduled_date, time(9, 0))))
    end_datetime = factory.LazyAttribute(lambda obj: timezone.make_aware(datetime.combine(obj.scheduled_date, time(10, 0))))


class ApprovedLeaveApplicationFactory(LeaveApplicationFactory):
    """Factory for creating approved leave applications"""
    status = 'approved'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = "Approved for medical reasons"


class RejectedLeaveApplicationFactory(LeaveApplicationFactory):
    """Factory for creating rejected leave applications"""
    status = 'rejected'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = "Insufficient documentation"


class ApprovedCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    """Factory for creating approved correction requests"""
    status = 'approved'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = "Correction approved after verification"


class RejectedCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    """Factory for creating rejected correction requests"""
    status = 'rejected'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = "No valid reason provided"


class CurrentAcademicPeriodFactory(AcademicPeriodFactory):
    """Factory for creating current academic period"""
    is_current = True
    is_active = True


class InactiveAcademicPeriodFactory(AcademicPeriodFactory):
    """Factory for creating inactive academic period"""
    is_current = False
    is_active = False


class ActiveBiometricDeviceFactory(BiometricDeviceFactory):
    """Factory for creating active biometric devices"""
    status = 'active'
    is_enabled = True


class InactiveBiometricDeviceFactory(BiometricDeviceFactory):
    """Factory for creating inactive biometric devices"""
    status = 'inactive'
    is_enabled = False


class HighQualityBiometricTemplateFactory(BiometricTemplateFactory):
    """Factory for creating high-quality biometric templates"""
    quality_score = factory.Faker('pydecimal', left_digits=1, right_digits=2, positive=True, min_value=0.9, max_value=1.0)
    is_active = True


class LowQualityBiometricTemplateFactory(BiometricTemplateFactory):
    """Factory for creating low-quality biometric templates"""
    quality_score = factory.Faker('pydecimal', left_digits=1, right_digits=2, positive=True, min_value=0.3, max_value=0.6)
    is_active = False


# =============================================================================
# BULK DATA FACTORIES
# =============================================================================

class BulkAttendanceSessionFactory:
    """Factory for creating multiple attendance sessions"""
    
    @staticmethod
    def create_sessions_for_course_section(course_section, count=10, start_date=None, end_date=None):
        """Create multiple sessions for a course section"""
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today() + timedelta(days=30)
        
        sessions = []
        for i in range(count):
            session_date = start_date + timedelta(days=i)
            session = AttendanceSessionFactory(
                course_section=course_section,
                scheduled_date=session_date,
                start_datetime=timezone.make_aware(datetime.combine(session_date, time(9, 0))),
                end_datetime=timezone.make_aware(datetime.combine(session_date, time(10, 0)))
            )
            sessions.append(session)
        
        return sessions


class BulkAttendanceRecordFactory:
    """Factory for creating multiple attendance records"""
    
    @staticmethod
    def create_records_for_session(session, students, mark='present'):
        """Create attendance records for all students in a session"""
        records = []
        for student in students:
            record = AttendanceRecordFactory(
                session=session,
                student=student,
                mark=mark
            )
            records.append(record)
        
        return records


class BulkStudentFactory:
    """Factory for creating multiple students"""
    
    @staticmethod
    def create_students_for_batch(batch, count=30):
        """Create multiple students for a batch"""
        students = []
        for i in range(count):
            student = StudentFactory(
                student_batch=batch,
                roll_number=f"{batch.batch_code}-{i+1:03d}"
            )
            students.append(student)
        
        return students