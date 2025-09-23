"""
API Views for Dynamic Dropdown Support
Provides endpoints for filtering dropdowns in admin forms
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from students.models import AcademicYear, Semester
from academics.models import CourseSection
from .models import TimetableSlot, AttendanceSession


class DropdownAPIViewSet(viewsets.ViewSet):
    """API endpoints for dynamic dropdown filtering"""
    
    @action(detail=False, methods=['get'])
    def semesters_by_academic_year(self, request):
        """Get semesters filtered by academic year"""
        academic_year_id = request.query_params.get('academic_year')
        
        if not academic_year_id:
            return Response(
                {'error': 'academic_year parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            semesters = Semester.objects.filter(
                academic_year_id=academic_year_id,
                is_active=True
            ).order_by('-semester_type', 'name')
            
            data = []
            for semester in semesters:
                data.append({
                    'id': semester.id,
                    'name': semester.name,
                    'semester_type': semester.semester_type,
                    'display_name': f"{semester.name} ({semester.semester_type})"
                })
            
            return Response({'results': data})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def course_sections_by_period(self, request):
        """Get course sections filtered by academic period"""
        academic_period_id = request.query_params.get('academic_period')
        
        if not academic_period_id:
            return Response(
                {'error': 'academic_period parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            course_sections = CourseSection.objects.filter(
                is_active=True
            ).order_by('course__code', 'section_type')
            
            data = []
            for section in course_sections:
                data.append({
                    'id': section.id,
                    'code': section.course.code if hasattr(section, 'course') else 'N/A',
                    'section_type': section.section_type,
                    'display_name': f"{section.course.code if hasattr(section, 'course') else 'N/A'} - {section.section_type}"
                })
            
            return Response({'results': data})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def timetable_slots_by_period(self, request):
        """Get timetable slots filtered by academic period"""
        academic_period_id = request.query_params.get('academic_period')
        
        if not academic_period_id:
            return Response(
                {'error': 'academic_period parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            timetable_slots = TimetableSlot.objects.filter(
                academic_period_id=academic_period_id,
                is_active=True
            ).select_related('course_section', 'faculty').order_by(
                'day_of_week', 'start_time'
            )
            
            data = []
            for slot in timetable_slots:
                data.append({
                    'id': slot.id,
                    'course_section_name': str(slot.course_section),
                    'day_name': slot.get_day_of_week_display(),
                    'start_time': slot.start_time.strftime('%H:%M'),
                    'end_time': slot.end_time.strftime('%H:%M'),
                    'display_name': f"{slot.course_section} - {slot.get_day_of_week_display()} {slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}"
                })
            
            return Response({'results': data})
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def session_students(self, request, pk=None):
        """Get students for a specific attendance session"""
        try:
            session = AttendanceSession.objects.get(pk=pk)
            
            # Get students from the course section's student batch
            students = []
            if (session.course_section and 
                session.course_section.student_batch):
                students = session.course_section.student_batch.students.filter(
                    is_active=True
                ).order_by('roll_number')
            
            data = []
            for student in students:
                data.append({
                    'id': student.id,
                    'roll_number': student.roll_number,
                    'full_name': student.full_name,
                    'display_name': f"{student.roll_number} - {student.full_name}"
                })
            
            return Response({'students': data})
            
        except AttendanceSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
