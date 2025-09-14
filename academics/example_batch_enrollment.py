#!/usr/bin/env python
"""
Example script demonstrating the Batch Course Enrollment System

This script shows how to:
1. Create batch enrollments
2. Enroll students automatically
3. Check prerequisites
4. Manage enrollment status

Run this script from the Django shell:
python manage.py shell < academics/example_batch_enrollment.py
"""

from academics.models import BatchCourseEnrollment, CoursePrerequisite, Course, CourseSection
from students.models import StudentBatch, Student
from faculty.models import Faculty
from departments.models import Department
from students.models import AcademicYear

def create_example_data():
    """Create example data for demonstration"""
    print("Creating example data...")
    
    # Create academic year
    academic_year, created = AcademicYear.objects.get_or_create(
        year="2024-2025",
        defaults={
            'start_date': '2024-08-01',
            'end_date': '2025-07-31',
            'is_current': True,
            'is_active': True
        }
    )
    print(f"Academic Year: {academic_year}")
    
    # Create department
    department, created = Department.objects.get_or_create(
        name="Computer Science",
        defaults={
            'code': 'CS',
            'description': 'Computer Science Department'
        }
    )
    print(f"Department: {department}")
    
    # Create academic program
    from academics.models import AcademicProgram
    program, created = AcademicProgram.objects.get_or_create(
        code="BCS",
        defaults={
            'name': 'Bachelor of Computer Science',
            'level': 'UG',
            'department': department,
            'duration_years': 4,
            'total_credits': 120
        }
    )
    print(f"Academic Program: {program}")
    
    # Create student batch
    batch, created = StudentBatch.objects.get_or_create(
        batch_code="CS-2024-1-A",
        defaults={
            'department': department,
            'academic_program': program,
            'academic_year': academic_year,
            'year_of_study': '1',
            'section': 'A',
            'batch_name': 'CS-2024-1-A',
            'max_capacity': 50,
            'is_active': True
        }
    )
    print(f"Student Batch: {batch}")
    
    # Create courses
    course1, created = Course.objects.get_or_create(
        code="CS101",
        defaults={
            'title': 'Introduction to Programming',
            'description': 'Basic programming concepts',
            'level': 'UG',
            'credits': 3,
            'department': department,
            'status': 'ACTIVE'
        }
    )
    print(f"Course 1: {course1}")
    
    course2, created = Course.objects.get_or_create(
        code="CS102",
        defaults={
            'title': 'Data Structures',
            'description': 'Introduction to data structures',
            'level': 'UG',
            'credits': 3,
            'department': department,
            'status': 'ACTIVE'
        }
    )
    print(f"Course 2: {course2}")
    
    # Create faculty
    faculty, created = Faculty.objects.get_or_create(
        employee_id="F001",
        defaults={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@university.edu',
            'department': department
        }
    )
    print(f"Faculty: {faculty}")
    
    # Create course sections
    section1, created = CourseSection.objects.get_or_create(
        course=course1,
        section_number="A",
        academic_year="2024-2025",
        semester="Fall",
        defaults={
            'section_type': 'LECTURE',
            'faculty': faculty,
            'max_students': 50,
            'is_active': True
        }
    )
    print(f"Course Section 1: {section1}")
    
    section2, created = CourseSection.objects.get_or_create(
        course=course2,
        section_number="A",
        academic_year="2024-2025",
        semester="Fall",
        defaults={
            'section_type': 'LECTURE',
            'faculty': faculty,
            'max_students': 50,
            'is_active': True
        }
    )
    print(f"Course Section 2: {section2}")
    
    return batch, course1, course2, section1, section2

def create_sample_students(batch, count=5):
    """Create sample students for the batch"""
    print(f"\nCreating {count} sample students...")
    
    students = []
    for i in range(1, count + 1):
        student, created = Student.objects.get_or_create(
            roll_number=f"CS2024{i:03d}",
            defaults={
                'first_name': f'Student{i}',
                'last_name': 'Test',
                'date_of_birth': '2000-01-01',
                'gender': 'M',
                'student_batch': batch,
                'status': 'ACTIVE',
                'email': f'student{i}@test.com'
            }
        )
        students.append(student)
        print(f"Created student: {student}")
    
    return students

