from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from students.models import Semester
from .models import GradeScale, MidTermGrade, SemesterGrade, SemesterGPA, CumulativeGPA
from .serializers import (
    GradeScaleSerializer,
    MidTermGradeSerializer,
    SemesterGradeSerializer,
    SemesterGPASerializer,
    CumulativeGPASerializer,
)


def health(request):
    return JsonResponse({"status": "ok", "app": "grads"})


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class IsFacultyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.is_superuser


class IsAssignedFacultyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True
        # Allow only the faculty assigned to the course section to write
        section = obj.course_section
        faculty_user = getattr(section.faculty, 'user', None)
        if request.method in permissions.SAFE_METHODS:
            return True
        return faculty_user and faculty_user.id == request.user.id


class GradeScaleViewSet(viewsets.ModelViewSet):
    queryset = GradeScale.objects.all().order_by('-grade_points')
    serializer_class = GradeScaleSerializer
    permission_classes = [IsFacultyOrAdmin]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['grade_points', 'letter', 'min_score', 'max_score']
    ordering = ['-grade_points']


class MidTermGradeViewSet(viewsets.ModelViewSet):
    queryset = MidTermGrade.objects.select_related('student', 'course_section', 'semester').order_by('-evaluated_at')
    serializer_class = MidTermGradeSerializer
    permission_classes = [IsAssignedFacultyOrAdmin]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['evaluated_at', 'midterm_marks', 'percentage', 'midterm_grade']
    ordering = ['-evaluated_at']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_student(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter is required'}, status=400)
        
        qs = self.get_queryset()
        qs = qs.filter(student_id=student_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        qs = self._filtered_queryset(request)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def _filtered_queryset(self, request):
        qs = self.get_queryset()
        params = request.query_params
        
        if 'student' in params:
            qs = qs.filter(student_id=params.get('student'))
        if 'semester' in params:
            qs = qs.filter(semester_id=params.get('semester'))
        if 'course' in params:
            qs = qs.filter(course_section__course_id=params.get('course'))
        if 'department' in params:
            qs = qs.filter(course_section__course__department__code__iexact=params.get('department'))
        
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAssignedFacultyOrAdmin])
    def bulk_upsert(self, request):
        """Bulk create or update mid-term grades."""
        data = request.data
        if not isinstance(data, list):
            return Response({'detail': 'Expected a list of mid-term grades.'}, status=status.HTTP_400_BAD_REQUEST)
        
        created, updated, errors = 0, 0, []
        for idx, item in enumerate(data):
            serializer = self.get_serializer(data=item, context={'request': request})
            if serializer.is_valid():
                # Try to find existing by unique key (student, course_section, semester)
                student = serializer.validated_data['student']
                course_section = serializer.validated_data['course_section']
                semester = serializer.validated_data['semester']
                
                obj, existed = MidTermGrade.objects.get_or_create(
                    student=student, 
                    course_section=course_section, 
                    semester=semester,
                    defaults={
                        'midterm_marks': serializer.validated_data.get('midterm_marks', 0),
                        'evaluator': request.user if request.user.is_authenticated else None,
                    }
                )
                
                if existed:
                    # Update existing
                    obj.midterm_marks = serializer.validated_data.get('midterm_marks', obj.midterm_marks)
                    obj.evaluator = request.user if request.user.is_authenticated else obj.evaluator
                    obj.save()
                    updated += 1
                else:
                    created += 1
            else:
                errors.append({'index': idx, 'errors': serializer.errors})
        
        return Response({'created': created, 'updated': updated, 'errors': errors})


