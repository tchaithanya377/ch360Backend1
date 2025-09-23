# Student Courses Implementation Prompt

## Overview
Create a comprehensive system for retrieving courses based on student enrollment and student batch for an Indian AP (Andhra Pradesh) university. The system should handle individual student enrollments, batch-based course assignments, and provide detailed course information with academic context.

## Core Requirements

### 1. Student Course Retrieval System

#### Get Student's Enrolled Courses
- **URL**: `GET /api/student-portal/courses/enrolled/`
- **Purpose**: Get all courses a student is currently enrolled in
- **Authentication**: JWT Token required

#### Request Parameters
```json
{
    "academic_year": "2024-2025",  // Optional: Filter by academic year
    "semester": "5",               // Optional: Filter by semester
    "status": "ENROLLED",          // Optional: Filter by enrollment status
    "include_grades": true,        // Optional: Include grade information
    "include_schedule": true       // Optional: Include timetable information
}
```

#### Response Format
```json
{
    "enrolled_courses": [
        {
            "enrollment_id": "uuid-string",
            "course": {
                "id": "uuid-string",
                "code": "CS301",
                "title": "Data Structures and Algorithms",
                "description": "Advanced data structures and algorithm design",
                "credits": 4,
                "level": "UG",
                "department": {
                    "id": "uuid-string",
                    "name": "Computer Science",
                    "code": "CS001"
                }
            },
            "course_section": {
                "id": "uuid-string",
                "section_type": "LECTURE",
                "faculty": {
                    "id": "uuid-string",
                    "name": "Dr. John Smith",
                    "email": "john.smith@university.edu"
                },
                "max_students": 60,
                "current_enrollment": 58,
                "available_seats": 2
            },
            "enrollment": {
                "enrollment_date": "2024-07-15",
                "status": "ENROLLED",
                "enrollment_type": "REGULAR",
                "grade": "A",
                "grade_points": 4.0,
                "attendance_percentage": 95.5,
                "notes": ""
            },
            "academic_context": {
                "academic_year": "2024-2025",
                "semester": "5",
                "year_of_study": "3",
                "section": "A"
            },
            "timetable": [
                {
                    "day": "MONDAY",
                    "start_time": "09:00:00",
                    "end_time": "10:30:00",
                    "room": "CS-101",
                    "building": "Computer Science Block"
                },
                {
                    "day": "WEDNESDAY",
                    "start_time": "09:00:00",
                    "end_time": "10:30:00",
                    "room": "CS-101",
                    "building": "Computer Science Block"
                }
            ]
        }
    ],
    "summary": {
        "total_courses": 6,
        "total_credits": 24,
        "enrolled_credits": 24,
        "completed_courses": 0,
        "current_gpa": 3.8,
        "attendance_average": 94.2
    },
    "academic_info": {
        "student_batch": {
            "batch_code": "CS-2024-3-A",
            "batch_name": "CS-2024-3-A",
            "department": "Computer Science",
            "academic_program": "B.Tech Computer Science",
            "year_of_study": "3rd Year",
            "section": "A",
            "semester": "5"
        },
        "academic_year": "2024-2025"
    }
}
```

### 2. Get Available Courses for Student

#### Available Courses Endpoint
- **URL**: `GET /api/student-portal/courses/available/`
- **Purpose**: Get courses available for enrollment based on student's batch and academic context
- **Authentication**: JWT Token required

#### Request Parameters
```json
{
    "academic_year": "2024-2025",  // Optional: Filter by academic year
    "semester": "5",               // Optional: Filter by semester
    "course_type": "ELECTIVE",     // Optional: MANDATORY, ELECTIVE, OPTIONAL
    "department": "CS001",         // Optional: Filter by department
    "include_prerequisites": true, // Optional: Include prerequisite information
    "include_sections": true       // Optional: Include available sections
}
```

