from rest_framework import serializers
from .models import (
    Course, CourseSection, Syllabus, SyllabusTopic, Timetable, 
    CourseEnrollment, AcademicCalendar, BatchCourseEnrollment, CoursePrerequisite
)
from faculty.serializers import FacultySerializer
from students.serializers import StudentSerializer, StudentBatchSerializer


class CourseSerializer(serializers.ModelSerializer):
    department = serializers.StringRelatedField(read_only=True)
    programs = serializers.StringRelatedField(many=True, read_only=True)
    prerequisites = serializers.StringRelatedField(many=True, read_only=True)
    enrolled_students_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'title', 'description', 'level', 'credits',
            'duration_weeks', 'max_students', 'prerequisites', 'department', 'programs',
            'status', 'enrolled_students_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_enrolled_students_count(self, obj):
        try:
            return sum(section.get_enrolled_students_count() for section in obj.sections.all())
        except Exception:
            return 0


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'code', 'title', 'description', 'level', 'credits',
            'duration_weeks', 'max_students', 'prerequisites', 'department', 'programs', 'status'
        ]


class SyllabusTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyllabusTopic
        fields = [
            'id', 'week_number', 'title', 'description', 'learning_outcomes',
            'readings', 'activities', 'duration_hours', 'order'
        ]
        read_only_fields = ['id']


