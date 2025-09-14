from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    EnrollmentRule, CourseAssignment, FacultyAssignment, StudentEnrollmentPlan,
    PlannedCourse, EnrollmentRequest, WaitlistEntry
)
from academics.models import Course, CourseSection, CourseEnrollment
from faculty.models import Faculty
from students.models import Student
from django.db import models


class EnrollmentService:
    """Service class for handling enrollment operations"""
    
    @staticmethod
    def create_department_based_enrollment_plan(student, academic_year, semester):
        """
        Create enrollment plan based on student's department and program
        """
        try:
            # Get student's department and program
            student_department = student.department_ref if hasattr(student, 'department_ref') else None
            if not student_department:
                raise ValidationError("Student must have a department assigned")
            
            # Get student's academic program
            student_program = student.academic_program if hasattr(student, 'academic_program') else None
            if not student_program:
                raise ValidationError("Student must have an academic program assigned")
            
            # Check if plan already exists
            existing_plan = StudentEnrollmentPlan.objects.filter(
                student=student,
                academic_year=academic_year,
                semester=semester
            ).first()
            
            if existing_plan:
                return existing_plan
            
            # Create new enrollment plan
            with transaction.atomic():
                plan = StudentEnrollmentPlan.objects.create(
                    student=student,
                    academic_program=student_program,
                    academic_year=academic_year,
                    semester=semester,
                    year_of_study=student.grade_level if hasattr(student, 'grade_level') else 1,
                    status='DRAFT'
                )
                
                # Get mandatory courses for the student's department and program
                mandatory_courses = CourseAssignment.objects.filter(
                    department=student_department,
                    academic_program=student_program,
                    academic_year=academic_year,
                    semester=semester,
                    assignment_type='MANDATORY',
                    is_active=True
                ).select_related('course')
                
                # Add mandatory courses to the plan
                for assignment in mandatory_courses:
                    PlannedCourse.objects.create(
                        enrollment_plan=plan,
                        course=assignment.course,
                        priority=1,
                        is_mandatory=True
                    )
                
                # Get elective courses
                elective_courses = CourseAssignment.objects.filter(
                    department=student_department,
                    academic_program=student_program,
                    academic_year=academic_year,
                    semester=semester,
                    assignment_type='ELECTIVE',
                    is_active=True
                ).select_related('course')
                
                # Add elective courses to the plan
                for assignment in elective_courses:
                    PlannedCourse.objects.create(
                        enrollment_plan=plan,
                        course=assignment.course,
                        priority=2,
                        is_mandatory=False
                    )
                
                return plan
                
        except Exception as e:
            raise ValidationError(f"Error creating enrollment plan: {str(e)}")
    
    @staticmethod
    def assign_faculty_to_course_section(faculty, course_section, workload_hours=3, is_primary=True):
        """
        Assign faculty to a course section
        """
        try:
            # Validate faculty assignment
            if faculty.department_ref != course_section.course.department:
                raise ValidationError("Faculty must belong to the same department as the course")
            
            # Check for conflicting assignments
            if is_primary:
                conflicting_assignments = FacultyAssignment.objects.filter(
                    faculty=faculty,
                    course_section__timetables__is_active=True,
                    status__in=['ASSIGNED', 'CONFIRMED']
                ).exclude(course_section=course_section)
                
                for assignment in conflicting_assignments:
                    for timetable1 in course_section.timetables.filter(is_active=True):
                        for timetable2 in assignment.course_section.timetables.filter(is_active=True):
                            if (timetable1.day_of_week == timetable2.day_of_week and
                                timetable1.start_time < timetable2.end_time and
                                timetable1.end_time > timetable2.start_time):
                                raise ValidationError(f"Faculty has conflicting schedule with {assignment.course_section}")
            
            # Create or update faculty assignment
            assignment, created = FacultyAssignment.objects.get_or_create(
                faculty=faculty,
                course_section=course_section,
                defaults={
                    'status': 'ASSIGNED',
                    'workload_hours': workload_hours,
                    'is_primary': is_primary
                }
            )
            
            if not created:
                assignment.status = 'ASSIGNED'
                assignment.workload_hours = workload_hours
                assignment.is_primary = is_primary
                assignment.save()
            
            return assignment
            
        except Exception as e:
            raise ValidationError(f"Error assigning faculty: {str(e)}")
    
    @staticmethod
    def create_course_section(course, section_number, academic_year, semester, faculty, max_students=50):
        """
        Create a new course section
        """
        try:
            with transaction.atomic():
                # Create course section
                section = CourseSection.objects.create(
                    course=course,
                    section_number=section_number,
                    academic_year=academic_year,
                    semester=semester,
                    faculty=faculty,
                    max_students=max_students,
                    current_enrollment=0
                )
                
                # Assign faculty to the section
                EnrollmentService.assign_faculty_to_course_section(
                    faculty=faculty,
                    course_section=section,
                    workload_hours=3,
                    is_primary=True
                )
                
                return section
                
        except Exception as e:
            raise ValidationError(f"Error creating course section: {str(e)}")
    
    @staticmethod
    def enroll_student_in_course(student, course_section, enrollment_type='REGULAR'):
        """
        Enroll a student in a course section
        """
        try:
            with transaction.atomic():
                # Check if student can enroll
                if not course_section.can_enroll_student():
                    # Add to waitlist
                    return EnrollmentService.add_to_waitlist(student, course_section)
                
                # Check if student is already enrolled
                existing_enrollment = CourseEnrollment.objects.filter(
                    student=student,
                    course_section=course_section
                ).first()
                
                if existing_enrollment:
                    if existing_enrollment.status == 'ENROLLED':
                        raise ValidationError("Student is already enrolled in this course section")
                    elif existing_enrollment.status in ['DROPPED', 'WITHDRAWN']:
                        # Reactivate enrollment
                        existing_enrollment.status = 'ENROLLED'
                        existing_enrollment.save()
                        return existing_enrollment
                
                # Create enrollment
                enrollment = CourseEnrollment.objects.create(
                    student=student,
                    course_section=course_section,
                    status='ENROLLED',
                    enrollment_type=enrollment_type
                )
                
                # Update section enrollment count
                course_section.current_enrollment += 1
                course_section.save()
                
                return enrollment
                
        except Exception as e:
            raise ValidationError(f"Error enrolling student: {str(e)}")
    
    @staticmethod
    def add_to_waitlist(student, course_section):
        """
        Add student to course section waitlist
        """
        try:
            # Check if student is already on waitlist
            existing_waitlist = WaitlistEntry.objects.filter(
                student=student,
                course_section=course_section,
                is_active=True
            ).first()
            
            if existing_waitlist:
                raise ValidationError("Student is already on the waitlist for this course section")
            
            # Get next position in waitlist
            last_position = WaitlistEntry.objects.filter(
                course_section=course_section,
                is_active=True
            ).aggregate(models.Max('position'))['position__max'] or 0
            
            # Create enrollment request
            enrollment_plan = StudentEnrollmentPlan.objects.filter(
                student=student,
                academic_year=course_section.academic_year,
                semester=course_section.semester
            ).first()
            
            if not enrollment_plan:
                enrollment_plan = EnrollmentService.create_department_based_enrollment_plan(
                    student, course_section.academic_year, course_section.semester
                )
            
            enrollment_request = EnrollmentRequest.objects.create(
                student=student,
                course_section=course_section,
                enrollment_plan=enrollment_plan,
                status='PENDING',
                requested_by=student.user if hasattr(student, 'user') else None
            )
            
            # Add to waitlist
            waitlist_entry = WaitlistEntry.objects.create(
                student=student,
                course_section=course_section,
                enrollment_request=enrollment_request,
                position=last_position + 1
            )
            
            return waitlist_entry
            
        except Exception as e:
            raise ValidationError(f"Error adding to waitlist: {str(e)}")
    
    @staticmethod
    def process_waitlist_for_course_section(course_section):
        """
        Process waitlist when space becomes available in a course section
        """
        try:
            with transaction.atomic():
                # Get first person on waitlist
                first_waitlist_entry = WaitlistEntry.objects.filter(
                    course_section=course_section,
                    is_active=True
                ).order_by('position').first()
                
                if not first_waitlist_entry:
                    return None
                
                # Try to move to enrollment
                if first_waitlist_entry.move_to_enrollment():
                    return first_waitlist_entry
                
                return None
                
        except Exception as e:
            raise ValidationError(f"Error processing waitlist: {str(e)}")
    
    @staticmethod
    def get_available_courses_for_student(student, academic_year, semester):
        """
        Get available courses for a student based on their department and program
        """
        try:
            student_department = student.department_ref if hasattr(student, 'department_ref') else None
            student_program = student.academic_program if hasattr(student, 'academic_program') else None
            
            if not student_department or not student_program:
                raise ValidationError("Student must have department and program assigned")
            
            # Get course assignments
            course_assignments = CourseAssignment.objects.filter(
                department=student_department,
                academic_program=student_program,
                academic_year=academic_year,
                semester=semester,
                is_active=True
            ).select_related('course', 'department', 'academic_program')
            
            available_courses = []
            for assignment in course_assignments:
                # Get available sections
                available_sections = CourseSection.objects.filter(
                    course=assignment.course,
                    academic_year=academic_year,
                    semester=semester,
                    is_active=True
                ).filter(
                    current_enrollment__lt=models.F('max_students')
                )
                
                if available_sections.exists():
                    available_courses.append({
                        'assignment': assignment,
                        'course': assignment.course,
                        'available_sections': available_sections,
                        'total_sections': assignment.course.sections.filter(
                            academic_year=academic_year,
                            semester=semester
                        ).count()
                    })
            
            return available_courses
            
        except Exception as e:
            raise ValidationError(f"Error getting available courses: {str(e)}")
    
    @staticmethod
    def get_student_enrollment_summary(student, academic_year, semester):
        """
        Get comprehensive enrollment summary for a student
        """
        try:
            # Get enrollment plan
            enrollment_plan = StudentEnrollmentPlan.objects.filter(
                student=student,
                academic_year=academic_year,
                semester=semester
            ).first()
            
            # Get current enrollments
            current_enrollments = CourseEnrollment.objects.filter(
                student=student,
                course_section__academic_year=academic_year,
                course_section__semester=semester
            ).select_related('course_section__course', 'course_section__faculty')
            
            # Get pending requests
            pending_requests = EnrollmentRequest.objects.filter(
                student=student,
                course_section__academic_year=academic_year,
                course_section__semester=semester,
                status='PENDING'
            ).select_related('course_section__course')
            
            # Get waitlist entries
            waitlist_entries = WaitlistEntry.objects.filter(
                student=student,
                course_section__academic_year=academic_year,
                course_section__semester=semester,
                is_active=True
            ).select_related('course_section__course')
            
            return {
                'enrollment_plan': enrollment_plan,
                'current_enrollments': current_enrollments,
                'pending_requests': pending_requests,
                'waitlist_entries': waitlist_entries,
                'total_credits': sum(enrollment.course.credits for enrollment in current_enrollments if enrollment.status == 'ENROLLED'),
                'total_courses': current_enrollments.filter(status='ENROLLED').count()
            }
            
        except Exception as e:
            raise ValidationError(f"Error getting enrollment summary: {str(e)}")


