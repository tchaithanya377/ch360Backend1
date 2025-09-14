from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO
import json

from .models import (
    ExamSession, ExamSchedule, ExamRoom, ExamRoomAllocation,
    ExamStaffAssignment, StudentDue, ExamRegistration, HallTicket,
    ExamAttendance, ExamViolation, ExamResult
)
from .serializers import (
    ExamSessionSerializer, ExamScheduleSerializer, ExamRoomSerializer,
    ExamRoomAllocationSerializer, ExamStaffAssignmentSerializer, StudentDueSerializer,
    ExamRegistrationSerializer, HallTicketSerializer, ExamAttendanceSerializer,
    ExamViolationSerializer, ExamResultSerializer, ExamSessionSummarySerializer,
    ExamScheduleDetailSerializer, ExamRegistrationDetailSerializer,
    HallTicketDetailSerializer, StudentDueSummarySerializer
)


class ExamSessionViewSet(viewsets.ModelViewSet):
    queryset = ExamSession.objects.all()
    serializer_class = ExamSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session_type', 'academic_year', 'semester', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-academic_year', '-semester', '-start_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ExamSessionSummarySerializer
        return ExamSessionSerializer
    
    @action(detail=True, methods=['get'])
    def exam_schedules(self, request, pk=None):
        """Get all exam schedules for a specific session"""
        session = self.get_object()
        schedules = ExamSchedule.objects.filter(exam_session=session)
        serializer = ExamScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a specific exam session"""
        session = self.get_object()
        
        stats = {
            'total_exams': session.exam_schedules.count(),
            'total_registrations': sum(exam.registrations.count() for exam in session.exam_schedules.all()),
            'total_students': session.exam_schedules.aggregate(
                total_students=Count('registrations__student', distinct=True)
            )['total_students'] or 0,
            'completed_exams': session.exam_schedules.filter(status='COMPLETED').count(),
            'ongoing_exams': session.exam_schedules.filter(status='ONGOING').count(),
            'upcoming_exams': session.exam_schedules.filter(status='SCHEDULED').count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def active_sessions(self, request):
        """Get all active exam sessions"""
        active_sessions = ExamSession.objects.filter(is_active=True, status__in=['PUBLISHED', 'ONGOING'])
        serializer = self.get_serializer(active_sessions, many=True)
        return Response(serializer.data)


class ExamScheduleViewSet(viewsets.ModelViewSet):
    queryset = ExamSchedule.objects.all()
    serializer_class = ExamScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam_session', 'exam_type', 'status', 'is_online', 'course']
    search_fields = ['title', 'description', 'course__code', 'course__title']
    ordering_fields = ['exam_date', 'start_time', 'created_at']
    ordering = ['exam_date', 'start_time']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExamScheduleDetailSerializer
        return ExamScheduleSerializer
    
    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """Get all registrations for a specific exam schedule"""
        exam_schedule = self.get_object()
        registrations = ExamRegistration.objects.filter(exam_schedule=exam_schedule)
        serializer = ExamRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def room_allocations(self, request, pk=None):
        """Get room allocations for a specific exam schedule"""
        exam_schedule = self.get_object()
        allocations = ExamRoomAllocation.objects.filter(exam_schedule=exam_schedule)
        serializer = ExamRoomAllocationSerializer(allocations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def staff_assignments(self, request, pk=None):
        """Get staff assignments for a specific exam schedule"""
        exam_schedule = self.get_object()
        assignments = ExamStaffAssignment.objects.filter(exam_schedule=exam_schedule)
        serializer = ExamStaffAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start_exam(self, request, pk=None):
        """Start an exam (change status to ONGOING)"""
        exam_schedule = self.get_object()
        if exam_schedule.status != 'SCHEDULED':
            return Response(
                {'error': 'Exam can only be started if it is in SCHEDULED status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exam_schedule.status = 'ONGOING'
        exam_schedule.save()
        serializer = self.get_serializer(exam_schedule)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def end_exam(self, request, pk=None):
        """End an exam (change status to COMPLETED)"""
        exam_schedule = self.get_object()
        if exam_schedule.status != 'ONGOING':
            return Response(
                {'error': 'Exam can only be ended if it is ONGOING'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exam_schedule.status = 'COMPLETED'
        exam_schedule.save()
        serializer = self.get_serializer(exam_schedule)
        return Response(serializer.data)


class ExamRoomViewSet(viewsets.ModelViewSet):
    queryset = ExamRoom.objects.all()
    serializer_class = ExamRoomSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['room_type', 'building', 'floor', 'is_accessible', 'is_active']
    search_fields = ['name', 'building', 'description']
    ordering_fields = ['building', 'floor', 'name', 'capacity']
    ordering = ['building', 'floor', 'name']
    
    @action(detail=True, methods=['get'])
    def exam_allocations(self, request, pk=None):
        """Get all exam allocations for a specific room"""
        room = self.get_object()
        allocations = ExamRoomAllocation.objects.filter(exam_room=room)
        serializer = ExamRoomAllocationSerializer(allocations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Check room availability for a specific date range"""
        room = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Both start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for conflicting exam allocations
        conflicting_allocations = ExamRoomAllocation.objects.filter(
            exam_room=room,
            exam_schedule__exam_date__range=[start_date, end_date]
        )
        
        availability = {
            'room': room.name,
            'start_date': start_date,
            'end_date': end_date,
            'is_available': not conflicting_allocations.exists(),
            'conflicting_exams': [
                {
                    'exam': allocation.exam_schedule.title,
                    'date': allocation.exam_schedule.exam_date
                }
                for allocation in conflicting_allocations
            ]
        }
        
        return Response(availability)


