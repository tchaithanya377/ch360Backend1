"""
Enhanced Attendance Factories for CampsHub360
Factory Boy factories for testing attendance system
"""

import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal

from .models_enhanced import (
    AttendanceConfiguration,
    AcademicCalendarHoliday,
    TimetableSlot,
    AttendanceSession,
    StudentSnapshot,
    AttendanceRecord,
    LeaveApplication,
    AttendanceCorrectionRequest,
    AttendanceAuditLog,
    AttendanceStatistics,
    BiometricDevice,
    BiometricTemplate,
)

from accounts.models import User
from students.models import Student, StudentBatch, AcademicYear
from academics.models import Course, CourseSection, AcademicProgram
from faculty.models import Faculty
from departments.models import Department


class UserFactory(DjangoModelFactory):
    """Factory for User model"""
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    is_active = True
    is_staff = False


class DepartmentFactory(DjangoModelFactory):
    """Factory for Department model"""
    class Meta:
        model = Department
    
    name = factory.Sequence(lambda n: f"Department {n}")
    code = factory.Sequence(lambda n: f"DEPT{n:03d}")
    is_active = True


class AcademicYearFactory(DjangoModelFactory):
    """Factory for AcademicYear model"""
    class Meta:
        model = AcademicYear
    
    year = factory.Sequence(lambda n: f"{2020 + n}-{2021 + n}")
    start_date = factory.LazyFunction(lambda: date.today().replace(month=7, day=1))
    end_date = factory.LazyFunction(lambda: date.today().replace(month=6, day=30, year=date.today().year + 1))
    is_current = True
    is_active = True


class AcademicProgramFactory(DjangoModelFactory):
    """Factory for AcademicProgram model"""
    class Meta:
        model = AcademicProgram
    
    name = factory.Sequence(lambda n: f"Program {n}")
    code = factory.Sequence(lambda n: f"PROG{n:03d}")
    level = "UG"
    department = factory.SubFactory(DepartmentFactory)
    duration_years = 4
    total_credits = 120
    is_active = True


class StudentBatchFactory(DjangoModelFactory):
    """Factory for StudentBatch model"""
    class Meta:
        model = StudentBatch
    
    department = factory.SubFactory(DepartmentFactory)
    academic_program = factory.SubFactory(AcademicProgramFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)
    semester = "1"
    year_of_study = "1"
    section = "A"
    batch_name = factory.LazyAttribute(lambda obj: f"{obj.department.code}-{obj.academic_year.year}-{obj.year_of_study}-{obj.section}")
    batch_code = factory.LazyAttribute(lambda obj: f"{obj.department.code}{obj.academic_year.year}{obj.year_of_study}{obj.section}")
    max_capacity = 70
    current_count = 0
    is_active = True


class StudentFactory(DjangoModelFactory):
    """Factory for Student model"""
    class Meta:
        model = Student
    
    roll_number = factory.Sequence(lambda n: f"STU{n:06d}")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=25)
    gender = factory.Iterator(['M', 'F'])
    student_batch = factory.SubFactory(StudentBatchFactory)
    email = factory.Sequence(lambda n: f"student{n}@example.com")
    student_mobile = factory.Faker('phone_number')
    status = 'ACTIVE'
    enrollment_date = factory.LazyFunction(lambda: date.today())


class FacultyFactory(DjangoModelFactory):
    """Factory for Faculty model"""
    class Meta:
        model = Faculty
    
    name = factory.Faker('name')
    apaar_faculty_id = factory.Sequence(lambda n: f"FAC{n:06d}")
    email = factory.Sequence(lambda n: f"faculty{n}@example.com")
    phone_number = factory.Faker('phone_number')
    designation = "LECTURER"
    department = "COMPUTER_SCIENCE"
    employment_type = "FULL_TIME"
    status = "ACTIVE"
    date_of_joining = factory.LazyFunction(lambda: date.today())


