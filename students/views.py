from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model

from .models import (
    Student, StudentEnrollmentHistory, StudentDocument, CustomField, 
    StudentCustomFieldValue, StudentBatch, BulkAssignment
)
from .serializers import (
    StudentSerializer, StudentCreateSerializer, StudentUpdateSerializer,
    StudentListSerializer, StudentDetailSerializer, StudentEnrollmentHistorySerializer,
    StudentDocumentSerializer, CustomFieldSerializer, StudentCustomFieldValueSerializer,
    StudentWithCustomFieldsSerializer, StudentBatchSerializer, BulkAssignmentSerializer,
    BulkAssignmentCreateSerializer, SmartBulkAssignmentSerializer
)

User = get_user_model()


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing students
    Provides CRUD operations for students
    """
    queryset = Student.objects.select_related(
        'student_batch__department', 'student_batch__academic_program', 'student_batch__academic_year'
    )
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return StudentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StudentUpdateSerializer
        elif self.action == 'list':
            return StudentListSerializer
        elif self.action == 'retrieve':
            return StudentDetailSerializer
        return StudentSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = Student.objects.select_related(
            'student_batch__department', 'student_batch__academic_program', 'student_batch__academic_year'
        )
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(roll_number__icontains=search) |
                Q(email__icontains=search) |
                Q(father_name__icontains=search) |
                Q(mother_name__icontains=search)
            )
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by year of study
        year_filter = self.request.query_params.get('year_of_study', None)
        if year_filter:
            queryset = queryset.filter(student_batch__year_of_study=year_filter)
        
        # Filter by semester
        semester_filter = self.request.query_params.get('semester', None)
        if semester_filter:
            queryset = queryset.filter(student_batch__semester=semester_filter)
        
        # Filter by academic program
        program_filter = self.request.query_params.get('academic_program', None)
        if program_filter:
            queryset = queryset.filter(student_batch__academic_program=program_filter)
        
        # Filter by academic year
        academic_year_filter = self.request.query_params.get('academic_year', None)
        if academic_year_filter:
            queryset = queryset.filter(student_batch__academic_year=academic_year_filter)

        # Filter by gender
        gender_filter = self.request.query_params.get('gender', None)
        if gender_filter:
            queryset = queryset.filter(gender=gender_filter)
        
        # Filter by section
        section_filter = self.request.query_params.get('section', None)
        if section_filter:
            queryset = queryset.filter(student_batch__section=section_filter)
        
        # Filter by quota
        quota_filter = self.request.query_params.get('quota', None)
        if quota_filter:
            queryset = queryset.filter(quota=quota_filter)
        
        # Filter by religion
        religion_filter = self.request.query_params.get('religion', None)
        if religion_filter:
            queryset = queryset.filter(religion=religion_filter)
        
        # Filter by department
        department_filter = self.request.query_params.get('department', None)
        if department_filter:
            queryset = queryset.filter(student_batch__department=department_filter)
        
        return queryset.order_by('last_name', 'first_name')
    
    def perform_create(self, serializer):
        """Set created_by field when creating a student"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by field when updating a student"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def enrollment_history(self, request, pk=None):
        """Get enrollment history for a specific student"""
        student = self.get_object()
        history = student.enrollment_history.all()
        serializer = StudentEnrollmentHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_enrollment(self, request, pk=None):
        """Add enrollment history entry for a student"""
        student = self.get_object()
        serializer = StudentEnrollmentHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=student)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get documents for a specific student"""
        student = self.get_object()
        documents = student.documents.all()
        serializer = StudentDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload a document for a student"""
        student = self.get_object()
        serializer = StudentDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=student, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get student statistics"""
        total_students = Student.objects.count()
        active_students = Student.objects.filter(status='ACTIVE').count()
        inactive_students = Student.objects.filter(status='INACTIVE').count()
        graduated_students = Student.objects.filter(status='GRADUATED').count()
        
        # Students by year of study
        year_stats = {}
        for year, _ in Student.YEAR_OF_STUDY_CHOICES:
            count = Student.objects.filter(year_of_study=year).count()
            if count:
                year_stats[year] = count
        
        # Students by gender
        gender_stats = {}
        for gender, _ in Student.GENDER_CHOICES:
            gender_stats[gender] = Student.objects.filter(gender=gender).count()
        
        stats = {
            'total_students': total_students,
            'active_students': active_students,
            'inactive_students': inactive_students,
            'graduated_students': graduated_students,
            'year_distribution': year_stats,
            'gender_distribution': gender_stats
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        """Change student status"""
        student = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in [choice[0] for choice in Student.STATUS_CHOICES]:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student.status = new_status
        student.updated_by = request.user
        student.save()
        
        serializer = StudentSerializer(student)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def custom_fields(self, request, pk=None):
        """Get custom field values for a specific student"""
        student = self.get_object()
        custom_values = student.custom_field_values.all()
        serializer = StudentCustomFieldValueSerializer(custom_values, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Set a custom field value for a student"""
        student = self.get_object()
        custom_field_id = request.data.get('custom_field_id')
        value = request.data.get('value')
        file_value = request.FILES.get('file_value')
        
        if not custom_field_id:
            return Response(
                {'error': 'custom_field_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            custom_field = CustomField.objects.get(id=custom_field_id, is_active=True)
        except CustomField.DoesNotExist:
            return Response(
                {'error': 'Custom field not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create or update the custom field value
        custom_value, created = StudentCustomFieldValue.objects.get_or_create(
            student=student,
            custom_field=custom_field,
            defaults={'value': value, 'file_value': file_value}
        )
        
        if not created:
            custom_value.value = value
            if file_value:
                custom_value.file_value = file_value
            custom_value.save()
        
        serializer = StudentCustomFieldValueSerializer(custom_value)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def available_custom_fields(self, request):
        """Get all available custom fields"""
        custom_fields = CustomField.objects.filter(is_active=True)
        serializer = CustomFieldSerializer(custom_fields, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def divisions(self, request):
        """Get students grouped by department, program, year, semester, and section"""
        from django.db.models import Count
        from departments.models import Department
        from academics.models import AcademicProgram
        
        # Get query parameters
        department_id = request.query_params.get('department', None)
        academic_program_id = request.query_params.get('academic_program', None)
        academic_year = request.query_params.get('academic_year', None)
        year_of_study = request.query_params.get('year_of_study', None)
        semester = request.query_params.get('semester', None)
        section = request.query_params.get('section', None)
        
        # Base queryset
        queryset = Student.objects.filter(status='ACTIVE')
        
        # Apply filters
        if department_id:
            queryset = queryset.filter(student_batch__department_id=department_id)
        if academic_program_id:
            queryset = queryset.filter(student_batch__academic_program_id=academic_program_id)
        if academic_year:
            queryset = queryset.filter(student_batch__academic_year__year=academic_year)
        if year_of_study:
            queryset = queryset.filter(student_batch__year_of_study=year_of_study)
        if semester:
            queryset = queryset.filter(student_batch__semester=semester)
        if section:
            queryset = queryset.filter(student_batch__section=section)
        
        # Group students by department, program, year, semester, and section
        divisions = {}
        
        # Get all departments
        departments = Department.objects.filter(is_active=True)
        
        for dept in departments:
            dept_students = queryset.filter(student_batch__department=dept)
            if dept_students.exists():
                divisions[dept.code] = {
                    'department_id': dept.id,
                    'department_name': dept.name,
                    'department_code': dept.code,
                    'programs': {}
                }
                
                # Group by academic programs
                programs = dept_students.values_list('student_batch__academic_program', flat=True).distinct()
                for program_id in programs:
                    if program_id:
                        try:
                            program = AcademicProgram.objects.get(id=program_id)
                            program_students = dept_students.filter(student_batch__academic_program=program)
                            
                            divisions[dept.code]['programs'][program.code] = {
                                'program_id': program.id,
                                'program_name': program.name,
                                'program_code': program.code,
                                'program_level': program.level,
                                'years': {}
                            }
                            
                            # Group by academic year
                            years = program_students.values_list('student_batch__academic_year__year', flat=True).distinct()
                            for year in years:
                                if year:
                                    year_students = program_students.filter(student_batch__academic_year__year=year)
                                    divisions[dept.code]['programs'][program.code]['years'][year] = {
                                        'year_of_study': {},
                                        'total_students': year_students.count()
                                    }
                                    
                                    # Group by year of study
                                    study_years = year_students.values_list('student_batch__year_of_study', flat=True).distinct()
                                    for study_year in study_years:
                                        if study_year:
                                            study_year_students = year_students.filter(student_batch__year_of_study=study_year)
                                            divisions[dept.code]['programs'][program.code]['years'][year]['year_of_study'][study_year] = {
                                                'semesters': {},
                                                'total_students': study_year_students.count()
                                            }
                                            
                                            # Group by semester
                                            semesters = study_year_students.values_list('student_batch__semester', flat=True).distinct()
                                            for sem in semesters:
                                                if sem:
                                                    semester_students = study_year_students.filter(student_batch__semester=sem)
                                                    divisions[dept.code]['programs'][program.code]['years'][year]['year_of_study'][study_year]['semesters'][sem] = {
                                                        'sections': {},
                                                        'total_students': semester_students.count()
                                                    }
                                                    
                                                    # Group by section
                                                    sections = semester_students.values_list('student_batch__section', flat=True).distinct()
                                                    for sec in sections:
                                                        if sec:
                                                            section_students = semester_students.filter(student_batch__section=sec)
                                                            divisions[dept.code]['programs'][program.code]['years'][year]['year_of_study'][study_year]['semesters'][sem]['sections'][sec] = {
                                                                'students': StudentListSerializer(section_students, many=True).data,
                                                                'count': section_students.count()
                                                            }
                        except AcademicProgram.DoesNotExist:
                            continue
        
        return Response(divisions)
    
    @action(detail=False, methods=['post'])
    def assign_students(self, request):
        """Assign multiple students to department, program, year, semester, and section"""
        student_ids = request.data.get('student_ids', [])
        department_id = request.data.get('department_id')
        academic_program_id = request.data.get('academic_program_id')
        academic_year = request.data.get('academic_year')
        year_of_study = request.data.get('year_of_study')
        semester = request.data.get('semester')
        section = request.data.get('section')
        
        if not student_ids:
            return Response(
                {'error': 'student_ids is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate department if provided
        if department_id:
            try:
                from departments.models import Department
                Department.objects.get(id=department_id, is_active=True)
            except Department.DoesNotExist:
                return Response(
                    {'error': 'Invalid department'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate academic program if provided
        if academic_program_id:
            try:
                from academics.models import AcademicProgram
                AcademicProgram.objects.get(id=academic_program_id, is_active=True)
            except AcademicProgram.DoesNotExist:
                return Response(
                    {'error': 'Invalid academic program'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update students
        updated_students = []
        errors = []
        
        for student_id in student_ids:
            try:
                student = Student.objects.get(id=student_id)
                
                # Update fields if provided - need to create or update StudentBatch
                if any([department_id, academic_program_id, academic_year, year_of_study, semester, section]):
                    # Get or create StudentBatch
                    batch, created = StudentBatch.objects.get_or_create(
                        department_id=department_id,
                        academic_program_id=academic_program_id,
                        academic_year_id=academic_year,
                        year_of_study=year_of_study,
                        semester=semester,
                        section=section,
                        defaults={
                            'batch_name': f"{department_id}-{academic_year}-{year_of_study}-{section}",
                            'batch_code': f"{department_id}-{academic_year}-{year_of_study}-{section}",
                        }
                    )
                    student.student_batch = batch
                
                student.updated_by = request.user
                student.save()
                updated_students.append(student)
                
            except Student.DoesNotExist:
                errors.append(f'Student with id {student_id} not found')
            except Exception as e:
                errors.append(f'Error updating student {student_id}: {str(e)}')
        
        # Serialize updated students
        serializer = StudentListSerializer(updated_students, many=True)
        
        response_data = {
            'updated_students': serializer.data,
            'updated_count': len(updated_students),
            'errors': errors
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def bulk_assign_by_criteria(self, request):
        """Enhanced bulk assign students based on criteria"""
        serializer = BulkAssignmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        criteria = data['criteria']
        assignment_data = data['assignment_data']
        
        # Create bulk assignment record
        bulk_assignment = BulkAssignment.objects.create(
            operation_type=data['operation_type'],
            title=data['title'],
            description=data.get('description', ''),
            criteria=criteria,
            assignment_data=assignment_data,
            status='PROCESSING',
            started_at=timezone.now(),
            created_by=request.user
        )
        
        try:
            # Build filter criteria
            queryset = Student.objects.filter(status='ACTIVE')
            
            # Apply criteria filters
            if criteria.get('current_department'):
                queryset = queryset.filter(student_batch__department_id=criteria['current_department'])
            if criteria.get('current_academic_program'):
                queryset = queryset.filter(student_batch__academic_program_id=criteria['current_academic_program'])
            if criteria.get('current_academic_year'):
                queryset = queryset.filter(student_batch__academic_year_id=criteria['current_academic_year'])
            if criteria.get('current_year_of_study'):
                queryset = queryset.filter(student_batch__year_of_study=criteria['current_year_of_study'])
            if criteria.get('current_semester'):
                queryset = queryset.filter(student_batch__semester=criteria['current_semester'])
            if criteria.get('current_section'):
                queryset = queryset.filter(student_batch__section=criteria['current_section'])
            if criteria.get('gender'):
                queryset = queryset.filter(gender=criteria['gender'])
            if criteria.get('quota'):
                queryset = queryset.filter(quota=criteria['quota'])
            
            total_found = queryset.count()
            bulk_assignment.total_students_found = total_found
            
            # Validate assignment data
            errors = []
            if assignment_data.get('department_id'):
                try:
                    from departments.models import Department
                    Department.objects.get(id=assignment_data['department_id'], is_active=True)
                except Department.DoesNotExist:
                    errors.append('Invalid assignment department')
            
            if assignment_data.get('academic_program_id'):
                try:
                    from academics.models import AcademicProgram
                    AcademicProgram.objects.get(id=assignment_data['academic_program_id'], is_active=True)
                except AcademicProgram.DoesNotExist:
                    errors.append('Invalid assignment academic program')
            
            if errors:
                bulk_assignment.errors = errors
                bulk_assignment.status = 'FAILED'
                bulk_assignment.completed_at = timezone.now()
                bulk_assignment.save()
                return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update students
            update_fields = {}
            if assignment_data.get('department_id'):
                update_fields['department_id'] = assignment_data['department_id']
            if assignment_data.get('academic_program_id'):
                update_fields['academic_program_id'] = assignment_data['academic_program_id']
            if assignment_data.get('academic_year_id'):
                update_fields['academic_year_id'] = assignment_data['academic_year_id']
            if assignment_data.get('semester_id'):
                update_fields['semester_id'] = assignment_data['semester_id']
            if assignment_data.get('year_of_study'):
                update_fields['year_of_study'] = assignment_data['year_of_study']
            if assignment_data.get('section'):
                update_fields['section'] = assignment_data['section']
            
            update_fields['updated_by'] = request.user
            
            # Perform bulk update
            updated_count = queryset.update(**update_fields)
            
            # Update bulk assignment record
            bulk_assignment.students_updated = updated_count
            bulk_assignment.students_failed = total_found - updated_count
            bulk_assignment.status = 'COMPLETED' if updated_count == total_found else 'PARTIAL'
            bulk_assignment.completed_at = timezone.now()
            bulk_assignment.save()
            
            # Get sample updated students for response
            updated_students = queryset.all()[:50]
            student_serializer = StudentListSerializer(updated_students, many=True)
            
            response_data = {
                'bulk_assignment_id': bulk_assignment.id,
                'updated_count': updated_count,
                'total_found': total_found,
                'success_rate': bulk_assignment.success_rate,
                'sample_updated_students': student_serializer.data,
                'assignment': assignment_data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            bulk_assignment.status = 'FAILED'
            bulk_assignment.errors = [str(e)]
            bulk_assignment.completed_at = timezone.now()
            bulk_assignment.save()
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def division_statistics(self, request):
        """Get statistics for student divisions"""
        from django.db.models import Count
        from departments.models import Department
        
        # Get query parameters for filtering
        department_id = request.query_params.get('department', None)
        academic_year = request.query_params.get('academic_year', None)
        
        # Base queryset
        queryset = Student.objects.filter(status='ACTIVE')
        
        # Apply filters
        if department_id:
            queryset = queryset.filter(student_batch__department_id=department_id)
        if academic_year:
            queryset = queryset.filter(student_batch__academic_year__year=academic_year)
        
        data = {
            'by_department': list(
                queryset.values('student_batch__department__id','student_batch__department__code','student_batch__department__name')
                        .annotate(total=Count('id'))
                        .order_by('student_batch__department__code')
            ),
            'by_academic_year': list(
                queryset.values('student_batch__academic_year__year').annotate(total=Count('id')).order_by('student_batch__academic_year__year')
            ),
            'by_year_of_study': list(
                queryset.values('student_batch__year_of_study').annotate(total=Count('id')).order_by('student_batch__year_of_study')
            ),
            'by_semester': list(
                queryset.values('student_batch__semester').annotate(total=Count('id')).order_by('student_batch__semester')
            ),
            'by_section': list(
                queryset.values('student_batch__section').annotate(total=Count('id')).order_by('student_batch__section')
            ),
            'total_students': queryset.count(),
        }
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def smart_bulk_assign(self, request):
        """Smart bulk assignment with automatic section management"""
        serializer = SmartBulkAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        student_ids = data['student_ids']
        auto_assign_sections = data['auto_assign_sections']
        max_students_per_section = data['max_students_per_section']
        strategy = data['section_assignment_strategy']
        
        # Get students
        students = Student.objects.filter(id__in=student_ids, status='ACTIVE')
        if not students.exists():
            return Response(
                {'error': 'No active students found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare assignment data
        assignment_fields = {}
        if data.get('department_id'):
            assignment_fields['department_id'] = data['department_id']
        if data.get('academic_program_id'):
            assignment_fields['academic_program_id'] = data['academic_program_id']
        if data.get('academic_year_id'):
            assignment_fields['academic_year_id'] = data['academic_year_id']
        if data.get('semester_id'):
            assignment_fields['semester_id'] = data['semester_id']
        if data.get('year_of_study'):
            assignment_fields['year_of_study'] = data['year_of_study']
        
        # Handle section assignment
        if auto_assign_sections and not data.get('section'):
            sections = self._assign_sections_to_students(
                students, max_students_per_section, strategy, assignment_fields
            )
        else:
            if data.get('section'):
                assignment_fields['section'] = data['section']
            sections = {data.get('section', 'A'): list(students)}
        
        # Update students
        updated_students = []
        errors = []
        
        for section, section_students in sections.items():
            for student in section_students:
                try:
                    # Update student
                    for field, value in assignment_fields.items():
                        setattr(student, field, value)
                    student.section = section
                    student.updated_by = request.user
                    student.save()
                    updated_students.append(student)
                except Exception as e:
                    errors.append(f'Error updating student {student.roll_number}: {str(e)}')
        
        # Serialize results
        student_serializer = StudentListSerializer(updated_students, many=True)
        
        response_data = {
            'updated_count': len(updated_students),
            'total_students': len(student_ids),
            'errors': errors,
            'section_distribution': {section: len(students) for section, students in sections.items()},
            'updated_students': student_serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _assign_sections_to_students(self, students, max_per_section, strategy, assignment_fields):
        """Assign students to sections based on strategy"""
        from collections import defaultdict
        
        # Get existing section counts for the same department/year/semester
        existing_counts = defaultdict(int)
        if assignment_fields.get('department_id') and assignment_fields.get('academic_year_id'):
            existing_students = Student.objects.filter(
                department_id=assignment_fields['department_id'],
                academic_year_id=assignment_fields['academic_year_id'],
                status='ACTIVE'
            )
            if assignment_fields.get('year_of_study'):
                existing_students = existing_students.filter(year_of_study=assignment_fields['year_of_study'])
            if assignment_fields.get('semester_id'):
                existing_students = existing_students.filter(semester_id=assignment_fields['semester_id'])
            
            for student in existing_students:
                if student.section:
                    existing_counts[student.section] += 1
        
        # Available sections (A-T)
        available_sections = [chr(i) for i in range(ord('A'), ord('T') + 1)]
        
        # Assign students to sections
        sections = defaultdict(list)
        student_list = list(students)
        
        if strategy == 'ROUND_ROBIN':
            section_index = 0
            for student in student_list:
                # Find section with available capacity
                while (existing_counts[available_sections[section_index]] + 
                       len(sections[available_sections[section_index]]) >= max_per_section):
                    section_index = (section_index + 1) % len(available_sections)
                
                sections[available_sections[section_index]].append(student)
                section_index = (section_index + 1) % len(available_sections)
        
        elif strategy == 'BALANCED':
            # Sort sections by current load
            sorted_sections = sorted(available_sections, 
                                   key=lambda s: existing_counts[s] + len(sections[s]))
            
            for student in student_list:
                # Find section with least load
                for section in sorted_sections:
                    if (existing_counts[section] + len(sections[section])) < max_per_section:
                        sections[section].append(student)
                        break
        
        else:  # SEQUENTIAL
            current_section = 'A'
            for student in student_list:
                # Check if current section has capacity
                if (existing_counts[current_section] + len(sections[current_section])) >= max_per_section:
                    # Move to next section
                    current_section = chr(ord(current_section) + 1)
                    if current_section > 'T':
                        current_section = 'A'  # Wrap around
                
                sections[current_section].append(student)
        
        return dict(sections)


class StudentEnrollmentHistoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student enrollment history"""
    queryset = StudentEnrollmentHistory.objects.all()
    serializer_class = StudentEnrollmentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter by student if provided"""
        queryset = StudentEnrollmentHistory.objects.all()
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        return queryset.order_by('-enrollment_date')


class StudentDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student documents"""
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Filter by student if provided"""
        queryset = StudentDocument.objects.all()
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        document_type = self.request.query_params.get('document_type', None)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Set uploaded_by field when creating a document"""
        serializer.save(uploaded_by=self.request.user)


class CustomFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom fields"""
    queryset = CustomField.objects.filter(is_active=True)
    serializer_class = CustomFieldSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter by field type if provided"""
        queryset = CustomField.objects.filter(is_active=True)
        field_type = self.request.query_params.get('field_type', None)
        if field_type:
            queryset = queryset.filter(field_type=field_type)
        return queryset.order_by('order', 'name')


class StudentCustomFieldValueViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student custom field values"""
    queryset = StudentCustomFieldValue.objects.all()
    serializer_class = StudentCustomFieldValueSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        """Filter by student if provided"""
        queryset = StudentCustomFieldValue.objects.all()
        student_id = self.request.query_params.get('student', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        custom_field_id = self.request.query_params.get('custom_field', None)
        if custom_field_id:
            queryset = queryset.filter(custom_field_id=custom_field_id)
        
        return queryset.order_by('custom_field__order', 'custom_field__name')


class StudentBatchViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student batches"""
    queryset = StudentBatch.objects.all()
    serializer_class = StudentBatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter batches based on query parameters"""
        queryset = StudentBatch.objects.select_related(
            'department', 'academic_program', 'academic_year'
        )
        
        # Filter by department
        department_id = self.request.query_params.get('department', None)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Filter by academic program
        program_id = self.request.query_params.get('academic_program', None)
        if program_id:
            queryset = queryset.filter(academic_program_id=program_id)
        
        # Filter by academic year
        year_id = self.request.query_params.get('academic_year', None)
        if year_id:
            queryset = queryset.filter(academic_year_id=year_id)
        
        # Filter by semester (using the semester string field)
        semester = self.request.query_params.get('semester', None)
        if semester:
            queryset = queryset.filter(semester=semester)
        
        # Filter by year of study
        year_of_study = self.request.query_params.get('year_of_study', None)
        if year_of_study:
            queryset = queryset.filter(year_of_study=year_of_study)
        
        # Filter by section
        section = self.request.query_params.get('section', None)
        if section:
            queryset = queryset.filter(section=section)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('department', 'academic_year', 'year_of_study', 'section')
    
    def perform_create(self, serializer):
        """Set created_by field when creating a batch"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_student_count(self, request, pk=None):
        """Update the student count for this batch"""
        batch = self.get_object()
        batch.update_student_count()
        serializer = self.get_serializer(batch)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def capacity_report(self, request):
        """Get capacity report for all batches"""
        from django.db.models import Count, Avg
        
        batches = self.get_queryset()
        
        total_batches = batches.count()
        full_batches = batches.filter(current_count__gte=models.F('max_capacity')).count()
        available_capacity = sum(batch.get_available_capacity() for batch in batches)
        total_capacity = sum(batch.max_capacity for batch in batches)
        total_students = sum(batch.current_count for batch in batches)
        
        # Average utilization
        avg_utilization = (total_students / total_capacity * 100) if total_capacity > 0 else 0
        
        # Department-wise breakdown
        dept_breakdown = {}
        for batch in batches:
            dept_code = batch.department.code
            if dept_code not in dept_breakdown:
                dept_breakdown[dept_code] = {
                    'department_name': batch.department.name,
                    'total_batches': 0,
                    'total_capacity': 0,
                    'total_students': 0,
                    'full_batches': 0
                }
            
            dept_breakdown[dept_code]['total_batches'] += 1
            dept_breakdown[dept_code]['total_capacity'] += batch.max_capacity
            dept_breakdown[dept_code]['total_students'] += batch.current_count
            if batch.is_full():
                dept_breakdown[dept_code]['full_batches'] += 1
        
        response_data = {
            'summary': {
                'total_batches': total_batches,
                'full_batches': full_batches,
                'available_capacity': available_capacity,
                'total_capacity': total_capacity,
                'total_students': total_students,
                'average_utilization': round(avg_utilization, 2)
            },
            'department_breakdown': dept_breakdown
        }
        
        return Response(response_data)


class BulkAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing bulk assignment operations"""
    queryset = BulkAssignment.objects.all()
    serializer_class = BulkAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter bulk assignments based on query parameters"""
        queryset = BulkAssignment.objects.select_related('created_by')
        
        # Filter by operation type
        operation_type = self.request.query_params.get('operation_type', None)
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by created by
        created_by = self.request.query_params.get('created_by', None)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed information about a bulk assignment operation"""
        bulk_assignment = self.get_object()
        
        # Get sample of affected students
        criteria = bulk_assignment.criteria
        queryset = Student.objects.filter(status='ACTIVE')
        
        # Apply same criteria as the original operation
        if criteria.get('current_department'):
            queryset = queryset.filter(department_id=criteria['current_department'])
        if criteria.get('current_academic_program'):
            queryset = queryset.filter(academic_program_id=criteria['current_academic_program'])
        if criteria.get('current_academic_year'):
            queryset = queryset.filter(academic_year_id=criteria['current_academic_year'])
        if criteria.get('current_year_of_study'):
            queryset = queryset.filter(year_of_study=criteria['current_year_of_study'])
        if criteria.get('current_semester'):
            queryset = queryset.filter(semester_id=criteria['current_semester'])
        if criteria.get('current_section'):
            queryset = queryset.filter(section=criteria['current_section'])
        if criteria.get('gender'):
            queryset = queryset.filter(gender=criteria['gender'])
        if criteria.get('quota'):
            queryset = queryset.filter(quota=criteria['quota'])
        
        # Get sample students
        sample_students = queryset[:20]
        student_serializer = StudentListSerializer(sample_students, many=True)
        
        response_data = {
            'bulk_assignment': BulkAssignmentSerializer(bulk_assignment).data,
            'criteria': criteria,
            'assignment_data': bulk_assignment.assignment_data,
            'sample_affected_students': student_serializer.data,
            'total_affected_students': queryset.count()
        }
        
        return Response(response_data)


# Additional utility views for frontend
def student_dashboard(request):
    """Dashboard view for student management"""
    if not request.user.is_authenticated:
        return render(request, 'registration/login.html')
    
    context = {
        'total_students': Student.objects.count(),
        'active_students': Student.objects.filter(status='ACTIVE').count(),
        'recent_students': Student.objects.order_by('-created_at')[:5]
    }
    return render(request, 'students/dashboard.html', context)


def student_list_view(request):
    """List view for students"""
    if not request.user.is_authenticated:
        return render(request, 'registration/login.html')
    
    students = Student.objects.all().order_by('last_name', 'first_name')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    context = {
        'students': students,
        'search_query': search_query
    }
    return render(request, 'students/student_list.html', context)


def student_detail_view(request, student_id):
    """Detail view for a specific student"""
    if not request.user.is_authenticated:
        return render(request, 'registration/login.html')
    
    student = get_object_or_404(Student, pk=student_id)
    context = {
        'student': student,
        'enrollment_history': student.enrollment_history.all(),
        'documents': student.documents.all()
    }
    return render(request, 'students/student_detail.html', context)