class ExamRoomAllocationViewSet(viewsets.ModelViewSet):
    queryset = ExamRoomAllocation.objects.all()
    serializer_class = ExamRoomAllocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam_schedule', 'exam_room', 'is_primary']
    search_fields = ['exam_schedule__title', 'exam_room__name', 'notes']
    ordering = ['-created_at']


class ExamStaffAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ExamStaffAssignment.objects.all()
    serializer_class = ExamStaffAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam_schedule', 'faculty', 'role', 'exam_room', 'is_available']
    search_fields = ['faculty__user__first_name', 'faculty__user__last_name', 'notes']
    ordering = ['-assigned_date']
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Toggle staff availability for exam duty"""
        assignment = self.get_object()
        assignment.is_available = not assignment.is_available
        assignment.save()
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)


class StudentDueViewSet(viewsets.ModelViewSet):
    queryset = StudentDue.objects.all()
    serializer_class = StudentDueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'due_type', 'status', 'due_date']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'description']
    ordering_fields = ['due_date', 'amount', 'created_at']
    ordering = ['-due_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StudentDueSummarySerializer
        return StudentDueSerializer
    
    @action(detail=False, methods=['get'])
    def overdue_dues(self, request):
        """Get all overdue dues"""
        overdue_dues = StudentDue.objects.filter(
            due_date__lt=timezone.now().date(),
            status='PENDING'
        )
        serializer = self.get_serializer(overdue_dues, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def student_dues(self, request):
        """Get dues for a specific student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student_dues = StudentDue.objects.filter(student_id=student_id)
        serializer = self.get_serializer(student_dues, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_payment(self, request, pk=None):
        """Update payment for a due"""
        due = self.get_object()
        payment_amount = request.data.get('payment_amount', 0)
        
        if payment_amount <= 0:
            return Response(
                {'error': 'Payment amount must be positive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        due.paid_amount += payment_amount
        if due.paid_amount >= due.amount:
            due.status = 'PAID'
        elif due.paid_amount > 0:
            due.status = 'PARTIAL'
        
        due.save()
        serializer = self.get_serializer(due)
        return Response(serializer.data)


class ExamRegistrationViewSet(viewsets.ModelViewSet):
    queryset = ExamRegistration.objects.all()
    serializer_class = ExamRegistrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'exam_schedule', 'status', 'exam_schedule__exam_session']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name']
    ordering_fields = ['registration_date', 'approved_date']
    ordering = ['-registration_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ExamRegistrationDetailSerializer
        return ExamRegistrationSerializer
    
    @action(detail=True, methods=['post'])
    def approve_registration(self, request, pk=None):
        """Approve a student's exam registration"""
        registration = self.get_object()
        if registration.status != 'PENDING':
            return Response(
                {'error': 'Registration can only be approved if it is pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration.status = 'APPROVED'
        registration.approved_by = request.user.faculty
        registration.approved_date = timezone.now()
        registration.save()
        
        serializer = self.get_serializer(registration)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject_registration(self, request, pk=None):
        """Reject a student's exam registration"""
        registration = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response(
                {'error': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        registration.status = 'REJECTED'
        registration.rejection_reason = rejection_reason
        registration.save()
        
        serializer = self.get_serializer(registration)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get all pending registrations that need approval"""
        pending_registrations = ExamRegistration.objects.filter(status='PENDING')
        serializer = self.get_serializer(pending_registrations, many=True)
        return Response(serializer.data)


class HallTicketViewSet(viewsets.ModelViewSet):
    queryset = HallTicket.objects.all()
    serializer_class = HallTicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'exam_room', 'exam_registration__exam_schedule']
    search_fields = ['ticket_number', 'exam_registration__student__roll_number']
    ordering_fields = ['generated_date', 'printed_date', 'issued_date']
    ordering = ['-generated_date']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return HallTicketDetailSerializer
        return HallTicketSerializer
    
    @action(detail=True, methods=['post'])
    def print_ticket(self, request, pk=None):
        """Mark hall ticket as printed"""
        hall_ticket = self.get_object()
        hall_ticket.status = 'PRINTED'
        hall_ticket.printed_date = timezone.now()
        hall_ticket.save()
        
        serializer = self.get_serializer(hall_ticket)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def issue_ticket(self, request, pk=None):
        """Issue hall ticket to student"""
        hall_ticket = self.get_object()
        hall_ticket.status = 'ISSUED'
        hall_ticket.issued_date = timezone.now()
        hall_ticket.save()
        
        serializer = self.get_serializer(hall_ticket)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download hall ticket as PDF"""
        hall_ticket = self.get_object()
        
        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content to PDF
        p.drawString(100, 750, f"HALL TICKET")
        p.drawString(100, 720, f"Ticket Number: {hall_ticket.ticket_number}")
        p.drawString(100, 690, f"Student: {hall_ticket.exam_registration.student.get_full_name()}")
        p.drawString(100, 660, f"Roll Number: {hall_ticket.exam_registration.student.roll_number}")
        p.drawString(100, 630, f"Exam: {hall_ticket.exam_registration.exam_schedule.title}")
        p.drawString(100, 600, f"Course: {hall_ticket.exam_registration.exam_schedule.course.code}")
        p.drawString(100, 570, f"Date: {hall_ticket.exam_registration.exam_schedule.exam_date}")
        p.drawString(100, 540, f"Time: {hall_ticket.exam_registration.exam_schedule.start_time} - {hall_ticket.exam_registration.exam_schedule.end_time}")
        
        if hall_ticket.exam_room:
            p.drawString(100, 510, f"Room: {hall_ticket.exam_room.name}")
            p.drawString(100, 480, f"Building: {hall_ticket.exam_room.building}")
        
        if hall_ticket.seat_number:
            p.drawString(100, 450, f"Seat Number: {hall_ticket.seat_number}")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="hall_ticket_{hall_ticket.ticket_number}.pdf"'
        return response


class ExamAttendanceViewSet(viewsets.ModelViewSet):
    queryset = ExamAttendance.objects.all()
    serializer_class = ExamAttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'exam_registration__exam_schedule', 'invigilator']
    search_fields = ['exam_registration__student__roll_number', 'exam_registration__student__first_name']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def mark_attendance(self, request, pk=None):
        """Mark student attendance for exam"""
        attendance = self.get_object()
        status = request.data.get('status')
        remarks = request.data.get('remarks', '')
        
        if not status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance.status = status
        attendance.remarks = remarks
        
        if status == 'PRESENT':
            attendance.check_in_time = timezone.now()
        
        attendance.save()
        serializer = self.get_serializer(attendance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        """Mark student check out from exam"""
        attendance = self.get_object()
        attendance.check_out_time = timezone.now()
        attendance.save()
        
        serializer = self.get_serializer(attendance)
        return Response(serializer.data)


class ExamViolationViewSet(viewsets.ModelViewSet):
    queryset = ExamViolation.objects.all()
    serializer_class = ExamViolationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['violation_type', 'severity', 'is_resolved', 'exam_registration__exam_schedule']
    search_fields = ['exam_registration__student__roll_number', 'description', 'action_taken']
    ordering = ['-reported_at']
    
    @action(detail=True, methods=['post'])
    def resolve_violation(self, request, pk=None):
        """Resolve a violation"""
        violation = self.get_object()
        action_taken = request.data.get('action_taken', '')
        penalty = request.data.get('penalty', '')
        
        if not action_taken:
            return Response(
                {'error': 'Action taken is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        violation.action_taken = action_taken
        violation.penalty = penalty
        violation.is_resolved = True
        violation.resolved_at = timezone.now()
        violation.resolved_by = request.user.faculty
        violation.save()
        
        serializer = self.get_serializer(violation)
        return Response(serializer.data)


class ExamResultViewSet(viewsets.ModelViewSet):
    queryset = ExamResult.objects.all()
    serializer_class = ExamResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_pass', 'is_published', 'exam_registration__exam_schedule']
    search_fields = ['exam_registration__student__roll_number', 'exam_registration__student__first_name']
    ordering = ['-evaluated_at']
    
    @action(detail=True, methods=['post'])
    def publish_result(self, request, pk=None):
        """Publish exam result to student"""
        result = self.get_object()
        result.is_published = True
        result.published_at = timezone.now()
        result.save()
        
        serializer = self.get_serializer(result)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def student_results(self, request):
        """Get results for a specific student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        student_results = ExamResult.objects.filter(
            exam_registration__student_id=student_id
        )
        serializer = self.get_serializer(student_results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def exam_results(self, request):
        """Get results for a specific exam"""
        exam_schedule_id = request.query_params.get('exam_schedule_id')
        if not exam_schedule_id:
            return Response(
                {'error': 'exam_schedule_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exam_results = ExamResult.objects.filter(
            exam_registration__exam_schedule_id=exam_schedule_id
        )
        serializer = self.get_serializer(exam_results, many=True)
        return Response(serializer.data)


# Additional API Views
class DashboardStatsView(APIView):
    """Dashboard statistics view"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get current date
        today = timezone.now().date()
        
        # Overall statistics
        total_exam_sessions = ExamSession.objects.count()
        active_exam_sessions = ExamSession.objects.filter(is_active=True).count()
        total_exam_schedules = ExamSchedule.objects.count()
        total_students = ExamRegistration.objects.values('student').distinct().count()
        
        # Today's exams
        today_exams = ExamSchedule.objects.filter(exam_date=today)
        today_exams_count = today_exams.count()
        ongoing_exams = ExamSchedule.objects.filter(status='ONGOING').count()
        
        # Pending approvals
        pending_registrations = ExamRegistration.objects.filter(status='PENDING').count()
        
        # Overdue dues
        overdue_dues = StudentDue.objects.filter(
            due_date__lt=today,
            status='PENDING'
        ).count()
        
        # Recent activities
        recent_registrations = ExamRegistration.objects.filter(
            created_at__date=today
        ).count()
        
        recent_hall_tickets = HallTicket.objects.filter(
            generated_date__date=today
        ).count()
        
        stats = {
            'overview': {
                'total_exam_sessions': total_exam_sessions,
                'active_exam_sessions': active_exam_sessions,
                'total_exam_schedules': total_exam_schedules,
                'total_students': total_students,
            },
            'today': {
                'exams_count': today_exams_count,
                'ongoing_exams': ongoing_exams,
            },
            'pending': {
                'registrations': pending_registrations,
                'overdue_dues': overdue_dues,
            },
            'recent_activity': {
                'registrations': recent_registrations,
                'hall_tickets': recent_hall_tickets,
            }
        }
        
        return Response(stats)


class ExamSummaryReportView(APIView):
    """Generate exam summary report"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        exam_session_id = request.query_params.get('exam_session_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if exam_session_id:
            # Report for specific exam session
            exam_session = get_object_or_404(ExamSession, id=exam_session_id)
            exam_schedules = ExamSchedule.objects.filter(exam_session=exam_session)
        elif start_date and end_date:
            # Report for date range
            exam_schedules = ExamSchedule.objects.filter(
                exam_date__range=[start_date, end_date]
            )
        else:
            # Default to current month
            current_month = timezone.now().month
            current_year = timezone.now().year
            exam_schedules = ExamSchedule.objects.filter(
                exam_date__month=current_month,
                exam_date__year=current_year
            )
        
        report_data = []
        for schedule in exam_schedules:
            registrations = schedule.registrations.all()
            attendance = ExamAttendance.objects.filter(
                exam_registration__exam_schedule=schedule
            )
            
            schedule_data = {
                'exam_title': schedule.title,
                'course': schedule.course.code,
                'exam_date': schedule.exam_date,
                'total_registrations': registrations.count(),
                'present_students': attendance.filter(status='PRESENT').count(),
                'absent_students': attendance.filter(status='ABSENT').count(),
                'violations': ExamViolation.objects.filter(
                    exam_registration__exam_schedule=schedule
                ).count(),
                'results_published': ExamResult.objects.filter(
                    exam_registration__exam_schedule=schedule,
                    is_published=True
                ).count(),
            }
            report_data.append(schedule_data)
        
        return Response({
            'report_period': {
                'exam_session_id': exam_session_id,
                'start_date': start_date,
                'end_date': end_date,
            },
            'total_exams': len(report_data),
            'exams': report_data
        })


class StudentPerformanceReportView(APIView):
    """Generate student performance report"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        student_id = request.query_params.get('student_id')
        exam_session_id = request.query_params.get('exam_session_id')
        
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get student's exam results
        results_query = ExamResult.objects.filter(
            exam_registration__student_id=student_id
        )
        
        if exam_session_id:
            results_query = results_query.filter(
                exam_registration__exam_schedule__exam_session_id=exam_session_id
            )
        
        results = results_query.select_related(
            'exam_registration__exam_schedule__course',
            'exam_registration__exam_schedule__exam_session'
        )
        
        performance_data = []
        total_marks = 0
        obtained_marks = 0
        passed_exams = 0
        
        for result in results:
            if result.marks_obtained is not None:
                total_marks += result.exam_registration.exam_schedule.total_marks
                obtained_marks += result.marks_obtained
                if result.is_pass:
                    passed_exams += 1
            
            performance_data.append({
                'exam_title': result.exam_registration.exam_schedule.title,
                'course_code': result.exam_registration.exam_schedule.course.code,
                'exam_date': result.exam_registration.exam_schedule.exam_date,
                'total_marks': result.exam_registration.exam_schedule.total_marks,
                'marks_obtained': result.marks_obtained,
                'percentage': result.percentage,
                'grade': result.grade,
                'is_pass': result.is_pass,
                'exam_session': result.exam_registration.exam_schedule.exam_session.name,
            })
        
        overall_percentage = (obtained_marks / total_marks * 100) if total_marks > 0 else 0
        
        return Response({
            'student_id': student_id,
            'exam_session_id': exam_session_id,
            'overall_performance': {
                'total_exams': len(performance_data),
                'passed_exams': passed_exams,
                'failed_exams': len(performance_data) - passed_exams,
                'overall_percentage': round(overall_percentage, 2),
                'total_marks': total_marks,
                'obtained_marks': obtained_marks,
            },
            'exam_results': performance_data
        })


class BulkGenerateHallTicketsView(APIView):
    """Bulk generate hall tickets for approved registrations"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        exam_schedule_id = request.data.get('exam_schedule_id')
        
        if not exam_schedule_id:
            return Response(
                {'error': 'exam_schedule_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get approved registrations without hall tickets
        approved_registrations = ExamRegistration.objects.filter(
            exam_schedule_id=exam_schedule_id,
            status='APPROVED'
        ).exclude(
            hall_ticket__isnull=False
        )
        
        generated_tickets = []
        for registration in approved_registrations:
            hall_ticket = HallTicket.objects.create(
                exam_registration=registration
            )
            generated_tickets.append({
                'student': registration.student.get_full_name(),
                'roll_number': registration.student.roll_number,
                'ticket_number': hall_ticket.ticket_number,
            })
        
        return Response({
            'message': f'Generated {len(generated_tickets)} hall tickets',
            'generated_tickets': generated_tickets
        })


class BulkAssignRoomsView(APIView):
    """Bulk assign rooms to exam schedules"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        exam_schedule_id = request.data.get('exam_schedule_id')
        room_assignments = request.data.get('room_assignments', [])
        
        if not exam_schedule_id or not room_assignments:
            return Response(
                {'error': 'exam_schedule_id and room_assignments are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exam_schedule = get_object_or_404(ExamSchedule, id=exam_schedule_id)
        
        # Clear existing allocations
        ExamRoomAllocation.objects.filter(exam_schedule=exam_schedule).delete()
        
        # Create new allocations
        created_allocations = []
        for assignment in room_assignments:
            room_id = assignment.get('room_id')
            allocated_capacity = assignment.get('allocated_capacity')
            is_primary = assignment.get('is_primary', False)
            notes = assignment.get('notes', '')
            
            room = get_object_or_404(ExamRoom, id=room_id)
            
            allocation = ExamRoomAllocation.objects.create(
                exam_schedule=exam_schedule,
                exam_room=room,
                allocated_capacity=allocated_capacity,
                is_primary=is_primary,
                notes=notes
            )
            
            created_allocations.append({
                'room_name': room.name,
                'building': room.building,
                'allocated_capacity': allocated_capacity,
                'is_primary': is_primary,
            })
        
        return Response({
            'message': f'Assigned {len(created_allocations)} rooms to exam schedule',
            'room_assignments': created_allocations
        })


class BulkAssignStaffView(APIView):
    """Bulk assign staff to exam schedules"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        exam_schedule_id = request.data.get('exam_schedule_id')
        staff_assignments = request.data.get('staff_assignments', [])
        
        if not exam_schedule_id or not staff_assignments:
            return Response(
                {'error': 'exam_schedule_id and staff_assignments are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exam_schedule = get_object_or_404(ExamSchedule, id=exam_schedule_id)
        
        # Clear existing assignments
        ExamStaffAssignment.objects.filter(exam_schedule=exam_schedule).delete()
        
        # Create new assignments
        created_assignments = []
        for assignment in staff_assignments:
            faculty_id = assignment.get('faculty_id')
            role = assignment.get('role')
            room_id = assignment.get('room_id')
            notes = assignment.get('notes', '')
            
            faculty = get_object_or_404('faculty.Faculty', id=faculty_id)
            room = get_object_or_404(ExamRoom, id=room_id) if room_id else None
            
            staff_assignment = ExamStaffAssignment.objects.create(
                exam_schedule=exam_schedule,
                faculty=faculty,
                role=role,
                exam_room=room,
                notes=notes
            )
            
            created_assignments.append({
                'faculty_name': faculty.user.get_full_name(),
                'role': role,
                'room_name': room.name if room else 'Not assigned',
                'notes': notes,
            })
        
        return Response({
            'message': f'Assigned {len(created_assignments)} staff members to exam schedule',
            'staff_assignments': created_assignments
        })

