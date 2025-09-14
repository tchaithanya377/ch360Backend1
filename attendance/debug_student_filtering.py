"""
Debug script to help verify student filtering is working correctly.
Run this script to check the relationship between sessions, course sections, and student batches.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

from attendance.models import AttendanceSession
from students.models import Student
from academics.models import CourseSection


def debug_session_students(session_id):
    """Debug function to check student filtering for a specific session"""
    try:
        session = AttendanceSession.objects.select_related(
            'course_section__student_batch'
        ).get(id=session_id)
        
        print(f"=== DEBUGGING SESSION {session_id} ===")
        print(f"Session: {session}")
        print(f"Course Section: {session.course_section}")
        
        if session.course_section:
            print(f"Course: {session.course_section.course}")
            print(f"Student Batch: {session.course_section.student_batch}")
            
            if session.course_section.student_batch:
                print(f"Batch Name: {session.course_section.student_batch.batch_name}")
                print(f"Batch Code: {session.course_section.student_batch.batch_code}")
                
                # Get students from this batch
                batch_students = Student.objects.filter(
                    student_batch=session.course_section.student_batch
                ).order_by('roll_number')
                
                print(f"\nStudents in batch '{session.course_section.student_batch.batch_name}':")
                for student in batch_students:
                    print(f"  - {student.roll_number}: {student.full_name}")
                
                print(f"\nTotal students in batch: {batch_students.count()}")
            else:
                print("No student batch assigned to this course section")
        else:
            print("No course section assigned to this session")
            
    except AttendanceSession.DoesNotExist:
        print(f"Session with ID {session_id} not found")
    except Exception as e:
        print(f"Error: {e}")


def list_all_sessions():
    """List all attendance sessions with their details"""
    sessions = AttendanceSession.objects.select_related(
        'course_section__student_batch'
    ).all()[:10]  # Limit to first 10 for readability
    
    print("=== ALL ATTENDANCE SESSIONS ===")
    for session in sessions:
        batch_info = "No Batch" if not session.course_section or not session.course_section.student_batch else session.course_section.student_batch.batch_name
        print(f"ID: {session.id} | {session} | Batch: {batch_info}")


def list_all_students_by_batch():
    """List all students grouped by their batches"""
    from students.models import StudentBatch
    
    batches = StudentBatch.objects.all()[:5]  # Limit to first 5 batches
    
    print("=== STUDENTS BY BATCH ===")
    for batch in batches:
        students = Student.objects.filter(student_batch=batch)
        print(f"\nBatch: {batch.batch_name} ({students.count()} students)")
        for student in students[:3]:  # Show first 3 students per batch
            print(f"  - {student.roll_number}: {student.full_name}")
        if students.count() > 3:
            print(f"  ... and {students.count() - 3} more")


if __name__ == "__main__":
    print("Student Filtering Debug Script")
    print("=" * 40)
    
    # List all sessions
    list_all_sessions()
    
    print("\n" + "=" * 40)
    
    # List students by batch
    list_all_students_by_batch()
    
    print("\n" + "=" * 40)
    print("To debug a specific session, run:")
    print("python manage.py shell")
    print(">>> from attendance.debug_student_filtering import debug_session_students")
    print(">>> debug_session_students(YOUR_SESSION_ID)")