#### Response Format
```json
{
    "available_courses": [
        {
            "course": {
                "id": "uuid-string",
                "code": "CS302",
                "title": "Database Management Systems",
                "description": "Introduction to database concepts and SQL",
                "credits": 3,
                "level": "UG",
                "department": {
                    "id": "uuid-string",
                    "name": "Computer Science",
                    "code": "CS001"
                }
            },
            "assignment_info": {
                "assignment_type": "MANDATORY",
                "year_of_study": 3,
                "is_required": true,
                "prerequisites": [
                    {
                        "course_code": "CS201",
                        "course_title": "Programming Fundamentals",
                        "status": "COMPLETED",
                        "grade": "A"
                    }
                ]
            },
            "available_sections": [
                {
                    "id": "uuid-string",
                    "section_type": "LECTURE",
                    "faculty": {
                        "id": "uuid-string",
                        "name": "Dr. Jane Doe",
                        "email": "jane.doe@university.edu"
                    },
                    "max_students": 60,
                    "current_enrollment": 45,
                    "available_seats": 15,
                    "timetable": [
                        {
                            "day": "TUESDAY",
                            "start_time": "11:00:00",
                            "end_time": "12:30:00",
                            "room": "CS-102",
                            "building": "Computer Science Block"
                        }
                    ]
                }
            ],
            "batch_enrollment": {
                "is_batch_enrolled": true,
                "auto_enroll": true,
                "enrollment_status": "ACTIVE"
            }
        }
    ],
    "filters_applied": {
        "academic_year": "2024-2025",
        "semester": "5",
        "department": "CS001"
    },
    "enrollment_guidelines": {
        "max_credits_per_semester": 30,
        "min_credits_per_semester": 15,
        "enrollment_deadline": "2024-08-15",
        "prerequisite_check_required": true
    }
}
```

### 3. Get Batch Courses

#### Batch Courses Endpoint
- **URL**: `GET /api/student-portal/courses/batch/`
- **Purpose**: Get all courses assigned to the student's batch
- **Authentication**: JWT Token required

#### Response Format
```json
{
    "batch_courses": [
        {
            "batch_enrollment": {
                "id": "uuid-string",
                "enrollment_date": "2024-07-01",
                "status": "ACTIVE",
                "auto_enroll_new_students": true,
                "notes": "Core curriculum for 3rd year CS students"
            },
            "course": {
                "id": "uuid-string",
                "code": "CS301",
                "title": "Data Structures and Algorithms",
                "description": "Advanced data structures and algorithm design",
                "credits": 4,
                "level": "UG"
            },
            "course_section": {
                "id": "uuid-string",
                "section_type": "LECTURE",
                "faculty": {
                    "id": "uuid-string",
                    "name": "Dr. John Smith",
                    "email": "john.smith@university.edu"
                },
                "max_students": 60,
                "current_enrollment": 58
            },
            "academic_context": {
                "academic_year": "2024-2025",
                "semester": "5",
                "year_of_study": "3",
                "section": "A"
            },
            "student_enrollment_status": "ENROLLED"  // ENROLLED, NOT_ENROLLED, DROPPED
        }
    ],
    "batch_info": {
        "batch_code": "CS-2024-3-A",
        "batch_name": "CS-2024-3-A",
        "department": "Computer Science",
        "academic_program": "B.Tech Computer Science",
        "total_students": 65,
        "enrolled_students": 63
    },
    "summary": {
        "total_batch_courses": 8,
        "mandatory_courses": 6,
        "elective_courses": 2,
        "total_credits": 24,
        "enrolled_courses": 6,
        "pending_enrollments": 2
    }
}
```

### 4. Course Enrollment Management

#### Enroll in Course
- **URL**: `POST /api/student-portal/courses/enroll/`
- **Purpose**: Enroll student in a specific course section
- **Authentication**: JWT Token required

#### Request Format
```json
{
    "course_section_id": "uuid-string",
    "enrollment_type": "REGULAR",  // REGULAR, AUDIT, CREDIT_TRANSFER, REPEAT
    "notes": "Elective course selection"
}
```