class DepartmentEnrollmentService:
    """Service for department-wide enrollment operations"""
    
    @staticmethod
    def create_department_course_sections(department, academic_year, semester):
        """
        Create course sections for all courses in a department
        """
        try:
            with transaction.atomic():
                courses = Course.objects.filter(department=department, status='ACTIVE')
                created_sections = []
                
                for course in courses:
                    # Get course assignments
                    assignments = CourseAssignment.objects.filter(
                        course=course,
                        department=department,
                        academic_year=academic_year,
                        semester=semester,
                        is_active=True
                    )
                    
                    for assignment in assignments:
                        # Create sections based on demand
                        sections_needed = max(1, assignment.course.max_students // 50)
                        
                        for i in range(sections_needed):
                            section_number = chr(65 + i) if i < 26 else str(i + 1)  # A, B, C... or 1, 2, 3...
                            
                            # Find available faculty
                            available_faculty = Faculty.objects.filter(
                                department_ref=department,
                                status='ACTIVE',
                                currently_associated=True
                            ).first()
                            
                            if available_faculty:
                                section = EnrollmentService.create_course_section(
                                    course=course,
                                    section_number=section_number,
                                    academic_year=academic_year,
                                    semester=semester,
                                    faculty=available_faculty,
                                    max_students=50
                                )
                                created_sections.append(section)
                
                return created_sections
                
        except Exception as e:
            raise ValidationError(f"Error creating department course sections: {str(e)}")
    
    @staticmethod
    def assign_faculty_to_department_courses(department, academic_year, semester):
        """
        Automatically assign faculty to course sections in a department
        """
        try:
            with transaction.atomic():
                # Get all course sections without faculty assignments
                unassigned_sections = CourseSection.objects.filter(
                    course__department=department,
                    academic_year=academic_year,
                    semester=semester,
                    is_active=True
                ).exclude(
                    faculty_assignments__status__in=['ASSIGNED', 'CONFIRMED']
                )
                
                # Get available faculty
                available_faculty = Faculty.objects.filter(
                    department_ref=department,
                    status='ACTIVE',
                    currently_associated=True
                )
                
                if not available_faculty.exists():
                    raise ValidationError("No available faculty in the department")
                
                faculty_list = list(available_faculty)
                faculty_index = 0
                
                for section in unassigned_sections:
                    # Assign faculty in round-robin fashion
                    faculty = faculty_list[faculty_index % len(faculty_list)]
                    
                    EnrollmentService.assign_faculty_to_course_section(
                        faculty=faculty,
                        course_section=section,
                        workload_hours=3,
                        is_primary=True
                    )
                    
                    faculty_index += 1
                
                return unassigned_sections.count()
                
        except Exception as e:
            raise ValidationError(f"Error assigning faculty: {str(e)}")