class SyllabusSerializer(serializers.ModelSerializer):
    topics = SyllabusTopicSerializer(many=True, read_only=True)
    course = CourseSerializer(read_only=True)
    approved_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Syllabus
        fields = [
            'id', 'course', 'version', 'academic_year', 'semester',
            'learning_objectives', 'course_outline', 'assessment_methods',
            'grading_policy', 'textbooks', 'additional_resources', 'status',
            'approved_by', 'approved_at', 'topics', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SyllabusCreateSerializer(serializers.ModelSerializer):
    topics = SyllabusTopicSerializer(many=True, required=False)
    
    class Meta:
        model = Syllabus
        fields = [
            'course', 'version', 'academic_year', 'semester',
            'learning_objectives', 'course_outline', 'assessment_methods',
            'grading_policy', 'textbooks', 'additional_resources', 'status', 'topics'
        ]
    
    def create(self, validated_data):
        topics_data = validated_data.pop('topics', [])
        syllabus = Syllabus.objects.create(**validated_data)
        
        for topic_data in topics_data:
            SyllabusTopic.objects.create(syllabus=syllabus, **topic_data)
        
        return syllabus
    
    def update(self, instance, validated_data):
        topics_data = validated_data.pop('topics', [])
        
        # Update syllabus fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update topics
        if topics_data:
            # Remove existing topics
            instance.topics.all().delete()
            # Create new topics
            for topic_data in topics_data:
                SyllabusTopic.objects.create(syllabus=instance, **topic_data)
        
        return instance


class CourseSectionSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student_batch = StudentBatchSerializer(read_only=True)
    faculty = serializers.StringRelatedField(read_only=True)
    section_number = serializers.SerializerMethodField()
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    available_seats = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseSection
        fields = [
            'id', 'course', 'student_batch', 'section_number', 'section_type', 
            'section_type_display', 'faculty', 'max_students', 'current_enrollment', 
            'available_seats', 'academic_year', 'semester', 'is_active', 'notes', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_enrollment', 'created_at', 'updated_at']
    
    def get_section_number(self, obj):
        return obj.section_number
    
    def get_available_seats(self, obj):
        return obj.get_available_seats()
    
    def get_academic_year(self, obj):
        return obj.academic_year
    
    def get_semester(self, obj):
        return obj.semester


class CourseSectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSection
        fields = [
            'course', 'student_batch', 'section_type', 'faculty', 
            'max_students', 'current_enrollment', 'is_active', 'notes'
        ]


class TimetableSerializer(serializers.ModelSerializer):
    course = serializers.SerializerMethodField()
    faculty = serializers.SerializerMethodField()
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Timetable
        fields = [
            'id', 'course', 'timetable_type', 'day_of_week', 'day_of_week_display', 'start_time', 'end_time',
            'room', 'faculty', 'is_active', 'notes', 'duration_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_course(self, obj):
        try:
            return CourseSerializer(obj.course_section.course).data
        except Exception:
            return None

    def get_faculty(self, obj):
        try:
            from faculty.serializers import FacultySerializer as FSer
            return FSer(obj.course_section.faculty).data
        except Exception:
            return None

    def get_duration_minutes(self, obj):
        try:
            return obj.get_duration_minutes()
        except Exception:
            return None


class TimetableCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = [
            'course_section', 'timetable_type',
            'day_of_week', 'start_time', 'end_time', 'room',
            'is_active', 'notes'
        ]


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    course_section = CourseSectionSerializer(read_only=True)
    student_batch = serializers.SerializerMethodField()
    academic_year = serializers.SerializerMethodField()
    semester = serializers.SerializerMethodField()
    section_number = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'student', 'course', 'course_section', 'student_batch', 
            'academic_year', 'semester', 'section_number',
            'enrollment_date', 'status', 'grade', 'grade_points',
            'attendance_percentage', 'enrollment_type', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'enrollment_date', 'created_at', 'updated_at']

    def get_course(self, obj):
        try:
            return CourseSerializer(obj.course).data
        except Exception:
            return None

    def get_academic_year(self, obj):
        try:
            return obj.academic_year
        except Exception:
            return None

    def get_semester(self, obj):
        try:
            return obj.semester
        except Exception:
            return None
    
    def get_student_batch(self, obj):
        try:
            if obj.student and obj.student.student_batch:
                return StudentBatchSerializer(obj.student.student_batch).data
            return None
        except Exception:
            return None
    
    def get_section_number(self, obj):
        try:
            if obj.course_section and obj.course_section.student_batch:
                return obj.course_section.student_batch.section
            return None
        except Exception:
            return None


class CourseEnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = [
            'student', 'course_section',
            'status', 'grade', 'grade_points', 'attendance_percentage', 'enrollment_type', 'notes'
        ]


class AcademicCalendarSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = AcademicCalendar
        fields = [
            'id', 'title', 'event_type', 'event_type_display', 'start_date',
            'end_date', 'description', 'academic_year', 'semester',
            'is_academic_day', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AcademicCalendarCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicCalendar
        fields = [
            'title', 'event_type', 'start_date', 'end_date', 'description',
            'academic_year', 'semester', 'is_academic_day'
        ]


# Nested serializers for detailed views
class CourseDetailSerializer(CourseSerializer):
    syllabus = SyllabusSerializer(read_only=True)
    timetables = TimetableSerializer(many=True, read_only=True)
    enrollments = CourseEnrollmentSerializer(many=True, read_only=True)
    
    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['syllabus', 'timetables', 'enrollments']


class SyllabusDetailSerializer(SyllabusSerializer):
    topics = SyllabusTopicSerializer(many=True, read_only=True)
    
    class Meta(SyllabusSerializer.Meta):
        fields = SyllabusSerializer.Meta.fields


class TimetableDetailSerializer(TimetableSerializer):
    course = CourseSerializer(read_only=True)
    faculty = FacultySerializer(read_only=True)
    
    class Meta(TimetableSerializer.Meta):
        fields = TimetableSerializer.Meta.fields


# Batch Enrollment Serializers
class BatchCourseEnrollmentSerializer(serializers.ModelSerializer):
    student_batch = StudentBatchSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    course_section = serializers.StringRelatedField(read_only=True)
    enrolled_students_count = serializers.SerializerMethodField()
    batch_students_count = serializers.SerializerMethodField()
    enrollment_percentage = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = BatchCourseEnrollment
        fields = [
            'id', 'student_batch', 'course', 'course_section', 'academic_year', 'semester',
            'enrollment_date', 'status', 'auto_enroll_new_students', 'notes',
            'enrolled_students_count', 'batch_students_count', 'enrollment_percentage',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'enrollment_date', 'created_at', 'updated_at']
    
    def get_enrolled_students_count(self, obj):
        return obj.get_enrolled_students_count()
    
    def get_batch_students_count(self, obj):
        return obj.get_batch_students_count()
    
    def get_enrollment_percentage(self, obj):
        return obj.get_enrollment_percentage()


class BatchCourseEnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchCourseEnrollment
        fields = [
            'student_batch', 'course', 'course_section', 'academic_year', 'semester',
            'status', 'auto_enroll_new_students', 'notes'
        ]
    
    def validate(self, data):
        # Validate that the course is appropriate for the student batch
        student_batch = data.get('student_batch')
        course = data.get('course')
        
        if student_batch and course:
            # Check if course is available for the batch's academic program
            if student_batch.academic_program and course not in student_batch.academic_program.courses.all():
                raise serializers.ValidationError(
                    f"Course {course.code} is not available for program {student_batch.academic_program.code}"
                )
            
            # Check if course level matches batch year of study
            if course.level == 'UG' and int(student_batch.year_of_study) > 4:
                raise serializers.ValidationError(
                    f"Undergraduate course {course.code} is not suitable for year {student_batch.year_of_study}"
                )
        
        return data


class BatchCourseEnrollmentDetailSerializer(BatchCourseEnrollmentSerializer):
    enrolled_students = serializers.SerializerMethodField()
    
    class Meta(BatchCourseEnrollmentSerializer.Meta):
        fields = BatchCourseEnrollmentSerializer.Meta.fields + ['enrolled_students']
    
    def get_enrolled_students(self, obj):
        """Get list of enrolled students from this batch"""
        enrollments = CourseEnrollment.objects.filter(
            student__student_batch=obj.student_batch,
            course_section__course=obj.course,
            status='ENROLLED'
        ).select_related('student')
        
        return StudentSerializer([enrollment.student for enrollment in enrollments], many=True).data


class CoursePrerequisiteSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    prerequisite_course = CourseSerializer(read_only=True)
    student_batch = StudentBatchSerializer(read_only=True)
    
    class Meta:
        model = CoursePrerequisite
        fields = [
            'id', 'course', 'prerequisite_course', 'student_batch',
            'is_mandatory', 'minimum_grade', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CoursePrerequisiteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePrerequisite
        fields = [
            'course', 'prerequisite_course', 'student_batch',
            'is_mandatory', 'minimum_grade'
        ]
    
    def validate(self, data):
        course = data.get('course')
        prerequisite_course = data.get('prerequisite_course')
        
        if course and prerequisite_course:
            if course == prerequisite_course:
                raise serializers.ValidationError("Course cannot be a prerequisite for itself")
            
            # Check for circular dependencies
            if CoursePrerequisite.objects.filter(
                course=prerequisite_course,
                prerequisite_course=course
            ).exists():
                raise serializers.ValidationError(
                    f"Circular dependency detected: {course.code} and {prerequisite_course.code} are mutually prerequisite"
                )
        
        return data