#### Response Format
```json
{
    "enrollment": {
        "id": "uuid-string",
        "student": {
            "id": "uuid-string",
            "roll_number": "22CS001",
            "name": "John Doe"
        },
        "course_section": {
            "id": "uuid-string",
            "course": {
                "code": "CS302",
                "title": "Database Management Systems"
            },
            "section_type": "LECTURE",
            "faculty": {
                "name": "Dr. Jane Doe"
            }
        },
        "enrollment_date": "2024-09-18",
        "status": "ENROLLED",
        "enrollment_type": "REGULAR",
        "notes": "Elective course selection"
    },
    "message": "Successfully enrolled in CS302 - Database Management Systems"
}
```

#### Drop Course
- **URL**: `POST /api/student-portal/courses/drop/`
- **Purpose**: Drop a course enrollment
- **Authentication**: JWT Token required

#### Request Format
```json
{
    "enrollment_id": "uuid-string",
    "reason": "Schedule conflict",
    "notes": "Will retake in next semester"
}
```

## Technical Implementation Details

### 1. Database Models

#### Course Enrollment Model
```python
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
    course_section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='ENROLLED')
    grade = models.CharField(max_length=5, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    enrollment_type = models.CharField(max_length=20, choices=[
        ('REGULAR', 'Regular'),
        ('AUDIT', 'Audit'),
        ('CREDIT_TRANSFER', 'Credit Transfer'),
        ('REPEAT', 'Repeat Course'),
    ], default='REGULAR')
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'course_section']
        indexes = [
            Index(fields=['student', 'status']),
            Index(fields=['course_section', 'status']),
        ]
```

#### Batch Course Enrollment Model
```python
class BatchCourseEnrollment(models.Model):
    """Model for batch-based course enrollments"""
    ENROLLMENT_STATUS = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    student_batch = models.ForeignKey(
        'students.StudentBatch', 
        on_delete=models.CASCADE, 
        related_name='batch_enrollments'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='batch_enrollments'
    )
    course_section = models.ForeignKey(
        CourseSection, 
        on_delete=models.CASCADE, 
        related_name='batch_enrollments',
        null=True, 
        blank=True
    )
    academic_year = models.CharField(max_length=9)
    semester = models.CharField(max_length=20)
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='ACTIVE')
    auto_enroll_new_students = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student_batch', 'course', 'academic_year', 'semester']
```

### 2. API Views Implementation

