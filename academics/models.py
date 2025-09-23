from django.db import models
from django.db import transaction
from django.db.models import F, Q, CheckConstraint, Index
from django.conf import settings
from faculty.models import Faculty
from students.models import Student


"""Deprecated local Department model removed in favor of departments.Department."""


class AcademicProgram(models.Model):
    """Model for academic programs/degrees"""
    PROGRAM_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('ARCHIVED', 'Archived'),
    ]
    PROGRAM_LEVELS = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('PHD', 'Doctorate'),
        ('DIPLOMA', 'Diploma'),
        ('CERTIFICATE', 'Certificate'),
    ]
    
    name = models.CharField(max_length=200, help_text="Program name (e.g., Bachelor of Computer Science)")
    code = models.CharField(max_length=20, unique=True, help_text="Program code (e.g., BCS)")
    level = models.CharField(max_length=20, choices=PROGRAM_LEVELS, default='UG')
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE, related_name='academic_programs')
    duration_years = models.PositiveIntegerField(default=4, help_text="Program duration in years")
    total_credits = models.PositiveIntegerField(help_text="Total credits required for graduation")
    description = models.TextField(blank=True, help_text="Program description")
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=PROGRAM_STATUS, default='ACTIVE', db_default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level', 'name']
        verbose_name = "Academic Program"
        verbose_name_plural = "Academic Programs"
    
    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        # Ensure status is always set to a valid value
        if not self.status:
            self.status = 'ACTIVE'
        super().save(*args, **kwargs)


class Course(models.Model):
    """Model for academic courses"""
    COURSE_LEVELS = [
        ('UG', 'Undergraduate'),
        ('PG', 'Postgraduate'),
        ('PHD', 'Doctorate'),
        ('DIPLOMA', 'Diploma'),
        ('CERTIFICATE', 'Certificate'),
    ]
    
    COURSE_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('DRAFT', 'Draft'),
        ('ARCHIVED', 'Archived'),
    ]
    
    code = models.CharField(max_length=20, unique=True, help_text="Course code (e.g., CS101)")
    title = models.CharField(max_length=200, help_text="Course title")
    description = models.TextField(help_text="Course description")
    level = models.CharField(max_length=20, choices=COURSE_LEVELS, default='UG')
    credits = models.PositiveIntegerField(default=3, help_text="Credit hours")
    duration_weeks = models.PositiveIntegerField(default=16, help_text="Duration in weeks")
    max_students = models.PositiveIntegerField(default=50, help_text="Maximum number of students per section")
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, help_text="Prerequisite courses")
    department = models.ForeignKey('departments.Department', on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    programs = models.ManyToManyField(AcademicProgram, related_name='courses', help_text="Programs this course belongs to")
    status = models.CharField(max_length=20, choices=COURSE_STATUS, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code', 'title']
        verbose_name = "Course"
        verbose_name_plural = "Courses"
    
    def __str__(self):
        return f"{self.code} - {self.title}"
    
    def get_enrolled_students_count(self):
        return sum(section.get_enrolled_students_count() for section in self.sections.all())
    
    def get_total_sections(self):
        return self.sections.count()


class CourseSection(models.Model):
    """Model for course sections (multiple sections of the same course)"""
    SECTION_TYPES = [
        ('LECTURE', 'Lecture'),
        ('LAB', 'Laboratory'),
        ('TUTORIAL', 'Tutorial'),
        ('SEMINAR', 'Seminar'),
        ('WORKSHOP', 'Workshop'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    student_batch = models.ForeignKey(
        'students.StudentBatch', 
        on_delete=models.CASCADE, 
        related_name='course_sections',
        null=True,
        blank=True,
        help_text="Student batch assigned to this section"
    )
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES, default='LECTURE')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='course_sections')
    max_students = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Maximum students for this section (optional)"
    )
    current_enrollment = models.PositiveIntegerField(
        default=0, 
        help_text="Current number of enrolled students (optional)"
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'student_batch']
        ordering = ['course__code', 'student_batch__batch_name']
        verbose_name = "Course Section"
        verbose_name_plural = "Course Sections"
        constraints = [
            CheckConstraint(check=Q(current_enrollment__gte=0), name='course_section_current_enrollment_nonnegative'),
        ]
        indexes = [
            Index(fields=['faculty']),
            Index(fields=['is_active']),
            Index(fields=['course', 'student_batch'], name='idx_section_course_batch'),
            Index(fields=['student_batch'], name='idx_section_student_batch'),
        ]
    
    def __str__(self):
        if self.student_batch:
            return f"{self.course.code} - {self.student_batch.batch_name}"
        else:
            return f"{self.course.code} - No Batch Assigned"
    
    @property
    def section_number(self):
        """Get section number from student batch"""
        return self.student_batch.section if self.student_batch else None
    
    @property
    def academic_year(self):
        """Get academic year from student batch"""
        return self.student_batch.academic_year.year if self.student_batch and self.student_batch.academic_year else None
    
    @property
    def semester(self):
        """Get semester from student batch"""
        return self.student_batch.semester if self.student_batch else None
    
    def get_enrolled_students_count(self):
        return self.enrollments.filter(status='ENROLLED').count()
    
    def get_available_seats(self):
        if self.max_students is None:
            return None
        return self.max_students - self.current_enrollment
    
    def is_full(self):
        if self.max_students is None:
            return False
        return self.current_enrollment >= self.max_students
    
    def can_enroll_student(self):
        return self.is_active and not self.is_full()


class Syllabus(models.Model):
    """Model for course syllabuses"""
    SYLLABUS_STATUS = [
        ('DRAFT', 'Draft'),
        ('REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
    ]
    
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='syllabus')
    version = models.CharField(max_length=20, default='1.0', help_text="Syllabus version")
    academic_year = models.CharField(max_length=9, help_text="Academic year (e.g., 2024-2025)")
    semester = models.CharField(max_length=20, help_text="Semester (e.g., Fall, Spring)")
    learning_objectives = models.TextField(help_text="Course learning objectives")
    course_outline = models.TextField(help_text="Detailed course outline")
    assessment_methods = models.TextField(help_text="Assessment and evaluation methods")
    grading_policy = models.TextField(help_text="Grading policy and criteria")
    textbooks = models.TextField(help_text="Required and recommended textbooks")
    additional_resources = models.TextField(blank=True, help_text="Additional learning resources")
    status = models.CharField(max_length=20, choices=SYLLABUS_STATUS, default='DRAFT')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_syllabi')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-academic_year', '-semester', 'course__code']
        verbose_name = "Syllabus"
        verbose_name_plural = "Syllabi"
    
    def __str__(self):
        return f"{self.course.code} Syllabus - {self.academic_year} {self.semester}"