def demonstrate_batch_enrollment():
    """Demonstrate batch enrollment functionality"""
    print("\n" + "="*50)
    print("BATCH ENROLLMENT DEMONSTRATION")
    print("="*50)
    
    # Create example data
    batch, course1, course2, section1, section2 = create_example_data()
    
    # Create sample students
    students = create_sample_students(batch, 5)
    
    print(f"\nBatch has {batch.current_count} students")
    
    # Create batch enrollment for course 1
    print(f"\n1. Creating batch enrollment for {course1.code}...")
    batch_enrollment1 = BatchCourseEnrollment.objects.create(
        student_batch=batch,
        course=course1,
        course_section=section1,
        academic_year="2024-2025",
        semester="Fall",
        auto_enroll_new_students=True,
        status='ACTIVE'
    )
    print(f"Created batch enrollment: {batch_enrollment1}")
    
    # Check enrollment results
    print(f"\n2. Checking enrollment results...")
    print(f"Enrolled students count: {batch_enrollment1.get_enrolled_students_count()}")
    print(f"Batch students count: {batch_enrollment1.get_batch_students_count()}")
    print(f"Enrollment percentage: {batch_enrollment1.get_enrollment_percentage()}%")
    
    # Create batch enrollment for course 2
    print(f"\n3. Creating batch enrollment for {course2.code}...")
    batch_enrollment2 = BatchCourseEnrollment.objects.create(
        student_batch=batch,
        course=course2,
        course_section=section2,
        academic_year="2024-2025",
        semester="Fall",
        auto_enroll_new_students=True,
        status='ACTIVE'
    )
    print(f"Created batch enrollment: {batch_enrollment2}")
    
    # Demonstrate prerequisite creation
    print(f"\n4. Creating prerequisite: {course2.code} requires {course1.code}...")
    prerequisite = CoursePrerequisite.objects.create(
        course=course2,
        prerequisite_course=course1,
        student_batch=batch,
        is_mandatory=True,
        minimum_grade='C'
    )
    print(f"Created prerequisite: {prerequisite}")
    
    # Check prerequisites
    print(f"\n5. Checking prerequisites for {course2.code}...")
    prerequisites = CoursePrerequisite.objects.filter(
        course=course2,
        student_batch=batch
    )
    
    for prereq in prerequisites:
        print(f"Prerequisite: {prereq.prerequisite_course.code} (Mandatory: {prereq.is_mandatory})")
    
    # Demonstrate manual enrollment
    print(f"\n6. Demonstrating manual enrollment...")
    result = batch_enrollment1.enroll_batch_students()
    print(f"Manual enrollment result: {result}")
    
    # Show all batch enrollments
    print(f"\n7. All batch enrollments for batch {batch.batch_name}:")
    enrollments = BatchCourseEnrollment.objects.filter(student_batch=batch)
    for enrollment in enrollments:
        print(f"  - {enrollment.course.code}: {enrollment.status} "
              f"({enrollment.get_enrollment_percentage()}% enrolled)")
    
    print(f"\n8. Summary:")
    print(f"   - Batch: {batch.batch_name}")
    print(f"   - Students: {batch.current_count}")
    print(f"   - Courses enrolled: {enrollments.count()}")
    print(f"   - Prerequisites defined: {CoursePrerequisite.objects.filter(student_batch=batch).count()}")

def demonstrate_bulk_operations():
    """Demonstrate bulk enrollment operations"""
    print("\n" + "="*50)
    print("BULK OPERATIONS DEMONSTRATION")
    print("="*50)
    
    # Get existing data
    batch = StudentBatch.objects.filter(batch_code="CS-2024-1-A").first()
    if not batch:
        print("No batch found. Run demonstrate_batch_enrollment() first.")
        return
    
    courses = Course.objects.filter(code__in=['CS101', 'CS102'])
    
    print(f"Creating bulk enrollments for batch {batch.batch_name}...")
    
    # Create multiple batch enrollments
    enrollments_created = 0
    for course in courses:
        enrollment, created = BatchCourseEnrollment.objects.get_or_create(
            student_batch=batch,
            course=course,
            academic_year="2024-2025",
            semester="Spring",
            defaults={
                'auto_enroll_new_students': True,
                'status': 'ACTIVE'
            }
        )
        if created:
            enrollments_created += 1
            print(f"Created enrollment: {enrollment}")
    
    print(f"\nCreated {enrollments_created} new batch enrollments")
    
    # Show statistics
    total_enrollments = BatchCourseEnrollment.objects.filter(student_batch=batch).count()
    active_enrollments = BatchCourseEnrollment.objects.filter(
        student_batch=batch, 
        status='ACTIVE'
    ).count()
    
    print(f"Total batch enrollments: {total_enrollments}")
    print(f"Active batch enrollments: {active_enrollments}")

if __name__ == "__main__":
    print("Batch Course Enrollment System Demo")
    print("===================================")
    
    # Run demonstrations
    demonstrate_batch_enrollment()
    demonstrate_bulk_operations()
    
    print("\n" + "="*50)
    print("DEMO COMPLETED")
    print("="*50)
    print("\nTo explore the system further:")
    print("1. Check the Django admin interface at /admin/academics/")
    print("2. Use the API endpoints at /academics/api/batch-enrollments/")
    print("3. Review the documentation in BATCH_ENROLLMENT_SYSTEM.md")