class SemesterGradeViewSet(viewsets.ModelViewSet):
    queryset = SemesterGrade.objects.select_related('student', 'course_section', 'semester').order_by('-evaluated_at')
    serializer_class = SemesterGradeSerializer
    permission_classes = [IsAssignedFacultyOrAdmin]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['evaluated_at', 'final_marks', 'percentage', 'final_grade']
    ordering = ['-evaluated_at']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_student(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter is required'}, status=400)
        
        qs = self.get_queryset()
        qs = qs.filter(student_id=student_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        qs = self._filtered_queryset(request)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def _filtered_queryset(self, request):
        qs = self.get_queryset()
        params = request.query_params
        
        if 'student' in params:
            qs = qs.filter(student_id=params.get('student'))
        if 'semester' in params:
            qs = qs.filter(semester_id=params.get('semester'))
        if 'course' in params:
            qs = qs.filter(course_section__course_id=params.get('course'))
        if 'department' in params:
            qs = qs.filter(course_section__course__department__code__iexact=params.get('department'))
        if 'passed' in params:
            val = params.get('passed').lower() in ['1', 'true', 'yes']
            qs = qs.filter(passed=val)
        
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAssignedFacultyOrAdmin])
    def bulk_upsert(self, request):
        """Bulk create or update semester grades."""
        data = request.data
        if not isinstance(data, list):
            return Response({'detail': 'Expected a list of semester grades.'}, status=status.HTTP_400_BAD_REQUEST)
        
        created, updated, errors = 0, 0, []
        for idx, item in enumerate(data):
            serializer = self.get_serializer(data=item, context={'request': request})
            if serializer.is_valid():
                # Try to find existing by unique key (student, course_section, semester)
                student = serializer.validated_data['student']
                course_section = serializer.validated_data['course_section']
                semester = serializer.validated_data['semester']
                
                obj, existed = SemesterGrade.objects.get_or_create(
                    student=student, 
                    course_section=course_section, 
                    semester=semester,
                    defaults={
                        'final_marks': serializer.validated_data.get('final_marks', 0),
                        'evaluator': request.user if request.user.is_authenticated else None,
                    }
                )
                
                if existed:
                    # Update existing
                    obj.final_marks = serializer.validated_data.get('final_marks', obj.final_marks)
                    obj.evaluator = request.user if request.user.is_authenticated else obj.evaluator
                    obj.save()
                    updated += 1
                else:
                    created += 1
                    
                # Update semester SGPA and cumulative CGPA after grade change
                semester_gpa, _ = SemesterGPA.objects.get_or_create(
                    student=student, 
                    semester=semester
                )
                semester_gpa.recalculate()
                # Update cumulative CGPA
                cumulative_gpa, _ = CumulativeGPA.objects.get_or_create(student=student)
                cumulative_gpa.recalculate()
            else:
                errors.append({'index': idx, 'errors': serializer.errors})
        
        return Response({'created': created, 'updated': updated, 'errors': errors})


class SemesterGPAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SemesterGPA.objects.select_related('student', 'semester').order_by('-updated_at')
    serializer_class = SemesterGPASerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['updated_at', 'sgpa', 'total_credits', 'academic_standing']
    ordering = ['-updated_at']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_student(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter is required'}, status=400)
        
        qs = self.get_queryset()
        qs = qs.filter(student_id=student_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class CumulativeGPAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CumulativeGPA.objects.select_related('student').order_by('-updated_at')
    serializer_class = CumulativeGPASerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['updated_at', 'cgpa', 'total_credits_earned', 'classification']
    ordering = ['-updated_at']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_student(self, request):
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter is required'}, status=400)
        
        qs = self.get_queryset()
        qs = qs.filter(student_id=student_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def academic_transcript(self, request):
        """Generate comprehensive academic transcript for a student."""
        student_id = request.query_params.get('student')
        if not student_id:
            return Response({'error': 'student parameter is required'}, status=400)
        
        try:
            cgpa = CumulativeGPA.objects.get(student_id=student_id)
        except CumulativeGPA.DoesNotExist:
            return Response({'error': 'No CGPA record found for this student'}, status=404)
        
        student = cgpa.student
        
        # Get all semester GPAs
        semester_gpas = SemesterGPA.objects.filter(student=student).select_related('semester').order_by('semester__academic_year__year')
        
        # Get all semester grades
        semester_grades = SemesterGrade.objects.filter(student=student).select_related('semester', 'course_section', 'course_section__course').order_by('semester__academic_year__year')
        
        transcript_data = {
            'student': {
                'id': student.id,
                'roll_number': student.roll_number,
                'name': f"{student.first_name} {student.last_name}",
            },
            'cgpa': {
                'value': cgpa.cgpa,
                'classification': cgpa.get_classification_display(),
                'total_credits_earned': cgpa.total_credits_earned,
                'is_eligible_for_graduation': cgpa.is_eligible_for_graduation,
            },
            'semesters': []
        }
        
        for sgpa in semester_gpas:
            semester_data = {
                'semester': {
                    'id': sgpa.semester.id,
                    'name': str(sgpa.semester),
                    'academic_year': sgpa.semester.academic_year.year,
                },
                'sgpa': {
                    'value': sgpa.sgpa,
                    'academic_standing': sgpa.get_academic_standing_display(),
                    'total_credits': sgpa.total_credits,
                },
                'courses': []
            }
            
            # Get courses for this semester
            semester_courses = semester_grades.filter(semester=sgpa.semester)
            for grade in semester_courses:
                course_data = {
                    'course_code': grade.course_section.course.code,
                    'course_title': grade.course_section.course.title,
                    'credits': grade.course_section.course.credits,
                    'marks_obtained': grade.final_marks,
                    'total_marks': grade.total_marks,
                    'percentage': grade.percentage,
                    'grade': grade.final_grade,
                    'grade_points': grade.final_grade_points,
                    'passed': grade.passed,
                }
                semester_data['courses'].append(course_data)
            
            transcript_data['semesters'].append(semester_data)
        
        return Response(transcript_data)