class CourseFactory(DjangoModelFactory):
    """Factory for Course model"""
    class Meta:
        model = Course
    
    code = factory.Sequence(lambda n: f"CS{n:03d}")
    title = factory.Sequence(lambda n: f"Course {n}")
    description = factory.Faker('text', max_nb_chars=200)
    level = "UG"
    credits = 3
    duration_weeks = 16
    max_students = 50
    status = "ACTIVE"


class CourseSectionFactory(DjangoModelFactory):
    """Factory for CourseSection model"""
    class Meta:
        model = CourseSection
    
    course = factory.SubFactory(CourseFactory)
    student_batch = factory.SubFactory(StudentBatchFactory)
    section_type = "LECTURE"
    faculty = factory.SubFactory(FacultyFactory)
    max_students = 50
    current_enrollment = 0
    is_active = True


class AttendanceConfigurationFactory(DjangoModelFactory):
    """Factory for AttendanceConfiguration model"""
    class Meta:
        model = AttendanceConfiguration
    
    key = factory.Sequence(lambda n: f"CONFIG_{n}")
    value = "default_value"
    description = factory.Faker('text', max_nb_chars=100)
    data_type = "string"
    is_active = True


class AcademicCalendarHolidayFactory(DjangoModelFactory):
    """Factory for AcademicCalendarHoliday model"""
    class Meta:
        model = AcademicCalendarHoliday
    
    name = factory.Faker('word')
    date = factory.Faker('date_between', start_date='-30d', end_date='+30d')
    is_full_day = True
    academic_year = factory.LazyFunction(lambda: f"{date.today().year}-{date.today().year + 1}")
    description = factory.Faker('text', max_nb_chars=100)
    affects_attendance = True


class TimetableSlotFactory(DjangoModelFactory):
    """Factory for TimetableSlot model"""
    class Meta:
        model = TimetableSlot
    
    course_section = factory.SubFactory(CourseSectionFactory)
    faculty = factory.SubFactory(FacultyFactory)
    day_of_week = factory.Iterator([0, 1, 2, 3, 4])  # Monday to Friday
    start_time = factory.Iterator(['09:00:00', '10:00:00', '11:00:00', '14:00:00', '15:00:00'])
    end_time = factory.Iterator(['09:50:00', '10:50:00', '11:50:00', '14:50:00', '15:50:00'])
    room = factory.Sequence(lambda n: f"Room {n}")
    is_active = True
    academic_year = factory.LazyFunction(lambda: f"{date.today().year}-{date.today().year + 1}")
    semester = "1"
    slot_type = "LECTURE"
    max_students = 50


class AttendanceSessionFactory(DjangoModelFactory):
    """Factory for AttendanceSession model"""
    class Meta:
        model = AttendanceSession
    
    course_section = factory.SubFactory(CourseSectionFactory)
    faculty = factory.SubFactory(FacultyFactory)
    timetable_slot = factory.SubFactory(TimetableSlotFactory)
    scheduled_date = factory.Faker('date_between', start_date='-7d', end_date='+7d')
    start_datetime = factory.LazyAttribute(lambda obj: datetime.combine(obj.scheduled_date, datetime.strptime('09:00:00', '%H:%M:%S').time()))
    end_datetime = factory.LazyAttribute(lambda obj: datetime.combine(obj.scheduled_date, datetime.strptime('09:50:00', '%H:%M:%S').time()))
    room = factory.Sequence(lambda n: f"Room {n}")
    status = "scheduled"
    auto_opened = False
    auto_closed = False
    makeup = False
    notes = factory.Faker('text', max_nb_chars=100)
    biometric_enabled = False
    biometric_device_id = ""


class StudentSnapshotFactory(DjangoModelFactory):
    """Factory for StudentSnapshot model"""
    class Meta:
        model = StudentSnapshot
    
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    course_section = factory.SubFactory(CourseSectionFactory)
    student_batch = factory.SubFactory(StudentBatchFactory)
    roll_number = factory.Sequence(lambda n: f"STU{n:06d}")
    full_name = factory.Faker('name')
    email = factory.Sequence(lambda n: f"student{n}@example.com")
    phone = factory.Faker('phone_number')
    academic_year = factory.LazyFunction(lambda: f"{date.today().year}-{date.today().year + 1}")
    semester = "1"
    year_of_study = "1"
    section = "A"