class SyllabusTopic(models.Model):
    """Model for individual topics within a syllabus"""
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='topics')
    week_number = models.PositiveIntegerField(help_text="Week number in the semester")
    title = models.CharField(max_length=200, help_text="Topic title")
    description = models.TextField(help_text="Topic description")
    learning_outcomes = models.TextField(help_text="Specific learning outcomes for this topic")
    readings = models.TextField(blank=True, help_text="Required readings for this topic")
    activities = models.TextField(blank=True, help_text="Learning activities and assignments")
    duration_hours = models.PositiveIntegerField(default=3, help_text="Duration in hours")
    order = models.PositiveIntegerField(default=0, help_text="Order within the week")
    
    class Meta:
        ordering = ['week_number', 'order']
        unique_together = ['syllabus', 'week_number', 'order']
    
    def __str__(self):
        return f"Week {self.week_number}: {self.title}"


class Timetable(models.Model):
    """Model for class timetables"""
    TIMETABLE_TYPE = [
        ('REGULAR', 'Regular Schedule'),
        ('EXAM', 'Examination Schedule'),
        ('MAKEUP', 'Make-up Classes'),
        ('SPECIAL', 'Special Events'),
    ]
    
    DAYS_OF_WEEK = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='timetables', null=True, blank=True)
    timetable_type = models.CharField(max_length=20, choices=TIMETABLE_TYPE, default='REGULAR')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField(help_text="Class start time")
    end_time = models.TimeField(help_text="Class end time")
    room = models.CharField(max_length=50, help_text="Classroom or venue")
    is_active = models.BooleanField(default=True, help_text="Whether this timetable entry is active")
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['course_section', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.course_section} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def get_duration_minutes(self):
        """Calculate duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes


class CourseEnrollment(models.Model):
    """Enhanced model for student course enrollments"""
    ENROLLMENT_STATUS = [
        ('ENROLLED', 'Enrolled'),
        ('DROPPED', 'Dropped'),
        ('COMPLETED', 'Completed'),
        ('WITHDRAWN', 'Withdrawn'),
        ('WAITLISTED', 'Waitlisted'),
        ('PENDING', 'Pending Approval'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='enrollments', null=True, blank=True)
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='ENROLLED')
    grade = models.CharField(max_length=5, blank=True, help_text="Final grade (e.g., A, B+, C)")
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Grade points")
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Attendance percentage")
    enrollment_type = models.CharField(max_length=20, choices=[
        ('REGULAR', 'Regular'),
        ('AUDIT', 'Audit'),
        ('CREDIT_TRANSFER', 'Credit Transfer'),
        ('REPEAT', 'Repeat Course'),
    ], default='REGULAR')
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course_section']
        ordering = ['-enrollment_date', 'course_section__course__code']
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"
        indexes = [
            Index(fields=['student', 'status']),
            Index(fields=['course_section', 'status']),
            Index(fields=['course_section'], name='idx_enroll_section_active', condition=Q(status='ENROLLED')),
        ]
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.course_section} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Override save to update section enrollment count using atomic F() updates"""
        with transaction.atomic():
            if self.pk is None:
                # New enrollment
                super().save(*args, **kwargs)
                if self.status == 'ENROLLED' and self.course_section_id:
                    CourseSection.objects.filter(pk=self.course_section_id).update(
                        current_enrollment=F('current_enrollment') + 1
                    )
            else:
                old_instance = CourseEnrollment.objects.select_for_update().get(pk=self.pk)
                status_changed = old_instance.status != self.status
                course_section_changed = old_instance.course_section_id != self.course_section_id
                super().save(*args, **kwargs)
                if status_changed or course_section_changed:
                    # Decrement from old if previously counted
                    if old_instance.status == 'ENROLLED' and old_instance.course_section_id:
                        CourseSection.objects.filter(pk=old_instance.course_section_id).update(
                            current_enrollment=F('current_enrollment') - 1
                        )
                    # Increment to new if now counted
                    if self.status == 'ENROLLED' and self.course_section_id:
                        CourseSection.objects.filter(pk=self.course_section_id).update(
                            current_enrollment=F('current_enrollment') + 1
                        )
    
    def delete(self, *args, **kwargs):
        """Override delete to update section enrollment count safely"""
        with transaction.atomic():
            if self.status == 'ENROLLED' and self.course_section_id:
                CourseSection.objects.filter(pk=self.course_section_id).update(
                    current_enrollment=F('current_enrollment') - 1
                )
            super().delete(*args, **kwargs)
    
    @property
    def course(self):
        return self.course_section.course
    
    @property
    def faculty(self):
        return self.course_section.faculty
    
    @property
    def academic_year(self):
        return self.student.student_batch.academic_year.year if self.student.student_batch and self.student.student_batch.academic_year else None
    
    @property
    def semester(self):
        return self.student.student_batch.semester if self.student.student_batch else None