#### Student Courses ViewSet
```python
class StudentCoursesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for student course management"""
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = StudentCourseSerializer
    
    def get_queryset(self):
        student = self.request.user.student_profile
        return CourseEnrollment.objects.filter(
            student=student
        ).select_related(
            'course_section__course',
            'course_section__faculty',
            'course_section__student_batch'
        ).prefetch_related(
            'course_section__timetable_set'
        )
    
    @action(detail=False, methods=['get'])
    def enrolled(self, request):
        """Get student's enrolled courses"""
        student = request.user.student_profile
        academic_year = request.query_params.get('academic_year')
        semester = request.query_params.get('semester')
        status = request.query_params.get('status', 'ENROLLED')
        
        queryset = self.get_queryset().filter(status=status)
        
        if academic_year:
            queryset = queryset.filter(
                course_section__student_batch__academic_year__year=academic_year
            )
        
        if semester:
            queryset = queryset.filter(
                course_section__student_batch__semester=semester
            )
        
        serializer = self.get_serializer(queryset, many=True)
        
        # Calculate summary statistics
        summary = self._calculate_enrollment_summary(queryset)
        academic_info = self._get_academic_info(student)
        
        return Response({
            'enrolled_courses': serializer.data,
            'summary': summary,
            'academic_info': academic_info
        })
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available courses for enrollment"""
        student = request.user.student_profile
        
        if not student.student_batch:
            return Response(
                {'error': 'No batch assigned'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        batch = student.student_batch
        
        # Get batch course enrollments
        batch_courses = BatchCourseEnrollment.objects.filter(
            student_batch=batch,
            status='ACTIVE'
        ).select_related(
            'course',
            'course_section__faculty'
        ).prefetch_related(
            'course__prerequisites',
            'course_section__timetable_set'
        )
        
        # Filter by request parameters
        course_type = request.query_params.get('course_type')
        if course_type:
            batch_courses = batch_courses.filter(assignment_type=course_type)
        
        serializer = AvailableCourseSerializer(batch_courses, many=True, context={
            'student': student,
            'request': request
        })
        
        return Response({
            'available_courses': serializer.data,
            'filters_applied': {
                'academic_year': batch.academic_year.year,
                'semester': batch.semester,
                'department': batch.department.code
            },
            'enrollment_guidelines': self._get_enrollment_guidelines()
        })
    
    @action(detail=False, methods=['get'])
    def batch(self, request):
        """Get courses assigned to student's batch"""
        student = request.user.student_profile
        
        if not student.student_batch:
            return Response(
                {'error': 'No batch assigned'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        batch = student.student_batch
        
        # Get batch course enrollments
        batch_enrollments = BatchCourseEnrollment.objects.filter(
            student_batch=batch,
            status='ACTIVE'
        ).select_related(
            'course',
            'course_section__faculty'
        )
        
        # Get student's current enrollments for status
        student_enrollments = CourseEnrollment.objects.filter(
            student=student,
            course_section__in=[be.course_section for be in batch_enrollments if be.course_section]
        ).values_list('course_section_id', 'status')
        
        enrollment_status_map = dict(student_enrollments)
        
        serializer = BatchCourseSerializer(batch_enrollments, many=True, context={
            'enrollment_status_map': enrollment_status_map
        })
        
        return Response({
            'batch_courses': serializer.data,
            'batch_info': {
                'batch_code': batch.batch_code,
                'batch_name': batch.batch_name,
                'department': batch.department.name,
                'academic_program': batch.academic_program.name if batch.academic_program else None,
                'total_students': batch.current_count,
                'enrolled_students': batch.current_count  # All students in batch
            },
            'summary': self._calculate_batch_summary(batch_enrollments, enrollment_status_map)
        })
    
    def _calculate_enrollment_summary(self, enrollments):
        """Calculate enrollment summary statistics"""
        total_courses = enrollments.count()
        total_credits = sum(
            enrollment.course_section.course.credits 
            for enrollment in enrollments
        )
        
        # Calculate GPA
        grades = [e.grade_points for e in enrollments if e.grade_points]
        gpa = sum(grades) / len(grades) if grades else 0
        
        # Calculate attendance average
        attendances = [e.attendance_percentage for e in enrollments if e.attendance_percentage]
        avg_attendance = sum(attendances) / len(attendances) if attendances else 0
        
        return {
            'total_courses': total_courses,
            'total_credits': total_credits,
            'enrolled_credits': total_credits,
            'completed_courses': enrollments.filter(status='COMPLETED').count(),
            'current_gpa': round(gpa, 2),
            'attendance_average': round(avg_attendance, 1)
        }
    
    def _get_academic_info(self, student):
        """Get student's academic information"""
        if not student.student_batch:
            return {}
        
        batch = student.student_batch
        return {
            'student_batch': {
                'batch_code': batch.batch_code,
                'batch_name': batch.batch_name,
                'department': batch.department.name,
                'academic_program': batch.academic_program.name if batch.academic_program else None,
                'year_of_study': batch.get_year_of_study_display(),
                'section': batch.get_section_display(),
                'semester': batch.semester
            },
            'academic_year': batch.academic_year.year if batch.academic_year else None
        }
```

### 3. Serializers