class AttendanceRecordFactory(DjangoModelFactory):
    """Factory for AttendanceRecord model"""
    class Meta:
        model = AttendanceRecord
    
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    mark = factory.Iterator(['present', 'absent', 'late', 'excused'])
    marked_at = factory.LazyFunction(timezone.now)
    source = factory.Iterator(['manual', 'qr', 'biometric', 'rfid'])
    reason = factory.Faker('text', max_nb_chars=100)
    notes = factory.Faker('text', max_nb_chars=100)
    device_id = factory.Sequence(lambda n: f"DEVICE_{n}")
    device_type = factory.Iterator(['mobile', 'tablet', 'desktop', 'biometric'])
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    sync_status = "synced"
    marked_by = factory.SubFactory(UserFactory)


class LeaveApplicationFactory(DjangoModelFactory):
    """Factory for LeaveApplication model"""
    class Meta:
        model = LeaveApplication
    
    student = factory.SubFactory(StudentFactory)
    leave_type = factory.Iterator(['medical', 'personal', 'on_duty', 'emergency'])
    start_date = factory.Faker('date_between', start_date='-7d', end_date='+7d')
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=1))
    reason = factory.Faker('text', max_nb_chars=200)
    status = factory.Iterator(['pending', 'approved', 'rejected'])
    affects_attendance = True
    auto_apply_to_sessions = True


class AttendanceCorrectionRequestFactory(DjangoModelFactory):
    """Factory for AttendanceCorrectionRequest model"""
    class Meta:
        model = AttendanceCorrectionRequest
    
    session = factory.SubFactory(AttendanceSessionFactory)
    student = factory.SubFactory(StudentFactory)
    from_mark = factory.Iterator(['absent', 'late'])
    to_mark = factory.Iterator(['present', 'excused'])
    reason = factory.Faker('text', max_nb_chars=200)
    status = factory.Iterator(['pending', 'approved', 'rejected'])
    requested_by = factory.SubFactory(UserFactory)


class AttendanceAuditLogFactory(DjangoModelFactory):
    """Factory for AttendanceAuditLog model"""
    class Meta:
        model = AttendanceAuditLog
    
    entity_type = factory.Iterator(['AttendanceRecord', 'AttendanceSession', 'LeaveApplication'])
    entity_id = factory.Sequence(lambda n: f"entity_{n}")
    action = factory.Iterator(['create', 'update', 'approve', 'reject', 'delete'])
    performed_by = factory.SubFactory(UserFactory)
    before = factory.LazyFunction(lambda: {"old_value": "test"})
    after = factory.LazyFunction(lambda: {"new_value": "test"})
    reason = factory.Faker('text', max_nb_chars=100)
    source = "system"
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    session_id = factory.Sequence(lambda n: f"session_{n}")
    student_id = factory.Sequence(lambda n: f"student_{n}")


class AttendanceStatisticsFactory(DjangoModelFactory):
    """Factory for AttendanceStatistics model"""
    class Meta:
        model = AttendanceStatistics
    
    student = factory.SubFactory(StudentFactory)
    course_section = factory.SubFactory(CourseSectionFactory)
    academic_year = factory.LazyFunction(lambda: f"{date.today().year}-{date.today().year + 1}")
    semester = "1"
    total_sessions = factory.Iterator([20, 25, 30])
    present_count = factory.Iterator([15, 20, 25])
    absent_count = factory.Iterator([3, 4, 5])
    late_count = factory.Iterator([1, 2, 3])
    excused_count = factory.Iterator([1, 1, 2])
    attendance_percentage = factory.LazyAttribute(lambda obj: round((obj.present_count / max(obj.total_sessions - obj.excused_count, 1)) * 100, 2))
    is_eligible_for_exam = factory.LazyAttribute(lambda obj: obj.attendance_percentage >= 75)
    period_start = factory.Faker('date_between', start_date='-30d', end_date='-15d')
    period_end = factory.Faker('date_between', start_date='-15d', end_date='today')


