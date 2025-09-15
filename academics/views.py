from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from copy import deepcopy

from .models import (
    Course, CourseSection, Syllabus, SyllabusTopic, Timetable, 
    CourseEnrollment, AcademicCalendar, BatchCourseEnrollment, CoursePrerequisite
)
from .serializers import (
    CourseSerializer, CourseCreateSerializer, CourseDetailSerializer,
    CourseSectionSerializer, CourseSectionCreateSerializer,
    SyllabusSerializer, SyllabusCreateSerializer, SyllabusDetailSerializer,
    SyllabusTopicSerializer, TimetableSerializer, TimetableCreateSerializer,
    TimetableDetailSerializer, CourseEnrollmentSerializer, 
    CourseEnrollmentCreateSerializer, AcademicCalendarSerializer,
    AcademicCalendarCreateSerializer, BatchCourseEnrollmentSerializer,
    BatchCourseEnrollmentCreateSerializer, BatchCourseEnrollmentDetailSerializer,
    CoursePrerequisiteSerializer, CoursePrerequisiteCreateSerializer
)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for Course model"""
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'status', 'credits', 'department', 'programs']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['code', 'title', 'credits', 'created_at']
    ordering = ['code']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseCreateSerializer
        elif self.action in ['retrieve', 'detail']:
            return CourseDetailSerializer
        return CourseSerializer
    
    def get_queryset(self):
        queryset = Course.objects.select_related('department').prefetch_related('prerequisites', 'programs')
        return queryset
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed course information including syllabus, timetables, and enrollments"""
        course = self.get_object()
        serializer = self.get_serializer(course)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_faculty(self, request):
        """Get courses by specific faculty member"""
        faculty_id = request.query_params.get('faculty_id')
        if faculty_id:
            courses = Course.objects.filter(sections__faculty__id=faculty_id).distinct()
            serializer = self.get_serializer(courses, many=True)
            return Response(serializer.data)
        return Response({'error': 'faculty_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get courses by level"""
        level = request.query_params.get('level')
        if level:
            courses = Course.objects.filter(level=level)
            serializer = self.get_serializer(courses, many=True)
            return Response(serializer.data)
        return Response({'error': 'level parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get course statistics"""
        total_courses = Course.objects.count()
        active_courses = Course.objects.filter(status='ACTIVE').count()
        courses_by_level = Course.objects.values('level').annotate(count=Count('id'))
        
        return Response({
            'total_courses': total_courses,
            'active_courses': active_courses,
            'courses_by_level': courses_by_level
        })


class CourseSectionViewSet(viewsets.ModelViewSet):
    """ViewSet for CourseSection model"""
    queryset = CourseSection.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'course', 'student_batch', 'section_type', 'faculty', 'is_active'
    ]
    search_fields = [
        'course__code', 'course__title', 'student_batch__batch_name', 
        'faculty__first_name', 'faculty__last_name'
    ]
    ordering_fields = ['course__code', 'student_batch__batch_name', 'created_at']
    ordering = ['course__code', 'student_batch__batch_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseSectionCreateSerializer
        return CourseSectionSerializer
    
    def get_queryset(self):
        return CourseSection.objects.select_related(
            'course', 'student_batch', 'student_batch__department', 
            'student_batch__academic_program', 'faculty'
        )
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get sections for a specific course"""
        course_id = request.query_params.get('course_id')
        if course_id:
            sections = CourseSection.objects.filter(course_id=course_id)
            serializer = self.get_serializer(sections, many=True)
            return Response(serializer.data)
        return Response({'error': 'course_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_faculty(self, request):
        """Get sections for a specific faculty member"""
        faculty_id = request.query_params.get('faculty_id')
        if faculty_id:
            sections = CourseSection.objects.filter(faculty_id=faculty_id)
            serializer = self.get_serializer(sections, many=True)
            return Response(serializer.data)
        return Response({'error': 'faculty_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get sections for a specific student batch"""
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            sections = CourseSection.objects.filter(student_batch_id=batch_id)
            serializer = self.get_serializer(sections, many=True)
            return Response(serializer.data)
        return Response({'error': 'batch_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def available_sections(self, request):
        """Get sections with available capacity"""
        course_id = request.query_params.get('course_id')
        queryset = CourseSection.objects.filter(is_active=True)
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter sections with available capacity
        available_sections = []
        for section in queryset:
            if section.max_students is None or section.current_enrollment < section.max_students:
                available_sections.append(section)
        
        serializer = self.get_serializer(available_sections, many=True)
        return Response(serializer.data)


class SyllabusViewSet(viewsets.ModelViewSet):
    """ViewSet for Syllabus model"""
    queryset = Syllabus.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'academic_year', 'semester', 'course']
    search_fields = ['course__code', 'course__title']
    ordering_fields = ['academic_year', 'semester', 'created_at']
    ordering = ['-academic_year', '-semester']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SyllabusCreateSerializer
        elif self.action in ['retrieve', 'detail']:
            return SyllabusDetailSerializer
        return SyllabusSerializer
    
    def get_queryset(self):
        return Syllabus.objects.select_related('course', 'approved_by').prefetch_related('topics')
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed syllabus information including topics"""
        syllabus = self.get_object()
        serializer = self.get_serializer(syllabus)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a syllabus"""
        syllabus = self.get_object()
        if syllabus.status == 'DRAFT':
            syllabus.status = 'APPROVED'
            syllabus.approved_by = request.user
            syllabus.approved_at = timezone.now()
            syllabus.save()
            serializer = self.get_serializer(syllabus)
            return Response(serializer.data)
        return Response({'error': 'Only draft syllabi can be approved'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_academic_year(self, request):
        """Get syllabi by academic year"""
        academic_year = request.query_params.get('academic_year')
        if academic_year:
            syllabi = Syllabus.objects.filter(academic_year=academic_year)
            serializer = self.get_serializer(syllabi, many=True)
            return Response(serializer.data)
        return Response({'error': 'academic_year parameter required'}, status=400)


class SyllabusTopicViewSet(viewsets.ModelViewSet):
    """ViewSet for SyllabusTopic model"""
    queryset = SyllabusTopic.objects.all()
    serializer_class = SyllabusTopicSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['syllabus', 'week_number']
    ordering_fields = ['week_number', 'order']
    ordering = ['week_number', 'order']
    
    def get_queryset(self):
        return SyllabusTopic.objects.select_related('syllabus')


class TimetableViewSet(viewsets.ModelViewSet):
    """ViewSet for Timetable model"""
    queryset = Timetable.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'timetable_type', 'day_of_week', 'is_active',
        'course_section',
        'course_section__faculty', 'course_section__course'
    ]
    search_fields = ['course_section__course__code', 'course_section__course__title', 'room']
    ordering_fields = ['day_of_week', 'start_time']
    ordering = ['day_of_week', 'start_time']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TimetableCreateSerializer
        elif self.action in ['retrieve', 'detail']:
            return TimetableDetailSerializer
        return TimetableSerializer
    
    def get_queryset(self):
        return Timetable.objects.select_related('course_section', 'course_section__course', 'course_section__faculty')
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed timetable information"""
        timetable = self.get_object()
        serializer = self.get_serializer(timetable)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def weekly_schedule(self, request):
        """Get weekly schedule for a specific faculty or course"""
        faculty_id = request.query_params.get('faculty_id')
        course_id = request.query_params.get('course_id')
        
        queryset = Timetable.objects.filter(is_active=True)
        
        if faculty_id:
            queryset = queryset.filter(course_section__faculty_id=faculty_id)
        if course_id:
            queryset = queryset.filter(course_section__course_id=course_id)
        
        # Group by day of week (return IDs for grouping to keep JSON-serializable)
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        weekly_schedule: dict[str, list] = {d: [] for d in ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']}
        for item in data:
            day = item.get('day_of_week')
            if day in weekly_schedule:
                weekly_schedule[day].append(item)
        return Response({
            'weekly_schedule': weekly_schedule,
            'all_schedules': data
        })
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Check for timetable conflicts"""
        faculty_id = request.query_params.get('faculty_id')
        room = request.query_params.get('room')
        
        if not all([faculty_id, room]):
            return Response({'error': 'faculty_id and room parameters required'}, status=400)
        
        # Find overlapping schedules
        conflicts = []
        timetables = Timetable.objects.filter(
            course_section__faculty_id=faculty_id,
            room=room,
            is_active=True
        )
        
        for i, t1 in enumerate(timetables):
            for t2 in timetables[i+1:]:
                if t1.day_of_week == t2.day_of_week:
                    # Check for time overlap
                    if (t1.start_time < t2.end_time and t2.start_time < t1.end_time):
                        conflicts.append({
                            'conflict_type': 'Time Overlap',
                            'timetable1': TimetableSerializer(t1).data,
                            'timetable2': TimetableSerializer(t2).data
                        })
        
        return Response({'conflicts': conflicts, 'total_conflicts': len(conflicts)})


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for CourseEnrollment model"""
    queryset = CourseEnrollment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'student', 'course_section',
        'course_section__course', 'course_section__student_batch',
        'student__student_batch', 'enrollment_type'
    ]
    search_fields = [
        'student__roll_number', 'student__first_name', 'student__last_name',
        'course_section__course__code', 'course_section__student_batch__batch_name'
    ]
    ordering_fields = ['enrollment_date', 'student__roll_number', 'course_section__course__code']
    ordering = ['-enrollment_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CourseEnrollmentCreateSerializer
        return CourseEnrollmentSerializer
    
    def get_queryset(self):
        return CourseEnrollment.objects.select_related(
            'student', 'student__student_batch', 'student__student_batch__department',
            'student__student_batch__academic_program', 'student__student_batch__academic_year',
            'course_section', 'course_section__course', 'course_section__student_batch',
            'course_section__faculty'
        )
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Get enrollments for a specific student"""
        student_id = request.query_params.get('student_id')
        if student_id:
            enrollments = CourseEnrollment.objects.filter(student_id=student_id)
            serializer = self.get_serializer(enrollments, many=True)
            return Response(serializer.data)
        return Response({'error': 'student_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get enrollments for a specific course"""
        course_id = request.query_params.get('course_id')
        if course_id:
            enrollments = CourseEnrollment.objects.filter(course_section__course_id=course_id)
            serializer = self.get_serializer(enrollments, many=True)
            return Response(serializer.data)
        return Response({'error': 'course_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get enrollments for students in a specific batch"""
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            enrollments = CourseEnrollment.objects.filter(student__student_batch_id=batch_id)
            serializer = self.get_serializer(enrollments, many=True)
            return Response(serializer.data)
        return Response({'error': 'batch_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_course_section(self, request):
        """Get enrollments for a specific course section"""
        section_id = request.query_params.get('section_id')
        if section_id:
            enrollments = CourseEnrollment.objects.filter(course_section_id=section_id)
            serializer = self.get_serializer(enrollments, many=True)
            return Response(serializer.data)
        return Response({'error': 'section_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def batch_enrollment_summary(self, request):
        """Get enrollment summary by student batch"""
        batch_id = request.query_params.get('batch_id')
        course_id = request.query_params.get('course_id')
        
        queryset = CourseEnrollment.objects.filter(status='ENROLLED')
        
        if batch_id:
            queryset = queryset.filter(student__student_batch_id=batch_id)
        if course_id:
            queryset = queryset.filter(course_section__course_id=course_id)
        
        # Group by student batch and course
        from django.db.models import Count, Q
        summary = queryset.values(
            'student__student_batch__batch_name',
            'student__student_batch__department__name',
            'course_section__course__code',
            'course_section__course__title'
        ).annotate(
            enrolled_count=Count('id')
        ).order_by('student__student_batch__batch_name', 'course_section__course__code')
        
        return Response({
            'summary': list(summary),
            'total_enrollments': queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get enrollment statistics"""
        total_enrollments = CourseEnrollment.objects.count()
        active_enrollments = CourseEnrollment.objects.filter(status='ENROLLED').count()
        completed_enrollments = CourseEnrollment.objects.filter(status='COMPLETED').count()
        
        enrollments_by_status = CourseEnrollment.objects.values('status').annotate(count=Count('id'))
        enrollments_by_year = CourseEnrollment.objects.values('student__student_batch__academic_year__year').annotate(count=Count('id'))
        
        return Response({
            'total_enrollments': total_enrollments,
            'active_enrollments': active_enrollments,
            'completed_enrollments': completed_enrollments,
            'enrollments_by_status': enrollments_by_status,
            'enrollments_by_year': enrollments_by_year
        })


class AcademicCalendarViewSet(viewsets.ModelViewSet):
    """ViewSet for AcademicCalendar model"""
    queryset = AcademicCalendar.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'academic_year', 'semester', 'is_academic_day']
    search_fields = ['title', 'description']
    ordering_fields = ['start_date', 'end_date', 'title']
    ordering = ['start_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AcademicCalendarCreateSerializer
        return AcademicCalendarSerializer
    
    @action(detail=False, methods=['get'])
    def upcoming_events(self, request):
        """Get upcoming events"""
        today = timezone.now().date()
        upcoming = AcademicCalendar.objects.filter(
            start_date__gte=today
        ).order_by('start_date')[:10]
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_month(self, request):
        """Get events for a specific month"""
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        
        if not all([year, month]):
            return Response({'error': 'year and month parameters required'}, status=400)
        
        try:
            start_date = datetime(int(year), int(month), 1).date()
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1).date()
            else:
                end_date = datetime(int(year), int(month) + 1, 1).date()
            
            events = AcademicCalendar.objects.filter(
                start_date__gte=start_date,
                start_date__lt=end_date
            ).order_by('start_date')
            
            serializer = self.get_serializer(events, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response({'error': 'Invalid year or month'}, status=400)
    
    @action(detail=False, methods=['get'])
    def academic_days(self, request):
        """Get academic days for a specific period"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not all([start_date, end_date]):
            return Response({'error': 'start_date and end_date parameters required'}, status=400)
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            academic_days = AcademicCalendar.objects.filter(
                start_date__gte=start,
                end_date__lte=end,
                is_academic_day=True
            ).order_by('start_date')
            
            serializer = self.get_serializer(academic_days, many=True)
            return Response(serializer.data)
            
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)


class BatchCourseEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for BatchCourseEnrollment model"""
    queryset = BatchCourseEnrollment.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'student_batch', 'course', 'academic_year', 'semester',
        'student_batch__department', 'student_batch__academic_program',
        'auto_enroll_new_students'
    ]
    search_fields = [
        'student_batch__batch_name', 'course__code', 'course__title',
        'academic_year', 'semester'
    ]
    ordering_fields = ['enrollment_date', 'student_batch__batch_name', 'course__code']
    ordering = ['-enrollment_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BatchCourseEnrollmentCreateSerializer
        if self.action in ['retrieve', 'detail']:
            return BatchCourseEnrollmentDetailSerializer
        return BatchCourseEnrollmentSerializer
    
    def get_queryset(self):
        return BatchCourseEnrollment.objects.select_related(
            'student_batch', 'student_batch__department', 'student_batch__academic_program',
            'course', 'course_section', 'created_by'
        ).prefetch_related('student_batch__students')
    
    def create(self, request, *args, **kwargs):
        # Make request data mutable copy to provide defaults
        data = deepcopy(request.data)
        if not data.get('academic_year') or not data.get('semester'):
            from students.models import AcademicYear as StudentAcademicYear, Semester as StudentSemester
            if not data.get('academic_year'):
                current_year = StudentAcademicYear.objects.filter(is_active=True).order_by('-is_current', '-year').first()
                if current_year:
                    data['academic_year'] = current_year.year
            if not data.get('semester') and data.get('academic_year'):
                sem = StudentSemester.objects.filter(
                    academic_year__year=data['academic_year'], is_active=True
                ).order_by('-is_current', 'semester_type').first()
                if sem:
                    data['semester'] = sem.name
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        # Return full representation including id
        from .serializers import BatchCourseEnrollmentSerializer as BCEReadSerializer
        response_data = BCEReadSerializer(instance).data
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'], url_path='detail')
    def get_detail(self, request, pk=None):
        """Get detailed batch enrollment information including enrolled students"""
        batch_enrollment = self.get_object()
        serializer = BatchCourseEnrollmentDetailSerializer(batch_enrollment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def enroll_students(self, request, pk=None):
        """Manually enroll all students from the batch into the course"""
        batch_enrollment = self.get_object()
        
        if batch_enrollment.status != 'ACTIVE':
            return Response(
                {'error': 'Batch enrollment is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = batch_enrollment.enroll_batch_students()
        
        if result['success']:
            return Response({
                'message': f"Successfully enrolled {result['enrolled_count']} students",
                'enrolled_count': result['enrolled_count'],
                'total_students': result['total_students'],
                'errors': result['errors']
            })
        else:
            return Response(
                {'error': result['message']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate batch enrollment"""
        batch_enrollment = self.get_object()
        batch_enrollment.status = 'ACTIVE'
        batch_enrollment.save()
        
        # Auto-enroll students if enabled
        if batch_enrollment.auto_enroll_new_students:
            result = batch_enrollment.enroll_batch_students()
            if result['success']:
                return Response({
                    'message': f"Batch enrollment activated and {result['enrolled_count']} students enrolled",
                    'enrolled_count': result['enrolled_count']
                })
        
        return Response({'message': 'Batch enrollment activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate batch enrollment"""
        batch_enrollment = self.get_object()
        batch_enrollment.status = 'INACTIVE'
        batch_enrollment.save()
        return Response({'message': 'Batch enrollment deactivated'})
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get batch enrollments for a specific student batch"""
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            enrollments = BatchCourseEnrollment.objects.filter(student_batch_id=batch_id)
            serializer = self.get_serializer(enrollments, many=True)
            return Response(serializer.data)
        return Response({'error': 'batch_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get batch enrollments for a specific course"""
        course_id = request.query_params.get('course_id')
        if course_id:
            enrollments = BatchCourseEnrollment.objects.filter(course_id=course_id)
            serializer = self.get_serializer(enrollments, many=True)
            return Response(serializer.data)
        return Response({'error': 'course_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get batch enrollment statistics"""
        total_batch_enrollments = BatchCourseEnrollment.objects.count()
        active_batch_enrollments = BatchCourseEnrollment.objects.filter(status='ACTIVE').count()
        
        # Get enrollment statistics by academic year
        enrollments_by_year = BatchCourseEnrollment.objects.values(
            'academic_year'
        ).annotate(count=Count('id'))
        
        # Get enrollment statistics by department
        enrollments_by_department = BatchCourseEnrollment.objects.values(
            'student_batch__department__name'
        ).annotate(count=Count('id'))
        
        return Response({
            'total_batch_enrollments': total_batch_enrollments,
            'active_batch_enrollments': active_batch_enrollments,
            'enrollments_by_year': enrollments_by_year,
            'enrollments_by_department': enrollments_by_department
        })
    
    @action(detail=False, methods=['post'])
    def bulk_enroll(self, request):
        """Bulk enroll multiple batches to multiple courses"""
        data = request.data
        batch_ids = data.get('batch_ids', [])
        course_ids = data.get('course_ids', [])
        academic_year = data.get('academic_year')
        semester = data.get('semester')
        auto_enroll = data.get('auto_enroll_new_students', True)
        
        if not all([batch_ids, course_ids, academic_year, semester]):
            return Response({
                'error': 'batch_ids, course_ids, academic_year, and semester are required'
            }, status=400)
        
        results = []
        errors = []
        
        for batch_id in batch_ids:
            for course_id in course_ids:
                try:
                    batch_enrollment = BatchCourseEnrollment.objects.create(
                        student_batch_id=batch_id,
                        course_id=course_id,
                        academic_year=academic_year,
                        semester=semester,
                        auto_enroll_new_students=auto_enroll,
                        created_by=request.user
                    )
                    results.append({
                        'batch_id': batch_id,
                        'course_id': course_id,
                        'enrollment_id': batch_enrollment.id,
                        'status': 'created'
                    })
                except Exception as e:
                    errors.append({
                        'batch_id': batch_id,
                        'course_id': course_id,
                        'error': str(e)
                    })
        
        return Response({
            'created_enrollments': results,
            'errors': errors,
            'total_created': len(results),
            'total_errors': len(errors)
        })


class CoursePrerequisiteViewSet(viewsets.ModelViewSet):
    """ViewSet for CoursePrerequisite model"""
    queryset = CoursePrerequisite.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'course', 'prerequisite_course', 'student_batch', 'is_mandatory'
    ]
    search_fields = [
        'course__code', 'course__title', 'prerequisite_course__code', 'prerequisite_course__title'
    ]
    ordering_fields = ['course__code', 'prerequisite_course__code', 'created_at']
    ordering = ['course__code', 'prerequisite_course__code']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CoursePrerequisiteCreateSerializer
        return CoursePrerequisiteSerializer
    
    def get_queryset(self):
        return CoursePrerequisite.objects.select_related(
            'course', 'prerequisite_course', 'student_batch'
        )
    
    @action(detail=False, methods=['get'])
    def by_course(self, request):
        """Get prerequisites for a specific course"""
        course_id = request.query_params.get('course_id')
        if course_id:
            prerequisites = CoursePrerequisite.objects.filter(course_id=course_id)
            serializer = self.get_serializer(prerequisites, many=True)
            return Response(serializer.data)
        return Response({'error': 'course_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get prerequisites for a specific student batch"""
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            prerequisites = CoursePrerequisite.objects.filter(
                Q(student_batch_id=batch_id) | Q(student_batch__isnull=True)
            )
            serializer = self.get_serializer(prerequisites, many=True)
            return Response(serializer.data)
        return Response({'error': 'batch_id parameter required'}, status=400)
    
    @action(detail=False, methods=['get'])
    def check_prerequisites(self, request):
        """Check if a student/batch meets prerequisites for a course"""
        student_id = request.query_params.get('student_id')
        batch_id = request.query_params.get('batch_id')
        course_id = request.query_params.get('course_id')
        
        if not course_id or not (student_id or batch_id):
            return Response({
                'error': 'course_id and either student_id or batch_id are required'
            }, status=400)
        
        # Get prerequisites for the course
        prerequisites = CoursePrerequisite.objects.filter(course_id=course_id)
        
        if student_id:
            # Check prerequisites for specific student
            from students.models import Student
            try:
                student = Student.objects.get(id=student_id)
                batch_id = student.student_batch_id if student.student_batch else None
            except Student.DoesNotExist:
                return Response({'error': 'Student not found'}, status=404)
        
        # Filter prerequisites for the batch
        batch_prerequisites = prerequisites.filter(
            Q(student_batch_id=batch_id) | Q(student_batch__isnull=True)
        )
        
        met_prerequisites = []
        unmet_prerequisites = []
        
        for prereq in batch_prerequisites:
            # Check if student has completed the prerequisite course
            completed = CourseEnrollment.objects.filter(
                student__student_batch_id=batch_id,
                course_section__course=prereq.prerequisite_course,
                status='COMPLETED'
            ).exists()
            
            if completed:
                met_prerequisites.append({
                    'prerequisite': CoursePrerequisiteSerializer(prereq).data,
                    'status': 'met'
                })
            else:
                unmet_prerequisites.append({
                    'prerequisite': CoursePrerequisiteSerializer(prereq).data,
                    'status': 'unmet'
                })
        
        return Response({
            'met_prerequisites': met_prerequisites,
            'unmet_prerequisites': unmet_prerequisites,
            'total_prerequisites': len(met_prerequisites) + len(unmet_prerequisites),
            'all_prerequisites_met': len(unmet_prerequisites) == 0
        })
