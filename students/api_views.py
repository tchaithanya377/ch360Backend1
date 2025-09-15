from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import os
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Student, StudentEnrollmentHistory, StudentDocument, 
    CustomField, StudentCustomFieldValue, StudentImport
)
# High-RPS batch listing support
from .models import StudentBatch
from .serializers import StudentBatchSerializer
from .api_serializers import (
    StudentSerializer, StudentDetailSerializer, StudentEnrollmentHistorySerializer,
    StudentDocumentSerializer, CustomFieldSerializer, StudentCustomFieldValueSerializer,
    StudentImportSerializer, StudentStatsSerializer
)
from .filters import StudentFilter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


@method_decorator(cache_page(60 * 5), name='list')
class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing students
    """
    queryset = Student.objects.all().select_related('user').only(
        'id','roll_number','first_name','last_name','middle_name','status','created_at','user_id'
    ).order_by('-created_at')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StudentFilter
    search_fields = [
        'roll_number', 'first_name', 'last_name', 'middle_name', 'email',
        'father_name', 'mother_name', 'student_mobile', 'father_mobile', 'mother_mobile'
    ]
    ordering_fields = [
        'roll_number', 'first_name', 'last_name', 'date_of_birth', 
        'status', 'created_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentSerializer

    def get_permissions(self):
        """Allow anonymous read-only access for load testing if enabled via env.
        Set ENABLE_PUBLIC_STUDENT_READS=True to bypass auth on safe read actions.
        """
        enable_public_reads = os.getenv('ENABLE_PUBLIC_STUDENT_READS', 'False').lower() == 'true'
        public_actions = {'list', 'retrieve', 'search', 'stats', 'documents', 'enrollment_history'}
        if enable_public_reads and self.action in public_actions and self.request.method == 'GET':
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get student statistics"""
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status='ACTIVE').count()
        students_with_login = Student.objects.filter(user__isnull=False).count()
        
        # Year of study distribution (via related student_batch)
        grade_distribution = Student.objects.values('student_batch__year_of_study').annotate(
            count=Count('id')
        ).order_by('student_batch__year_of_study')
        
        # Status distribution
        status_distribution = Student.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Recent enrollments (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_enrollments = Student.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Gender distribution
        gender_distribution = Student.objects.values('gender').annotate(
            count=Count('id')
        ).order_by('gender')
        
        data = {
            'total_students': total_students,
            'active_students': active_students,
            'students_with_login': students_with_login,
            'recent_enrollments': recent_enrollments,
            'grade_distribution': list(grade_distribution),
            'status_distribution': list(status_distribution),
            'gender_distribution': list(gender_distribution),
        }
        
        serializer = StudentStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search endpoint"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=400)
        
        students = Student.objects.only('id','roll_number','first_name','last_name','email').filter(
            Q(roll_number__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(email__icontains=query) |
            Q(father_name__icontains=query) |
            Q(mother_name__icontains=query) |
            Q(student_mobile__icontains=query)
        )[:20]  # Limit to 20 results
        
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def division_statistics(self, request):
        """Aggregated statistics grouped by department/year/semester/section (API v1)."""
        qs = Student.objects.all()

        # Optional filters
        dept = request.query_params.get('department')
        if dept:
            qs = qs.filter(student_batch__department_id=dept)
        ay = request.query_params.get('academic_year')
        if ay:
            qs = qs.filter(student_batch__academic_year__year=ay)

        data = {
            'total_students': qs.count(),
            'by_department': list(
                qs.values('student_batch__department__id','student_batch__department__code','student_batch__department__name')
                  .annotate(total=Count('id'))
                  .order_by('student_batch__department__code')
            ),
            'by_academic_year': list(
                qs.values('student_batch__academic_year__year').annotate(total=Count('id')).order_by('student_batch__academic_year__year')
            ),
            'by_year_of_study': list(
                qs.values('student_batch__year_of_study').annotate(total=Count('id')).order_by('student_batch__year_of_study')
            ),
            'by_semester': list(
                qs.values('student_batch__semester').annotate(total=Count('id')).order_by('student_batch__semester')
            ),
            'by_section': list(
                qs.values('student_batch__section').annotate(total=Count('id')).order_by('student_batch__section')
            ),
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def divisions(self, request):
        """Compact divisions listing with counts (API v1)."""
        base = Student.objects.select_related('student_batch__department','student_batch__academic_program')

        # Filters
        for qp, field in (
            ('department','student_batch__department_id'),
            ('academic_program','student_batch__academic_program_id'),
            ('academic_year','student_batch__academic_year__year'),
            ('year_of_study','student_batch__year_of_study'),
            ('semester','student_batch__semester'),
            ('section','student_batch__section'),
        ):
            val = request.query_params.get(qp)
            if val:
                base = base.filter(**{field: val})

        divisions = {}
        for row in base.values(
            'student_batch__department__code','student_batch__department__name',
            'student_batch__academic_program__code','student_batch__academic_program__name',
            'student_batch__academic_year__year','student_batch__year_of_study','student_batch__semester','student_batch__section'
        ).annotate(count=Count('id')):
            dcode = row['student_batch__department__code'] or 'UNASSIGNED'
            pcode = row['student_batch__academic_program__code'] or 'UNASSIGNED'
            ay = row['student_batch__academic_year__year'] or 'UNSET'
            yos = row['student_batch__year_of_study'] or 'UNSET'
            sem = row['student_batch__semester'] or 'UNSET'
            sec = row['student_batch__section'] or 'UNSET'

            d = divisions.setdefault(dcode, {
                'department_name': row['student_batch__department__name'],
                'programs': {}
            })
            p = d['programs'].setdefault(pcode, {
                'program_name': row['student_batch__academic_program__name'],
                'years': {}
            })
            y = p['years'].setdefault(ay, {'year_of_study': {}})
            ys = y['year_of_study'].setdefault(yos, {'semesters': {}})
            se = ys['semesters'].setdefault(sem, {'sections': {}})
            se['sections'][sec] = {'count': row['count']}

        return Response(divisions)

    @action(detail=True, methods=['post'])
    def create_login(self, request, pk=None):
        """Manually create login account for student"""
        student = self.get_object()
        
        if student.user:
            return Response(
                {'error': 'Student already has a login account'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # This will trigger the signal to create user
            student.save()
            return Response({'message': 'Login account created successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to create login account: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get student documents"""
        student = self.get_object()
        documents = StudentDocument.objects.select_related('uploaded_by').only(
            'id','title','document_type','uploaded_by_id','created_at','student_id','document_file'
        ).filter(student=student)
        serializer = StudentDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def enrollment_history(self, request, pk=None):
        """Get student enrollment history"""
        student = self.get_object()
        history = StudentEnrollmentHistory.objects.only('id','year_of_study','academic_year','enrollment_date','status','student_id').filter(student=student)
        serializer = StudentEnrollmentHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def custom_fields(self, request, pk=None):
        """Get student custom field values"""
        student = self.get_object()
        custom_values = StudentCustomFieldValue.objects.select_related('custom_field').only('id','custom_field_id','value','student_id').filter(student=student)
        serializer = StudentCustomFieldValueSerializer(custom_values, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create students"""
        students_data = request.data.get('students', [])
        if not students_data:
            return Response(
                {'error': 'No students data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_students = []
        errors = []
        
        for i, student_data in enumerate(students_data):
            try:
                serializer = self.get_serializer(data=student_data)
                if serializer.is_valid():
                    student = serializer.save()
                    created_students.append(student)
                else:
                    errors.append({
                        'row': i + 1,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'row': i + 1,
                    'errors': {'general': str(e)}
                })
        
        response_data = {
            'created_count': len(created_students),
            'error_count': len(errors),
            'errors': errors
        }
        
        if created_students:
            response_data['created_students'] = StudentSerializer(created_students, many=True).data
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update students"""
        updates_data = request.data.get('updates', [])
        if not updates_data:
            return Response(
                {'error': 'No updates data provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_students = []
        errors = []
        
        for update_data in updates_data:
            roll_number = update_data.get('roll_number')
            if not roll_number:
                errors.append({'error': 'roll_number is required for updates'})
                continue
            
            try:
                student = Student.objects.get(roll_number=roll_number)
                serializer = self.get_serializer(student, data=update_data, partial=True)
                if serializer.is_valid():
                    updated_student = serializer.save()
                    updated_students.append(updated_student)
                else:
                    errors.append({
                        'roll_number': roll_number,
                        'errors': serializer.errors
                    })
            except Student.DoesNotExist:
                errors.append({
                    'roll_number': roll_number,
                    'error': 'Student not found'
                })
            except Exception as e:
                errors.append({
                    'roll_number': roll_number,
                    'error': str(e)
                })
        
        response_data = {
            'updated_count': len(updated_students),
            'error_count': len(errors),
            'errors': errors
        }
        
        if updated_students:
            response_data['updated_students'] = StudentSerializer(updated_students, many=True).data
        
        return Response(response_data)

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """Bulk delete students"""
        roll_numbers = request.data.get('roll_numbers', [])
        if not roll_numbers:
            return Response(
                {'error': 'No roll numbers provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = 0
        errors = []
        
        for roll_number in roll_numbers:
            try:
                student = Student.objects.get(roll_number=roll_number)
                student.delete()
                deleted_count += 1
            except Student.DoesNotExist:
                errors.append({
                    'roll_number': roll_number,
                    'error': 'Student not found'
                })
            except Exception as e:
                errors.append({
                    'roll_number': roll_number,
                    'error': str(e)
                })
        
        return Response({
            'deleted_count': deleted_count,
            'error_count': len(errors),
            'errors': errors
        })


class StudentEnrollmentHistoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student enrollment history
    """
    queryset = StudentEnrollmentHistory.objects.all().order_by('-enrollment_date')
    serializer_class = StudentEnrollmentHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'academic_year', 'year_of_study', 'status']
    search_fields = ['student__first_name', 'student__last_name', 'student__roll_number']
    ordering_fields = ['enrollment_date', 'academic_year', 'year_of_study']
    ordering = ['-enrollment_date']


class StudentDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student documents
    """
    queryset = StudentDocument.objects.all().order_by('-created_at')
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'document_type', 'uploaded_by']
    search_fields = ['title', 'description', 'student__first_name', 'student__last_name']
    ordering_fields = ['created_at', 'title', 'document_type']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class CustomFieldViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing custom fields
    """
    queryset = CustomField.objects.filter(is_active=True).order_by('order')
    serializer_class = CustomFieldSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field_type', 'required', 'is_active']
    search_fields = ['name', 'label', 'help_text']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order']

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available field types"""
        field_types = CustomField.FIELD_TYPE_CHOICES
        return Response([{'value': choice[0], 'label': choice[1]} for choice in field_types])

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get custom field statistics"""
        total_fields = CustomField.objects.count()
        active_fields = CustomField.objects.filter(is_active=True).count()
        required_fields = CustomField.objects.filter(required=True).count()
        
        # Field type distribution
        type_distribution = CustomField.objects.values('field_type').annotate(
            count=Count('id')
        ).order_by('field_type')
        
        return Response({
            'total_fields': total_fields,
            'active_fields': active_fields,
            'required_fields': required_fields,
            'type_distribution': list(type_distribution)
        })


class StudentCustomFieldValueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student custom field values
    """
    queryset = StudentCustomFieldValue.objects.all().order_by('-created_at')
    serializer_class = StudentCustomFieldValueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'custom_field']
    search_fields = ['value', 'student__first_name', 'student__last_name', 'custom_field__name']
    ordering_fields = ['created_at', 'custom_field__name']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Get custom field values for a specific student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'error': 'student_id parameter is required'}, status=400)
        
        values = StudentCustomFieldValue.objects.select_related('custom_field').only('id','custom_field_id','value','student_id').filter(student_id=student_id)
        serializer = self.get_serializer(values, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_field(self, request):
        """Get values for a specific custom field"""
        field_id = request.query_params.get('field_id')
        if not field_id:
            return Response({'error': 'field_id parameter is required'}, status=400)
        
        values = StudentCustomFieldValue.objects.select_related('student').only('id','student_id','value','custom_field_id').filter(custom_field_id=field_id)
        serializer = self.get_serializer(values, many=True)
        return Response(serializer.data)


@method_decorator(cache_page(60 * 2), name='list')
class StudentImportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing student import history
    """
    queryset = StudentImport.objects.all().order_by('-created_at')
    serializer_class = StudentImportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'created_by']
    search_fields = ['filename']
    ordering_fields = ['created_at', 'success_count', 'error_count']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get import statistics"""
        total_imports = StudentImport.objects.count()
        successful_imports = StudentImport.objects.filter(status='COMPLETED').count()
        failed_imports = StudentImport.objects.filter(status='FAILED').count()
        
        # Recent imports (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_imports = StudentImport.objects.filter(
            created_at__gte=seven_days_ago
        ).count()
        
        # Total students imported
        total_students_imported = sum(
            import_record.success_count for import_record in StudentImport.objects.filter(status='COMPLETED')
        )
        
        return Response({
            'total_imports': total_imports,
            'successful_imports': successful_imports,
            'failed_imports': failed_imports,
            'recent_imports': recent_imports,
            'total_students_imported': total_students_imported
        })


@method_decorator(cache_page(60 * 2), name='list')
class StudentBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API v1 endpoint for listing student batches used by the enrollment UI.

    Optimized for high read throughput:
    - select_related for FK fields
    - ordering and search fields indexed/cheap
    - optional caching via cache_page
    """

    queryset = StudentBatch.objects.select_related(
        'department', 'academic_program', 'academic_year'
    ).only(
        'id', 'department', 'academic_program', 'academic_year', 'semester',
        'year_of_study', 'section', 'batch_name', 'batch_code', 'max_capacity',
        'current_count', 'is_active', 'created_at', 'updated_at'
    )
    serializer_class = StudentBatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'department', 'academic_program', 'academic_year', 'semester',
        'year_of_study', 'section', 'is_active'
    ]
    search_fields = [
        'batch_name', 'batch_code',
        'department__code', 'department__name',
        'academic_program__code', 'academic_program__name',
        'academic_year__year'
    ]
    ordering_fields = [
        'department__code', 'academic_year__year', 'year_of_study', 'semester',
        'section', 'batch_name', 'batch_code'
    ]
    ordering = ['department__code', 'academic_year__year', 'year_of_study', 'section']

    def get_queryset(self):
        qs = super().get_queryset()
        # Normalize boolean query param for is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs
