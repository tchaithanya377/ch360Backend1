from django.db import models
from django.conf import settings
from departments.models import Department
from academics.models import AcademicProgram, Course, CourseSection
from faculty.models import Faculty
from students.models import Student
from django.core.exceptions import ValidationError
from django.utils import timezone


class EnrollmentRule(models.Model):
    """Model for defining enrollment rules and constraints"""
    RULE_TYPES = [
        ('DEPARTMENT', 'Department Based'),
        ('PROGRAM', 'Program Based'),
        ('YEAR', 'Year Based'),
        ('SECTION', 'Section Based'),
        ('FACULTY', 'Faculty Based'),
        ('PREREQUISITE', 'Prerequisite Based'),
        ('CAPACITY', 'Capacity Based'),
    ]
    
    name = models.CharField(max_length=200, help_text="Rule name")
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='enrollment_rules')
    academic_program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, null=True, blank=True, related_name='enrollment_rules')
    academic_year = models.CharField(max_length=9, help_text="Academic year this rule applies to")
    semester = models.CharField(max_length=20, help_text="Semester this rule applies to")
    is_active = models.BooleanField(default=True)
    description = models.TextField(help_text="Rule description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['academic_year', 'semester', 'rule_type']
        verbose_name = "Enrollment Rule"
        verbose_name_plural = "Enrollment Rules"
    
    def __str__(self):
        return f"{self.name} - {self.rule_type} ({self.academic_year} {self.semester})"


class CourseAssignment(models.Model):
    """Model for assigning courses to departments, programs, and faculty"""
    ASSIGNMENT_TYPES = [
        ('MANDATORY', 'Mandatory'),
        ('ELECTIVE', 'Elective'),
        ('OPTIONAL', 'Optional'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='course_assignments')
    academic_program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='course_assignments')
    academic_year = models.CharField(max_length=9, help_text="Academic year")
    semester = models.CharField(max_length=20, help_text="Semester")
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='MANDATORY')
    year_of_study = models.PositiveIntegerField(help_text="Year in the program when this course is taken")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'department', 'academic_program', 'academic_year', 'semester']
        ordering = ['academic_year', 'semester', 'year_of_study', 'course__code']
        verbose_name = "Course Assignment"
        verbose_name_plural = "Course Assignments"
    
    def __str__(self):
        return f"{self.course.code} - {self.department.code} - {self.academic_program.code} ({self.academic_year} {self.semester})"


class FacultyAssignment(models.Model):
    """Model for assigning faculty to course sections"""
    ASSIGNMENT_STATUS = [
        ('ASSIGNED', 'Assigned'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='faculty_assignments')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='faculty_assignments')
    assignment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS, default='ASSIGNED')
    workload_hours = models.PositiveIntegerField(help_text="Weekly workload in hours")
    is_primary = models.BooleanField(default=True, help_text="Whether this is the primary faculty for the section")
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['faculty', 'course_section']
        ordering = ['-assignment_date', 'faculty__first_name']
        verbose_name = "Faculty Assignment"
        verbose_name_plural = "Faculty Assignments"
    
    def __str__(self):
        return f"{self.faculty.first_name} {self.faculty.last_name} - {self.course_section}"
    
    def clean(self):
        """Validate faculty assignment"""
        if self.faculty.department_ref != self.course_section.course.department:
            raise ValidationError("Faculty must belong to the same department as the course")
        
        # Check if faculty is already assigned to conflicting time slots
        if self.is_primary:
            conflicting_assignments = FacultyAssignment.objects.filter(
                faculty=self.faculty,
                course_section__timetables__is_active=True,
                status__in=['ASSIGNED', 'CONFIRMED']
            ).exclude(pk=self.pk)
            
            for assignment in conflicting_assignments:
                for timetable1 in self.course_section.timetables.filter(is_active=True):
                    for timetable2 in assignment.course_section.timetables.filter(is_active=True):
                        if (timetable1.day_of_week == timetable2.day_of_week and
                            timetable1.start_time < timetable2.end_time and
                            timetable1.end_time > timetable2.start_time):
                            raise ValidationError(f"Faculty has conflicting schedule with {assignment.course_section}")