class BatchCourseEnrollment(models.Model):
    """Model for batch-based course enrollments - links student batches to courses"""
    ENROLLMENT_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student_batch = models.ForeignKey(
        'students.StudentBatch', 
        on_delete=models.CASCADE, 
        related_name='batch_enrollments',
        help_text="Student batch to enroll"
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='batch_enrollments',
        help_text="Course to enroll the batch in"
    )
    course_section = models.ForeignKey(
        CourseSection, 
        on_delete=models.CASCADE, 
        related_name='batch_enrollments',
        null=True, 
        blank=True,
        help_text="Specific course section (optional)"
    )
    academic_year = models.CharField(max_length=9, help_text="Academic year for enrollment")
    semester = models.CharField(max_length=20, help_text="Semester for enrollment")
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='ACTIVE')
    auto_enroll_new_students = models.BooleanField(
        default=True, 
        help_text="Automatically enroll new students added to this batch"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_batch_enrollments'
    )
    
    class Meta:
        unique_together = ['student_batch', 'course', 'academic_year', 'semester']
        ordering = ['-enrollment_date', 'student_batch__batch_name', 'course__code']
        verbose_name = "Batch Course Enrollment"
        verbose_name_plural = "Batch Course Enrollments"
        indexes = [
            Index(fields=['student_batch', 'status']),
            Index(fields=['course', 'status']),
            Index(fields=['academic_year', 'semester', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student_batch.batch_name} → {self.course.code} ({self.academic_year} {self.semester})"
    
    def get_enrolled_students_count(self):
        """Get count of students actually enrolled from this batch"""
        return CourseEnrollment.objects.filter(
            student__student_batch=self.student_batch,
            course_section__course=self.course,
            status='ENROLLED'
        ).count()
    
    def get_batch_students_count(self):
        """Get total students in the batch"""
        return self.student_batch.current_count
    
    def get_enrollment_percentage(self):
        """Get percentage of batch students enrolled"""
        batch_count = self.get_batch_students_count()
        if batch_count == 0:
            return 0
        enrolled_count = self.get_enrolled_students_count()
        return round((enrolled_count / batch_count) * 100, 2)
    
    def enroll_batch_students(self, course_section=None):
        """Enroll all students from the batch into the course"""
        from django.db import transaction
        
        if not self.status == 'ACTIVE':
            return {'success': False, 'message': 'Batch enrollment is not active'}
        
        # Use provided course_section or find/create appropriate one
        if not course_section:
            course_section = self.course_section
        
        if not course_section:
            # Find or create a course section for this batch
            course_section = self._get_or_create_course_section()
        
        if not course_section:
            return {'success': False, 'message': 'No suitable course section found'}
        
        enrolled_count = 0
        errors = []
        
        with transaction.atomic():
            # Get all active students from the batch
            students = self.student_batch.students.filter(status='ACTIVE')
            
            for student in students:
                # Check if student is already enrolled
                existing_enrollment = CourseEnrollment.objects.filter(
                    student=student,
                    course_section=course_section
                ).first()
                
                if existing_enrollment:
                    if existing_enrollment.status != 'ENROLLED':
                        existing_enrollment.status = 'ENROLLED'
                        existing_enrollment.save()
                        enrolled_count += 1
                    continue
                
                # Create new enrollment
                try:
                    CourseEnrollment.objects.create(
                        student=student,
                        course_section=course_section,
                        status='ENROLLED',
                        enrollment_type='REGULAR'
                    )
                    enrolled_count += 1
                except Exception as e:
                    errors.append(f"Failed to enroll {student.roll_number}: {str(e)}")
        
        return {
            'success': True,
            'enrolled_count': enrolled_count,
            'total_students': students.count(),
            'errors': errors
        }
    
    def _get_or_create_course_section(self):
        """Get or create a course section suitable for this batch"""
        # Try to find existing section with capacity
        existing_section = CourseSection.objects.filter(
            course=self.course,
            student_batch=self.student_batch,
            is_active=True
        ).filter(
            models.Q(max_students__isnull=True) | 
            models.Q(current_enrollment__lt=models.F('max_students'))
        ).first()
        
        if existing_section:
            return existing_section
        
        # Create new section if none found
        # This would require faculty assignment - for now return None
        return None


class CoursePrerequisite(models.Model):
    """Model for course prerequisites with batch-specific rules"""
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='prerequisite_rules',
        help_text="Course that has prerequisites"
    )
    prerequisite_course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='required_for_courses',
        help_text="Prerequisite course"
    )
    student_batch = models.ForeignKey(
        'students.StudentBatch', 
        on_delete=models.CASCADE, 
        related_name='course_prerequisites',
        null=True, 
        blank=True,
        help_text="Specific batch (null means applies to all batches)"
    )
    is_mandatory = models.BooleanField(
        default=True, 
        help_text="Whether this prerequisite is mandatory"
    )
    minimum_grade = models.CharField(
        max_length=5, 
        blank=True, 
        help_text="Minimum grade required (e.g., C, B+)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['course', 'prerequisite_course', 'student_batch']
        verbose_name = "Course Prerequisite"
        verbose_name_plural = "Course Prerequisites"
    
    def __str__(self):
        batch_info = f" ({self.student_batch.batch_name})" if self.student_batch else ""
        return f"{self.course.code} requires {self.prerequisite_course.code}{batch_info}"


class AcademicTimetableSlot(models.Model):
    """Model for academic timetable slots linked to academic year and semester from students table"""
    
    SLOT_TYPES = [
        ('LECTURE', 'Lecture'),
        ('LAB', 'Laboratory'),
        ('TUTORIAL', 'Tutorial'),
        ('SEMINAR', 'Seminar'),
        ('WORKSHOP', 'Workshop'),
        ('EXAM', 'Examination'),
        ('BREAK', 'Break'),
        ('FREE', 'Free Period'),
    ]
    
    DAYS_OF_WEEK = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    
    # Link to academic year and semester from students table
    academic_year = models.ForeignKey(
        'students.AcademicYear',
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        help_text="Academic year from students table"
    )
    semester = models.ForeignKey(
        'students.Semester',
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        help_text="Semester from students table"
    )
    
    # Course and faculty information
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        null=True,
        blank=True,
        help_text="Course for this slot (optional)"
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        null=True,
        blank=True,
        help_text="Faculty member for this slot (optional)"
    )
    
    # Student batch information
    student_batch = models.ForeignKey(
        'students.StudentBatch',
        on_delete=models.CASCADE,
        related_name='timetable_slots',
        null=True,
        blank=True,
        help_text="Student batch for this slot (optional)"
    )
    
    # Slot details
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPES, default='LECTURE')
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField(help_text="Slot start time")
    end_time = models.TimeField(help_text="Slot end time")
    room = models.CharField(max_length=100, help_text="Room or venue")
    
    # Additional information
    subject = models.CharField(max_length=200, blank=True, help_text="Subject or topic")
    description = models.TextField(blank=True, help_text="Additional description")
    is_active = models.BooleanField(default=True, help_text="Whether this slot is active")
    is_recurring = models.BooleanField(default=True, help_text="Whether this slot repeats weekly")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_timetable_slots'
    )
    
    class Meta:
        ordering = ['academic_year', 'semester', 'day_of_week', 'start_time']
        verbose_name = "Timetable Slot"
        verbose_name_plural = "Timetable Slots"
        indexes = [
            Index(fields=['academic_year', 'semester']),
            Index(fields=['day_of_week', 'start_time']),
            Index(fields=['faculty', 'is_active']),
            Index(fields=['student_batch', 'is_active']),
        ]
    
    def __str__(self):
        course_info = f" - {self.course.code}" if self.course else ""
        faculty_info = f" ({self.faculty.name})" if self.faculty else ""
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}{course_info}{faculty_info}"
    
    @property
    def duration_minutes(self):
        """Calculate slot duration in minutes"""
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return end_minutes - start_minutes
    
    @property
    def academic_period_display(self):
        """Get formatted academic period display"""
        return f"{self.academic_year.year} - {self.semester.name}"
    
    @property
    def slot_display_name(self):
        """Get formatted slot display name"""
        if self.course and self.faculty:
            return f"{self.course.code} - {self.faculty.name}"
        elif self.course:
            return f"{self.course.code}"
        elif self.faculty:
            return f"{self.faculty.name}"
        elif self.subject:
            return self.subject
        else:
            return f"{self.get_slot_type_display()}"


class AcademicCalendar(models.Model):
    """Model for academic calendar events"""
    EVENT_TYPE = [
        ('HOLIDAY', 'Holiday'),
        ('EXAM', 'Examination'),
        ('BREAK', 'Break'),
        ('EVENT', 'Special Event'),
        ('DEADLINE', 'Deadline'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200, help_text="Event title")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE)
    start_date = models.DateField(help_text="Event start date")
    end_date = models.DateField(help_text="Event end date")
    description = models.TextField(help_text="Event description")
    academic_year = models.CharField(max_length=9, help_text="Academic year")
    semester = models.CharField(max_length=20, help_text="Semester (if applicable)")
    is_academic_day = models.BooleanField(default=True, help_text="Whether this is an academic day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_date', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.start_date} - {self.end_date})"
