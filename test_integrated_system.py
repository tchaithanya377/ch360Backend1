#!/usr/bin/env python
"""
Test script for the integrated academic system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

from attendance.models import AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord
from students.models import AcademicYear, Semester
from academics.models import CourseSection
from faculty.models import Faculty
from accounts.models import User

def test_academic_period_creation():
    """Test creating an academic period"""
    print("Testing Academic Period Creation...")
    
    # Create academic year
    academic_year, created = AcademicYear.objects.get_or_create(
        year='2024-2025',
        defaults={
            'start_date': '2024-09-01',
            'end_date': '2025-05-31',
            'is_current': True,
            'is_active': True
        }
    )
    print(f"Academic Year: {academic_year} (created: {created})")
    
    # Create semester
    semester, created = Semester.objects.get_or_create(
        academic_year=academic_year,
        semester_type='ODD',
        defaults={
            'name': 'Fall 2024',
            'start_date': '2024-09-01',
            'end_date': '2024-12-31',
            'is_current': True,
            'is_active': True
        }
    )
    print(f"Semester: {semester} (created: {created})")
    
    # Create academic period
    academic_period, created = AcademicPeriod.objects.get_or_create(
        academic_year=academic_year,
        semester=semester,
        defaults={
            'period_start': '2024-09-01',
            'period_end': '2024-12-31',
            'is_current': True,
            'is_active': True,
            'description': 'Fall 2024 Academic Period'
        }
    )
    print(f"Academic Period: {academic_period} (created: {created})")
    
    # Test properties
    print(f"Display Name: {academic_period.display_name}")
    print(f"Is Ongoing: {academic_period.is_ongoing}")
    print(f"Duration Days: {academic_period.get_duration_days()}")
    
    return academic_period

def test_current_period():
    """Test getting current academic period"""
    print("\nTesting Current Academic Period...")
    
    current_period = AcademicPeriod.get_current_period()
    if current_period:
        print(f"Current Period: {current_period}")
    else:
        print("No current academic period found")

def test_timetable_slot_with_academic_period():
    """Test creating timetable slot with academic period"""
    print("\nTesting Timetable Slot with Academic Period...")
    
    # Get or create academic period
    academic_period = AcademicPeriod.get_current_period()
    if not academic_period:
        academic_period = test_academic_period_creation()
    
    # Get a course section (assuming one exists)
    course_section = CourseSection.objects.first()
    if not course_section:
        print("No course sections found. Please create a course section first.")
        return
    
    # Get a faculty member
    faculty = Faculty.objects.first()
    if not faculty:
        print("No faculty found. Please create a faculty member first.")
        return
    
    # Create timetable slot
    timetable_slot, created = TimetableSlot.objects.get_or_create(
        academic_period=academic_period,
        course_section=course_section,
        faculty=faculty,
        day_of_week=0,  # Monday
        start_time='09:00:00',
        end_time='10:00:00',
        defaults={
            'slot_type': 'LECTURE',
            'room': 'A101',
            'is_active': True
        }
    )
    print(f"Timetable Slot: {timetable_slot} (created: {created})")
    
    # Test properties
    print(f"Academic Year Display: {timetable_slot.academic_year_display}")
    print(f"Semester Display: {timetable_slot.semester_display}")
    print(f"Duration Minutes: {timetable_slot.duration_minutes}")
    print(f"Can Generate Sessions: {timetable_slot.can_generate_sessions()}")
    
    return timetable_slot

def test_attendance_session_with_academic_period():
    """Test creating attendance session with academic period"""
    print("\nTesting Attendance Session with Academic Period...")
    
    # Get timetable slot
    timetable_slot = TimetableSlot.objects.filter(academic_period__isnull=False).first()
    if not timetable_slot:
        timetable_slot = test_timetable_slot_with_academic_period()
    
    if not timetable_slot:
        print("No timetable slot found. Cannot test attendance session.")
        return
    
    # Create attendance session
    from datetime import date, time
    from django.utils import timezone
    
    attendance_session, created = AttendanceSession.objects.get_or_create(
        timetable_slot=timetable_slot,
        scheduled_date=date.today(),
        defaults={
            'start_datetime': timezone.datetime.combine(date.today(), time(9, 0)),
            'end_datetime': timezone.datetime.combine(date.today(), time(10, 0)),
            'room': timetable_slot.room,
            'status': 'scheduled'
        }
    )
    print(f"Attendance Session: {attendance_session} (created: {created})")
    
    # Test properties
    print(f"Academic Year Display: {attendance_session.academic_year_display}")
    print(f"Semester Display: {attendance_session.semester_display}")
    print(f"Duration Minutes: {attendance_session.duration_minutes}")
    
    return attendance_session

def test_system_integration():
    """Test the complete system integration"""
    print("\n" + "="*50)
    print("TESTING INTEGRATED ACADEMIC SYSTEM")
    print("="*50)
    
    try:
        # Test 1: Academic Period Creation
        academic_period = test_academic_period_creation()
        
        # Test 2: Current Period
        test_current_period()
        
        # Test 3: Timetable Slot
        timetable_slot = test_timetable_slot_with_academic_period()
        
        # Test 4: Attendance Session
        attendance_session = test_attendance_session_with_academic_period()
        
        print("\n" + "="*50)
        print("INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("="*50)
        
        # Summary
        print(f"\nSummary:")
        print(f"- Academic Periods: {AcademicPeriod.objects.count()}")
        print(f"- Timetable Slots: {TimetableSlot.objects.count()}")
        print(f"- Attendance Sessions: {AttendanceSession.objects.count()}")
        print(f"- Attendance Records: {AttendanceRecord.objects.count()}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_system_integration()