class StudentEnrollmentPlan(models.Model):
    """Model for planning student enrollments based on department and program"""
    PLAN_STATUS = [
        ('DRAFT', 'Draft'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollment_plans')
    academic_program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE, related_name='student_enrollment_plans')
    academic_year = models.CharField(max_length=9, help_text="Academic year")
    semester = models.CharField(max_length=20, help_text="Semester")
    year_of_study = models.PositiveIntegerField(help_text="Current year in the program")
    status = models.CharField(max_length=20, choices=PLAN_STATUS, default='DRAFT')
    total_credits = models.PositiveIntegerField(default=0, help_text="Total credits for this semester")
    advisor = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='advised_enrollment_plans')
    notes = models.TextField(blank=True, help_text="Advisor notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'academic_year', 'semester']
        ordering = ['-academic_year', '-semester', 'student__roll_number']
        verbose_name = "Student Enrollment Plan"
        verbose_name_plural = "Student Enrollment Plans"
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.academic_program.code} ({self.academic_year} {self.semester})"
    
    def get_planned_courses(self):
        """Get courses planned for enrollment"""
        return self.planned_courses.all()
    
    def get_total_planned_credits(self):
        """Calculate total planned credits"""
        return sum(course.course.credits for course in self.planned_courses.all())


class PlannedCourse(models.Model):
    """Model for courses planned in student enrollment plan"""
    enrollment_plan = models.ForeignKey(StudentEnrollmentPlan, on_delete=models.CASCADE, related_name='planned_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='planned_enrollments')
    priority = models.PositiveIntegerField(default=1, help_text="Priority for enrollment (1=highest)")
    is_mandatory = models.BooleanField(default=True, help_text="Whether this course is mandatory")
    notes = models.TextField(blank=True, help_text="Student or advisor notes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['enrollment_plan', 'course']
        ordering = ['priority', 'course__code']
        verbose_name = "Planned Course"
        verbose_name_plural = "Planned Courses"
    
    def __str__(self):
        return f"{self.course.code} - Priority {self.priority}"


class EnrollmentRequest(models.Model):
    """Model for handling enrollment requests and approvals"""
    REQUEST_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollment_requests')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='enrollment_requests')
    enrollment_plan = models.ForeignKey(StudentEnrollmentPlan, on_delete=models.CASCADE, related_name='enrollment_requests')
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='PENDING')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_enrollment_requests')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_enrollment_requests')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection if applicable")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    class Meta:
        unique_together = ['student', 'course_section']
        ordering = ['-request_date']
        verbose_name = "Enrollment Request"
        verbose_name_plural = "Enrollment Requests"
        indexes = [
            models.Index(fields=['course_section', 'status'], name='idx_enrollreq_section_status'),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section} ({self.status})"
    
    def approve(self, approved_by_user):
        """Approve the enrollment request"""
        if self.status != 'PENDING':
            raise ValidationError("Only pending requests can be approved")
        
        self.status = 'APPROVED'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
        
        # Create actual enrollment
        from academics.models import CourseEnrollment
        CourseEnrollment.objects.create(
            student=self.student,
            course_section=self.course_section,
            status='ENROLLED',
            enrollment_type='REGULAR'
        )
    
    def reject(self, rejected_by_user, reason):
        """Reject the enrollment request"""
        if self.status != 'PENDING':
            raise ValidationError("Only pending requests can be rejected")
        
        self.status = 'REJECTED'
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class WaitlistEntry(models.Model):
    """Model for managing waitlist when courses are full"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='waitlist_entries')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='waitlist_entries')
    enrollment_request = models.ForeignKey(EnrollmentRequest, on_delete=models.CASCADE, related_name='waitlist_entry')
    position = models.PositiveIntegerField(help_text="Position in waitlist")
    added_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['student', 'course_section']
        ordering = ['position', 'added_date']
        verbose_name = "Waitlist Entry"
        verbose_name_plural = "Waitlist Entries"
        indexes = [
            models.Index(fields=['course_section', 'position'], name='idx_waitlist_section_position'),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section} (Position {self.position})"
    
    def move_to_enrollment(self):
        """Move student from waitlist to enrollment when space becomes available"""
        if self.position == 1:  # First in waitlist
            # Check if course section has available space
            if self.course_section.can_enroll_student():
                # Create enrollment
                from academics.models import CourseEnrollment
                CourseEnrollment.objects.create(
                    student=self.student,
                    course_section=self.course_section,
                    status='ENROLLED',
                    enrollment_type='REGULAR'
                )
                
                # Update enrollment request
                self.enrollment_request.status = 'APPROVED'
                self.enrollment_request.approved_at = timezone.now()
                self.enrollment_request.save()
                
                # Remove from waitlist
                self.is_active = False
                self.save()
                
                # Move next person up in waitlist
                next_entry = WaitlistEntry.objects.filter(
                    course_section=self.course_section,
                    is_active=True,
                    position__gt=self.position
                ).order_by('position').first()
                
                if next_entry:
                    next_entry.position = 1
                    next_entry.save()
                
                return True
        return False