class BiometricDeviceFactory(DjangoModelFactory):
    """Factory for BiometricDevice model"""
    class Meta:
        model = BiometricDevice
    
    device_id = factory.Sequence(lambda n: f"BIO_DEV_{n}")
    device_name = factory.Sequence(lambda n: f"Biometric Device {n}")
    device_type = factory.Iterator(['fingerprint', 'face', 'iris', 'palm'])
    location = factory.Sequence(lambda n: f"Location {n}")
    room = factory.Sequence(lambda n: f"Room {n}")
    status = factory.Iterator(['active', 'inactive', 'maintenance'])
    last_seen = factory.LazyFunction(timezone.now)
    firmware_version = factory.Sequence(lambda n: f"v1.{n}.0")
    is_enabled = True
    auto_sync = True
    sync_interval_minutes = 5
    ip_address = factory.Faker('ipv4')
    port = 80
    api_endpoint = factory.Sequence(lambda n: f"http://device{n}.example.com/api")


class BiometricTemplateFactory(DjangoModelFactory):
    """Factory for BiometricTemplate model"""
    class Meta:
        model = BiometricTemplate
    
    student = factory.SubFactory(StudentFactory)
    device = factory.SubFactory(BiometricDeviceFactory)
    template_data = factory.Faker('text', max_nb_chars=500)
    template_hash = factory.Sequence(lambda n: f"hash_{n:064x}")
    quality_score = factory.Faker('pydecimal', left_digits=1, right_digits=2, positive=True, min_value=0.5, max_value=1.0)
    is_active = True
    enrolled_at = factory.LazyFunction(timezone.now)
    last_used = factory.LazyFunction(timezone.now)


# Specialized factories for specific test scenarios

class PresentAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for present attendance records"""
    mark = 'present'


class AbsentAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for absent attendance records"""
    mark = 'absent'


class LateAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for late attendance records"""
    mark = 'late'


class ExcusedAttendanceRecordFactory(AttendanceRecordFactory):
    """Factory for excused attendance records"""
    mark = 'excused'


class OpenAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for open attendance sessions"""
    status = 'open'
    actual_start_datetime = factory.LazyFunction(timezone.now)


class ClosedAttendanceSessionFactory(AttendanceSessionFactory):
    """Factory for closed attendance sessions"""
    status = 'closed'
    actual_start_datetime = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=1))
    actual_end_datetime = factory.LazyFunction(timezone.now)


class ApprovedLeaveApplicationFactory(LeaveApplicationFactory):
    """Factory for approved leave applications"""
    status = 'approved'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = factory.Faker('text', max_nb_chars=100)


class PendingLeaveApplicationFactory(LeaveApplicationFactory):
    """Factory for pending leave applications"""
    status = 'pending'


class ApprovedCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    """Factory for approved correction requests"""
    status = 'approved'
    decided_by = factory.SubFactory(UserFactory)
    decided_at = factory.LazyFunction(timezone.now)
    decision_note = factory.Faker('text', max_nb_chars=100)


class PendingCorrectionRequestFactory(AttendanceCorrectionRequestFactory):
    """Factory for pending correction requests"""
    status = 'pending'


class EligibleStudentStatisticsFactory(AttendanceStatisticsFactory):
    """Factory for eligible student statistics"""
    attendance_percentage = factory.Iterator([75.0, 80.0, 85.0, 90.0, 95.0])
    is_eligible_for_exam = True


class IneligibleStudentStatisticsFactory(AttendanceStatisticsFactory):
    """Factory for ineligible student statistics"""
    attendance_percentage = factory.Iterator([60.0, 65.0, 70.0, 74.0])
    is_eligible_for_exam = False
