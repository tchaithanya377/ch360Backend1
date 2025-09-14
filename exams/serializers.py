from rest_framework import serializers
from django.utils import timezone
from .models import (
    ExamSession, ExamSchedule, ExamRoom, ExamRoomAllocation,
    ExamStaffAssignment, StudentDue, ExamRegistration, HallTicket,
    ExamAttendance, ExamViolation, ExamResult
)


class ExamSessionSerializer(serializers.ModelSerializer):
    is_registration_open = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    exam_schedules_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSession
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_exam_schedules_count(self, obj):
        return obj.exam_schedules.count()
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("End date must be after start date")
        
        if data['registration_start'] >= data['registration_end']:
            raise serializers.ValidationError("Registration end must be after registration start")
        
        if data['registration_end'] > data['start_date']:
            raise serializers.ValidationError("Registration must end before exam session starts")
        
        return data


class ExamScheduleSerializer(serializers.ModelSerializer):
    exam_session_name = serializers.CharField(source='exam_session.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    is_ongoing = serializers.ReadOnlyField()
    registrations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSchedule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_registrations_count(self, obj):
        return obj.registrations.count()
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        if data['passing_marks'] > data['total_marks']:
            raise serializers.ValidationError("Passing marks cannot exceed total marks")
        
        return data


class ExamRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRoom
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ExamRoomAllocationSerializer(serializers.ModelSerializer):
    exam_schedule_title = serializers.CharField(source='exam_schedule.title', read_only=True)
    exam_room_name = serializers.CharField(source='exam_room.name', read_only=True)
    
    class Meta:
        model = ExamRoomAllocation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        if data['allocated_capacity'] > data['exam_room'].capacity:
            raise serializers.ValidationError("Allocated capacity cannot exceed room capacity")
        return data


class ExamStaffAssignmentSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source='faculty.user.get_full_name', read_only=True)
    exam_schedule_title = serializers.CharField(source='exam_schedule.title', read_only=True)
    exam_room_name = serializers.CharField(source='exam_room.name', read_only=True)
    
    class Meta:
        model = ExamStaffAssignment
        fields = '__all__'
        read_only_fields = ['assigned_date', 'created_at', 'updated_at']


class StudentDueSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    remaining_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = StudentDue
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        if data['paid_amount'] > data['amount']:
            raise serializers.ValidationError("Paid amount cannot exceed total amount")
        return data


class ExamRegistrationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    exam_schedule_title = serializers.CharField(source='exam_schedule.title', read_only=True)
    course_code = serializers.CharField(source='exam_schedule.course.code', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = ExamRegistration
        fields = '__all__'
        read_only_fields = ['registration_date', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Check if student has pending dues
        student = data['student']
        pending_dues = StudentDue.objects.filter(
            student=student,
            status__in=['PENDING', 'OVERDUE']
        )
        
        if pending_dues.exists():
            raise serializers.ValidationError("Student has pending dues and cannot register for exams")
        
        # Check if registration is open
        exam_session = data['exam_schedule'].exam_session
        if not exam_session.is_registration_open:
            raise serializers.ValidationError("Exam registration is not open")
        
        return data


class HallTicketSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='exam_registration.student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='exam_registration.student.roll_number', read_only=True)
    exam_title = serializers.CharField(source='exam_registration.exam_schedule.title', read_only=True)
    course_code = serializers.CharField(source='exam_registration.exam_schedule.course.code', read_only=True)
    exam_date = serializers.DateField(source='exam_registration.exam_schedule.exam_date', read_only=True)
    start_time = serializers.TimeField(source='exam_registration.exam_schedule.start_time', read_only=True)
    end_time = serializers.TimeField(source='exam_registration.exam_schedule.end_time', read_only=True)
    exam_room_name = serializers.CharField(source='exam_room.name', read_only=True)
    building = serializers.CharField(source='exam_room.building', read_only=True)
    
    class Meta:
        model = HallTicket
        fields = '__all__'
        read_only_fields = ['ticket_number', 'generated_date', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Generate ticket number if not provided
        instance = super().create(validated_data)
        instance.generate_ticket_number()
        instance.save()
        return instance


class ExamAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='exam_registration.student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='exam_registration.student.roll_number', read_only=True)
    exam_title = serializers.CharField(source='exam_registration.exam_schedule.title', read_only=True)
    invigilator_name = serializers.CharField(source='invigilator.user.get_full_name', read_only=True)
    
    class Meta:
        model = ExamAttendance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        if data['status'] == 'PRESENT' and not data.get('check_in_time'):
            data['check_in_time'] = timezone.now()
        return data


class ExamViolationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='exam_registration.student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='exam_registration.student.roll_number', read_only=True)
    exam_title = serializers.CharField(source='exam_registration.exam_schedule.title', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.user.get_full_name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = ExamViolation
        fields = '__all__'
        read_only_fields = ['reported_at', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('is_resolved') and not data.get('action_taken'):
            raise serializers.ValidationError("Action taken is required when resolving a violation")
        return data


class ExamResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='exam_registration.student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='exam_registration.student.roll_number', read_only=True)
    exam_title = serializers.CharField(source='exam_registration.exam_schedule.title', read_only=True)
    course_code = serializers.CharField(source='exam_registration.exam_schedule.course.code', read_only=True)
    total_marks = serializers.IntegerField(source='exam_registration.exam_schedule.total_marks', read_only=True)
    passing_marks = serializers.IntegerField(source='exam_registration.exam_schedule.passing_marks', read_only=True)
    evaluated_by_name = serializers.CharField(source='evaluated_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = ExamResult
        fields = '__all__'
        read_only_fields = ['percentage', 'grade', 'is_pass', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('marks_obtained') is not None:
            total_marks = data['exam_registration'].exam_schedule.total_marks
            if data['marks_obtained'] > total_marks:
                raise serializers.ValidationError("Marks obtained cannot exceed total marks")
            if data['marks_obtained'] < 0:
                raise serializers.ValidationError("Marks obtained cannot be negative")
        return data
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.marks_obtained is not None:
            instance.calculate_grade_and_percentage()
            instance.save()
        return instance


# Nested serializers for detailed views
class ExamScheduleDetailSerializer(ExamScheduleSerializer):
    exam_session = ExamSessionSerializer(read_only=True)
    course = serializers.SerializerMethodField()
    room_allocations = ExamRoomAllocationSerializer(many=True, read_only=True)
    staff_assignments = ExamStaffAssignmentSerializer(many=True, read_only=True)
    
    def get_course(self, obj):
        from academics.serializers import CourseSerializer
        return CourseSerializer(obj.course).data


class ExamRegistrationDetailSerializer(ExamRegistrationSerializer):
    exam_schedule = ExamScheduleSerializer(read_only=True)
    hall_ticket = HallTicketSerializer(read_only=True)
    attendance = ExamAttendanceSerializer(read_only=True)
    result = ExamResultSerializer(read_only=True)
    violations = ExamViolationSerializer(many=True, read_only=True)


class HallTicketDetailSerializer(HallTicketSerializer):
    exam_registration = ExamRegistrationSerializer(read_only=True)
    exam_room = ExamRoomSerializer(read_only=True)


# Summary serializers for dashboard
class ExamSessionSummarySerializer(serializers.ModelSerializer):
    total_exams = serializers.SerializerMethodField()
    total_registrations = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamSession
        fields = ['id', 'name', 'session_type', 'academic_year', 'semester', 
                 'start_date', 'end_date', 'status', 'total_exams', 
                 'total_registrations', 'total_students']
    
    def get_total_exams(self, obj):
        return obj.exam_schedules.count()
    
    def get_total_registrations(self, obj):
        return sum(exam.registrations.count() for exam in obj.exam_schedules.all())
    
    def get_total_students(self, obj):
        from django.db.models import Count
        return obj.exam_schedules.aggregate(
            total_students=Count('registrations__student', distinct=True)
        )['total_students'] or 0


class StudentDueSummarySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    
    class Meta:
        model = StudentDue
        fields = ['id', 'student_name', 'student_roll_number', 'due_type', 
                 'amount', 'paid_amount', 'remaining_amount', 'due_date', 
                 'status', 'is_overdue']
