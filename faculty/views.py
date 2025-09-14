from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Faculty, FacultySubject, FacultySchedule, FacultyLeave, 
    FacultyPerformance, FacultyDocument, CustomField, CustomFieldValue
)
from .serializers import (
    FacultySerializer, FacultyCreateSerializer, FacultyUpdateSerializer,
    FacultyListSerializer, FacultyDetailSerializer, FacultySubjectSerializer,
    FacultySubjectCreateSerializer, FacultyScheduleSerializer, FacultyScheduleCreateSerializer,
    FacultyLeaveSerializer, FacultyLeaveCreateSerializer, FacultyPerformanceSerializer,
    FacultyPerformanceCreateSerializer, FacultyDocumentSerializer, FacultyDocumentCreateSerializer,
    CustomFieldSerializer, CustomFieldCreateSerializer, CustomFieldValueSerializer, CustomFieldValueCreateSerializer
)


class FacultyViewSet(viewsets.ModelViewSet):
    """ViewSet for Faculty model with comprehensive CRUD operations"""
    queryset = Faculty.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'status', 'designation', 'department', 'employment_type', 
        'is_head_of_department', 'is_mentor', 'gender', 'currently_associated',
        'nature_of_association', 'contractual_full_time_part_time'
    ]
    search_fields = [
        'name', 'first_name', 'last_name', 'middle_name', 'employee_id', 
        'apaar_faculty_id', 'email', 'phone_number', 'area_of_specialization',
        'pan_no', 'highest_degree', 'university'
    ]
    ordering_fields = [
        'name', 'first_name', 'last_name', 'date_of_joining_institution', 'experience_in_current_institute',
        'created_at', 'updated_at'
    ]
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return FacultyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FacultyUpdateSerializer
        elif self.action == 'retrieve':
            return FacultyDetailSerializer
        elif self.action == 'list':
            return FacultyListSerializer
        return FacultySerializer

    def get_queryset(self):
        """Return filtered queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Add department filter if user is not admin
        if not self.request.user.is_superuser:
            # Filter by department if user has department-specific access
            # This can be customized based on your permission system
            pass
        
        return queryset.select_related('user').prefetch_related(
            'subjects', 'schedules', 'leaves', 'performances', 'documents', 'custom_field_values__custom_field'
        )

    @action(detail=False, methods=['get'])
    def active_faculty(self, request):
        """Get all active faculty members"""
        active_faculty = self.get_queryset().filter(status='ACTIVE', currently_associated=True)
        serializer = self.get_serializer(active_faculty, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def department_heads(self, request):
        """Get all department heads"""
        department_heads = self.get_queryset().filter(is_head_of_department=True)
        serializer = self.get_serializer(department_heads, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mentors(self, request):
        """Get all faculty mentors"""
        mentors = self.get_queryset().filter(is_mentor=True)
        serializer = self.get_serializer(mentors, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get faculty statistics"""
        total_faculty = Faculty.objects.count()
        active_faculty = Faculty.objects.filter(status='ACTIVE', currently_associated=True).count()
        department_stats = Faculty.objects.values('department').annotate(
            count=Count('id')
        ).order_by('-count')
        
        designation_stats = Faculty.objects.values('present_designation').annotate(
            count=Count('id')
        ).order_by('-count')
        
        employment_stats = Faculty.objects.values('employment_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        association_stats = Faculty.objects.values('nature_of_association').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_faculty': total_faculty,
            'active_faculty': active_faculty,
            'department_statistics': department_stats,
            'designation_statistics': designation_stats,
            'employment_statistics': employment_stats,
            'association_statistics': association_stats,
        })

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Get faculty schedule"""
        faculty = self.get_object()
        schedules = faculty.schedules.all().order_by('day_of_week', 'start_time')
        serializer = FacultyScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """Get faculty subjects"""
        faculty = self.get_object()
        subjects = faculty.subjects.all().order_by('subject_name')
        serializer = FacultySubjectSerializer(subjects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def leaves(self, request, pk=None):
        """Get faculty leave history"""
        faculty = self.get_object()
        leaves = faculty.leaves.all().order_by('-start_date')
        serializer = FacultyLeaveSerializer(leaves, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get faculty performance history"""
        faculty = self.get_object()
        performances = faculty.performances.all().order_by('-evaluation_date')
        serializer = FacultyPerformanceSerializer(performances, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def custom_fields(self, request, pk=None):
        """Get faculty custom field values"""
        faculty = self.get_object()
        custom_fields = faculty.custom_field_values.all().select_related('custom_field')
        serializer = CustomFieldValueSerializer(custom_fields, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset faculty password to default"""
        faculty = self.get_object()
        if faculty.user:
            faculty.user.set_password('CampusHub@360')
            faculty.user.save()
            return Response({'message': 'Password reset successfully to default password'})
        return Response({'error': 'No user account found'}, status=400)


class CustomFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomField model"""
    queryset = CustomField.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field_type', 'required', 'is_active']
    search_fields = ['name', 'label', 'help_text']
    ordering_fields = ['order', 'name', 'label']
    ordering = ['order', 'name']

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomFieldCreateSerializer
        return CustomFieldSerializer

    @action(detail=False, methods=['get'])
    def active_fields(self, request):
        """Get all active custom fields"""
        active_fields = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active_fields, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get custom fields by type"""
        field_type = request.query_params.get('field_type')
        if field_type:
            fields = self.get_queryset().filter(field_type=field_type, is_active=True)
            serializer = self.get_serializer(fields, many=True)
            return Response(serializer.data)
        return Response({'error': 'field_type parameter is required'}, status=400)


class CustomFieldValueViewSet(viewsets.ModelViewSet):
    """ViewSet for CustomFieldValue model"""
    queryset = CustomFieldValue.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'custom_field']
    search_fields = ['value', 'faculty__name', 'custom_field__label']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomFieldValueCreateSerializer
        return CustomFieldValueSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('faculty', 'custom_field')

    @action(detail=False, methods=['get'])
    def by_faculty(self, request):
        """Get custom field values by faculty"""
        faculty_id = request.query_params.get('faculty_id')
        if faculty_id:
            values = self.get_queryset().filter(faculty_id=faculty_id)
            serializer = self.get_serializer(values, many=True)
            return Response(serializer.data)
        return Response({'error': 'faculty_id parameter is required'}, status=400)

    @action(detail=False, methods=['get'])
    def by_field(self, request):
        """Get custom field values by field"""
        field_id = request.query_params.get('field_id')
        if field_id:
            values = self.get_queryset().filter(custom_field_id=field_id)
            serializer = self.get_serializer(values, many=True)
            return Response(serializer.data)
        return Response({'error': 'field_id parameter is required'}, status=400)


class FacultySubjectViewSet(viewsets.ModelViewSet):
    """ViewSet for FacultySubject model"""
    queryset = FacultySubject.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'grade_level', 'academic_year', 'is_primary_subject']
    search_fields = ['subject_name', 'faculty__name']
    ordering_fields = ['subject_name', 'grade_level', 'academic_year']
    ordering = ['faculty__name', 'subject_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return FacultySubjectCreateSerializer
        return FacultySubjectSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('faculty')

    @action(detail=False, methods=['get'])
    def by_subject(self, request):
        """Get all faculty teaching a specific subject"""
        subject_name = request.query_params.get('subject_name')
        if subject_name:
            subjects = self.get_queryset().filter(
                subject_name__icontains=subject_name
            )
            serializer = self.get_serializer(subjects, many=True)
            return Response(serializer.data)
        return Response({'error': 'subject_name parameter is required'}, status=400)

    @action(detail=False, methods=['get'])
    def by_grade(self, request):
        """Get all subjects for a specific grade level"""
        grade_level = request.query_params.get('grade_level')
        if grade_level:
            subjects = self.get_queryset().filter(grade_level=grade_level)
            serializer = self.get_serializer(subjects, many=True)
            return Response(serializer.data)
        return Response({'error': 'grade_level parameter is required'}, status=400)


class FacultyScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for FacultySchedule model"""
    queryset = FacultySchedule.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'day_of_week', 'grade_level', 'is_online']
    search_fields = ['subject', 'faculty__name', 'room_number']
    ordering_fields = ['day_of_week', 'start_time', 'end_time']
    ordering = ['day_of_week', 'start_time']

    def get_serializer_class(self):
        if self.action == 'create':
            return FacultyScheduleCreateSerializer
        return FacultyScheduleSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('faculty')

    @action(detail=False, methods=['get'])
    def today_schedule(self, request):
        """Get today's schedule for all faculty"""
        today = timezone.now().strftime('%A').upper()
        schedules = self.get_queryset().filter(day_of_week=today).order_by('start_time')
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def faculty_schedule(self, request):
        """Get schedule for a specific faculty member"""
        faculty_id = request.query_params.get('faculty_id')
        if faculty_id:
            schedules = self.get_queryset().filter(faculty_id=faculty_id).order_by('day_of_week', 'start_time')
            serializer = self.get_serializer(schedules, many=True)
            return Response(serializer.data)
        return Response({'error': 'faculty_id parameter is required'}, status=400)

    @action(detail=False, methods=['get'])
    def room_schedule(self, request):
        """Get schedule for a specific room"""
        room_number = request.query_params.get('room_number')
        if room_number:
            schedules = self.get_queryset().filter(room_number=room_number).order_by('day_of_week', 'start_time')
            serializer = self.get_serializer(schedules, many=True)
            return Response(serializer.data)
        return Response({'error': 'room_number parameter is required'}, status=400)


class FacultyLeaveViewSet(viewsets.ModelViewSet):
    """ViewSet for FacultyLeave model"""
    queryset = FacultyLeave.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'leave_type', 'status', 'approved_by']
    search_fields = ['reason', 'faculty__name']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return FacultyLeaveCreateSerializer
        return FacultyLeaveSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('faculty', 'approved_by')

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get all pending leave approvals"""
        pending_leaves = self.get_queryset().filter(status='PENDING').order_by('start_date')
        serializer = self.get_serializer(pending_leaves, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def approved_leaves(self, request):
        """Get all approved leaves"""
        approved_leaves = self.get_queryset().filter(status='APPROVED').order_by('-start_date')
        serializer = self.get_serializer(approved_leaves, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve_leave(self, request, pk=None):
        """Approve a leave request"""
        leave = self.get_object()
        if leave.status == 'PENDING':
            leave.status = 'APPROVED'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()
            serializer = self.get_serializer(leave)
            return Response(serializer.data)
        return Response({'error': 'Leave request is not pending'}, status=400)

    @action(detail=True, methods=['post'])
    def reject_leave(self, request, pk=None):
        """Reject a leave request"""
        leave = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if leave.status == 'PENDING':
            leave.status = 'REJECTED'
            leave.rejection_reason = rejection_reason
            leave.save()
            serializer = self.get_serializer(leave)
            return Response(serializer.data)
        return Response({'error': 'Leave request is not pending'}, status=400)

    @action(detail=False, methods=['get'])
    def current_leaves(self, request):
        """Get currently active leaves"""
        today = timezone.now().date()
        current_leaves = self.get_queryset().filter(
            start_date__lte=today,
            end_date__gte=today,
            status='APPROVED'
        ).order_by('end_date')
        serializer = self.get_serializer(current_leaves, many=True)
        return Response(serializer.data)


class FacultyPerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet for FacultyPerformance model"""
    queryset = FacultyPerformance.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'academic_year', 'evaluation_period', 'evaluated_by']
    search_fields = ['faculty__name', 'academic_year']
    ordering_fields = ['evaluation_date', 'overall_score']
    ordering = ['-evaluation_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return FacultyPerformanceCreateSerializer
        return FacultyPerformanceSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('faculty', 'evaluated_by')

    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing faculty members"""
        top_performers = self.get_queryset().order_by('-overall_score')[:10]
        serializer = self.get_serializer(top_performers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def performance_summary(self, request):
        """Get performance summary statistics"""
        academic_year = request.query_params.get('academic_year')
        queryset = self.get_queryset()
        
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        
        avg_scores = queryset.aggregate(
            avg_teaching=Avg('teaching_effectiveness'),
            avg_student_satisfaction=Avg('student_satisfaction'),
            avg_research=Avg('research_contribution'),
            avg_admin=Avg('administrative_work'),
            avg_professional=Avg('professional_development'),
            avg_overall=Avg('overall_score')
        )
        
        return Response(avg_scores)

    @action(detail=True, methods=['get'])
    def performance_history(self, request, pk=None):
        """Get performance history for a specific faculty member"""
        faculty = Faculty.objects.get(pk=pk)
        performances = faculty.performances.all().order_by('-evaluation_date')
        serializer = self.get_serializer(performances, many=True)
        return Response(serializer.data)


class FacultyDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for FacultyDocument model"""
    queryset = FacultyDocument.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['faculty', 'document_type', 'is_verified', 'verified_by']
    search_fields = ['title', 'description', 'faculty__name']
    ordering_fields = ['created_at', 'verified_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return FacultyDocumentCreateSerializer
        return FacultyDocumentSerializer

    def get_queryset(self):
        return super().get_queryset().select_related('faculty', 'verified_by')

    @action(detail=False, methods=['get'])
    def unverified_documents(self, request):
        """Get all unverified documents"""
        unverified_docs = self.get_queryset().filter(is_verified=False).order_by('created_at')
        serializer = self.get_serializer(unverified_docs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def verify_document(self, request, pk=None):
        """Verify a document"""
        document = self.get_object()
        if not document.is_verified:
            document.is_verified = True
            document.verified_by = request.user
            document.verified_at = timezone.now()
            document.save()
            serializer = self.get_serializer(document)
            return Response(serializer.data)
        return Response({'error': 'Document is already verified'}, status=400)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get documents by type"""
        document_type = request.query_params.get('document_type')
        if document_type:
            documents = self.get_queryset().filter(document_type=document_type)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        return Response({'error': 'document_type parameter is required'}, status=400)
