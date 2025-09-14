from datetime import date

from django.db.models import Prefetch
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AttendanceSession, AttendanceRecord
from .serializers import AttendanceSessionSerializer, AttendanceRecordSerializer
from academics.models import Timetable, CourseEnrollment
from students.models import Student


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    queryset = AttendanceSession.objects.all().select_related('course_section', 'timetable').prefetch_related(
        Prefetch('records', queryset=AttendanceRecord.objects.select_related('student'))
    )
    serializer_class = AttendanceSessionSerializer

    @action(detail=True, methods=['post'])
    def generate_records(self, request, pk=None):
        session = self.get_object()
        enrollments = CourseEnrollment.objects.filter(course_section=session.course_section, status='ENROLLED').select_related('student')
        created = 0
        for enrollment in enrollments:
            AttendanceRecord.objects.get_or_create(session=session, student=enrollment.student)
            created += 1
        return Response({
            'created_records': created,
            'total_records': session.records.count(),
        }, status=status.HTTP_200_OK)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all().select_related('session', 'student')
    serializer_class = AttendanceRecordSerializer


@csrf_exempt
@require_http_methods(["GET"])
def get_students_for_session(request):
    """AJAX view to get students filtered by attendance session"""
    session_id = request.GET.get('session_id')
    
    if not session_id:
        return JsonResponse({'students': []})
    
    try:
        session = AttendanceSession.objects.select_related('course_section__student_batch').get(id=session_id)
    except AttendanceSession.DoesNotExist:
        return JsonResponse({'students': []})
    
    students = []
    
    if session.course_section and session.course_section.student_batch:
        # Only get students from the specific student batch assigned to this course section
        batch_students = Student.objects.filter(
            student_batch=session.course_section.student_batch
        ).order_by('roll_number')
        
        students = [
            {
                'id': student.id,
                'roll_number': student.roll_number,
                'full_name': student.full_name
            }
            for student in batch_students
        ]
    
    return JsonResponse({'students': students})