#### Student Course Serializer
```python
class StudentCourseSerializer(serializers.ModelSerializer):
    """Serializer for student course enrollments"""
    course = CourseSerializer(read_only=True)
    course_section = CourseSectionSerializer(read_only=True)
    enrollment = EnrollmentSerializer(source='*', read_only=True)
    academic_context = serializers.SerializerMethodField()
    timetable = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'enrollment_id', 'course', 'course_section', 
            'enrollment', 'academic_context', 'timetable'
        ]
    
    def get_academic_context(self, obj):
        """Get academic context from course section"""
        section = obj.course_section
        if section.student_batch:
            return {
                'academic_year': section.student_batch.academic_year.year,
                'semester': section.student_batch.semester,
                'year_of_study': section.student_batch.get_year_of_study_display(),
                'section': section.student_batch.get_section_display()
            }
        return {}
    
    def get_timetable(self, obj):
        """Get timetable for the course section"""
        timetables = obj.course_section.timetable_set.filter(is_active=True)
        return TimetableSerializer(timetables, many=True).data

class AvailableCourseSerializer(serializers.ModelSerializer):
    """Serializer for available courses"""
    course = CourseSerializer(read_only=True)
    assignment_info = serializers.SerializerMethodField()
    available_sections = serializers.SerializerMethodField()
    batch_enrollment = serializers.SerializerMethodField()
    
    class Meta:
        model = BatchCourseEnrollment
        fields = [
            'course', 'assignment_info', 'available_sections', 'batch_enrollment'
        ]
    
    def get_assignment_info(self, obj):
        """Get course assignment information"""
        return {
            'assignment_type': 'MANDATORY',  # Based on course assignment
            'year_of_study': obj.student_batch.year_of_study,
            'is_required': True,
            'prerequisites': self._get_prerequisites(obj.course)
        }
    
    def get_available_sections(self, obj):
        """Get available course sections"""
        if obj.course_section:
            return [CourseSectionSerializer(obj.course_section).data]
        
        # Get all sections for this course and batch
        sections = CourseSection.objects.filter(
            course=obj.course,
            student_batch=obj.student_batch,
            is_active=True
        ).select_related('faculty').prefetch_related('timetable_set')
        
        return CourseSectionSerializer(sections, many=True).data
    
    def get_batch_enrollment(self, obj):
        """Get batch enrollment information"""
        return {
            'is_batch_enrolled': True,
            'auto_enroll': obj.auto_enroll_new_students,
            'enrollment_status': obj.status
        }
    
    def _get_prerequisites(self, course):
        """Get course prerequisites with completion status"""
        student = self.context.get('student')
        prerequisites = []
        
        for prereq in course.prerequisites.all():
            # Check if student has completed prerequisite
            completed = CourseEnrollment.objects.filter(
                student=student,
                course_section__course=prereq,
                status='COMPLETED'
            ).first()
            
            prerequisites.append({
                'course_code': prereq.code,
                'course_title': prereq.title,
                'status': 'COMPLETED' if completed else 'PENDING',
                'grade': completed.grade if completed else None
            })
        
        return prerequisites
```

### 4. Course Enrollment Logic

#### Enrollment Service
```python
class CourseEnrollmentService:
    """Service for handling course enrollments"""
    
    @staticmethod
    def enroll_student_in_course(student, course_section, enrollment_type='REGULAR'):
        """Enroll a student in a course section"""
        try:
            with transaction.atomic():
                # Check if student can enroll
                if not course_section.can_enroll_student():
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
    def drop_course_enrollment(enrollment, reason=None, notes=None):
        """Drop a course enrollment"""
        try:
            with transaction.atomic():
                enrollment.status = 'DROPPED'
                if reason:
                    enrollment.notes = f"Drop reason: {reason}. {notes or ''}"
                enrollment.save()
                
                # Update section enrollment count
                course_section = enrollment.course_section
                course_section.current_enrollment -= 1
                course_section.save()
                
                return enrollment
                
        except Exception as e:
            raise ValidationError(f"Error dropping course: {str(e)}")
    
    @staticmethod
    def get_student_courses(student, academic_year=None, semester=None, status='ENROLLED'):
        """Get student's courses with filters"""
        queryset = CourseEnrollment.objects.filter(
            student=student,
            status=status
        ).select_related(
            'course_section__course',
            'course_section__faculty',
            'course_section__student_batch'
        ).prefetch_related(
            'course_section__timetable_set'
        )
        
        if academic_year:
            queryset = queryset.filter(
                course_section__student_batch__academic_year__year=academic_year
            )
        
        if semester:
            queryset = queryset.filter(
                course_section__student_batch__semester=semester
            )
        
        return queryset.order_by('course_section__course__code')
    
    @staticmethod
    def get_available_courses_for_student(student):
        """Get courses available for student enrollment"""
        if not student.student_batch:
            return []
        
        batch = student.student_batch
        
        # Get batch course enrollments
        batch_courses = BatchCourseEnrollment.objects.filter(
            student_batch=batch,
            status='ACTIVE'
        ).select_related(
            'course',
            'course_section__faculty'
        ).prefetch_related(
            'course__prerequisites',
            'course_section__timetable_set'
        )
        
        # Filter out already enrolled courses
        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=student,
            status='ENROLLED'
        ).values_list('course_section__course_id', flat=True)
        
        available_courses = []
        for batch_course in batch_courses:
            if batch_course.course.id not in enrolled_course_ids:
                available_courses.append(batch_course)
        
        return available_courses
```

### 5. URL Configuration

#### Student Portal URLs
```python
# students/student_portal_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .student_courses_views import StudentCoursesViewSet

router = DefaultRouter()
router.register(r'courses', StudentCoursesViewSet, basename='student-courses')

urlpatterns = [
    # Existing URLs...
    path('', include(router.urls)),
]
```

### 6. Performance Optimizations

#### Database Indexes
```python
class CourseEnrollment(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            Index(fields=['student', 'status']),
            Index(fields=['course_section', 'status']),
            Index(fields=['student', 'course_section']),
            Index(fields=['enrollment_date']),
        ]

class BatchCourseEnrollment(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            Index(fields=['student_batch', 'status']),
            Index(fields=['course', 'academic_year', 'semester']),
            Index(fields=['student_batch', 'course']),
        ]
```

#### Query Optimization
```python
# Use select_related for foreign keys
enrollments = CourseEnrollment.objects.select_related(
    'course_section__course',
    'course_section__faculty',
    'course_section__student_batch'
).filter(student=student)

# Use prefetch_related for reverse foreign keys
enrollments = enrollments.prefetch_related(
    'course_section__timetable_set',
    'course_section__course__prerequisites'
)
```

### 7. Error Handling

#### Standard Error Responses
```json
// Enrollment Error
{
    "error": "Student is already enrolled in this course section"
}

// Prerequisite Error
{
    "error": "Prerequisites not met",
    "missing_prerequisites": [
        {
            "course_code": "CS201",
            "course_title": "Programming Fundamentals"
        }
    ]
}

// Capacity Error
{
    "error": "Course section is full",
    "available_seats": 0,
    "waitlist_available": true
}

// Batch Error
{
    "error": "No batch assigned to student"
}
```

### 8. Testing Requirements

#### Unit Tests
- Course enrollment creation and validation
- Batch course enrollment retrieval
- Prerequisite checking
- Enrollment status updates
- Error handling scenarios

#### Integration Tests
- End-to-end enrollment workflow
- Batch-based course assignment
- Timetable integration
- Grade and attendance tracking

#### Performance Tests
- Course retrieval performance (target: <200ms)
- Batch course loading (target: <500ms)
- Enrollment operations (target: <300ms)
- Concurrent enrollment handling

### 9. Security Considerations

#### Permission Classes
```python
class CanEnrollInCourse(BasePermission):
    """Permission to enroll in courses"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is a student
        if not request.user.groups.filter(name='Student').exists():
            return False
        
        # Check enrollment deadlines
        return self._check_enrollment_deadline()
    
    def _check_enrollment_deadline(self):
        """Check if enrollment is within deadline"""
        # Implementation for deadline checking
        return True
```

### 10. Success Criteria

1. **Course Retrieval**: Students can view their enrolled courses with complete information
2. **Available Courses**: Students can see courses available for enrollment
3. **Batch Integration**: Courses are properly linked to student batches
4. **Enrollment Management**: Students can enroll and drop courses
5. **Academic Context**: All course information includes proper academic context
6. **Performance**: System handles 20K+ students efficiently
7. **Data Integrity**: Enrollment data is consistent and accurate
8. **User Experience**: Intuitive course management interface

## Implementation Timeline

1. **Week 1**: Database models and enrollment logic
2. **Week 2**: API endpoints and serializers
3. **Week 3**: Batch integration and course assignment
4. **Week 4**: Testing, optimization, and deployment

This implementation provides a comprehensive course management system that integrates student enrollment with batch-based course assignments, specifically designed for Indian AP universities with excellent performance characteristics.
