from datetime import date, timedelta
import csv
import io
import jwt
from django.db import transaction
from django.db.models import Prefetch, Q, Count, F
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest, 
    LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
    AttendanceConfiguration, get_attendance_settings, get_student_attendance_summary,
    StudentSnapshot
)
from .serializers import (
    AttendanceSessionSerializer, AttendanceRecordSerializer, AttendanceCorrectionRequestSerializer,
    LeaveApplicationSerializer, TimetableSlotSerializer, AcademicCalendarHolidaySerializer,
    AttendanceConfigurationSerializer, StudentAttendanceSummarySerializer,
    BulkAttendanceMarkSerializer, QRCheckinSerializer, OfflineSyncSerializer,
    SessionGenerationSerializer, AttendanceReportSerializer, BiometricWebhookSerializer,
    AttendanceStatisticsSerializer, NotificationSerializer
)
from academics.models import CourseSection, CourseEnrollment
from students.models import Student
from faculty.models import Faculty


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance sessions"""
    queryset = AttendanceSession.objects.all().select_related(
        'course_section__course', 'faculty', 'timetable_slot'
    ).prefetch_related(
        Prefetch('records', queryset=AttendanceRecord.objects.select_related('student')),
        Prefetch('snapshots', queryset=StudentSnapshot.objects.select_related('student'))
    )
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by course section
        course_section = self.request.query_params.get('course_section')
        if course_section:
            queryset = queryset.filter(course_section_id=course_section)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        # Filter by faculty
        faculty = self.request.query_params.get('faculty')
        if faculty:
            queryset = queryset.filter(faculty_id=faculty)
        
        return queryset.order_by('-scheduled_date', 'start_datetime')

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate attendance sessions from timetable"""
        serializer = SessionGenerationSerializer(data=request.data)
        if serializer.is_valid():
            # For now, return a simple response - we'll implement the task later
            return Response({
                'status': 'accepted',
                'message': 'Session generation started'
            }, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def open(self, request, pk=None):
        """Open an attendance session"""
        session = self.get_object()
        if session.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled sessions can be opened'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'open'
        session.save(update_fields=['status', 'updated_at'])
        
        # Generate QR token if enabled
        settings_dict = get_attendance_settings()
        if settings_dict.get('ALLOW_QR_SELF_MARK', True):
            session.generate_qr_token()
        
        return Response(AttendanceSessionSerializer(session).data)

    @action(detail=True, methods=['patch'])
    def close(self, request, pk=None):
        """Close an attendance session"""
        session = self.get_object()
        if session.status not in ['open', 'scheduled']:
            return Response(
                {'error': 'Only open or scheduled sessions can be closed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'closed'
        session.save(update_fields=['status', 'updated_at'])
        return Response(AttendanceSessionSerializer(session).data)

    @action(detail=True, methods=['patch'])
    def lock(self, request, pk=None):
        """Lock an attendance session"""
        session = self.get_object()
        if session.status != 'closed':
            return Response(
                {'error': 'Only closed sessions can be locked'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'locked'
        session.save(update_fields=['status', 'updated_at'])
        return Response(AttendanceSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def qr_token(self, request, pk=None):
        """Generate QR token for session"""
        session = self.get_object()
        settings_dict = get_attendance_settings()
        
        if not settings_dict.get('ALLOW_QR_SELF_MARK', True):
            return Response(
                {'error': 'QR self-marking is disabled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if session.status not in ['open', 'closed']:
            return Response(
                {'error': 'Session must be open or closed for QR check-in'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.generate_qr_token()
        return Response({
            'token': session.qr_token,
            'expires_at': session.qr_expires_at.isoformat() if session.qr_expires_at else None
        })

    @action(detail=True, methods=['post'])
    def generate_records(self, request, pk=None):
        """Generate attendance records for all enrolled students"""
        session = self.get_object()
        
        # Get enrolled students from course section
        enrollments = CourseEnrollment.objects.filter(
            course_section=session.course_section, 
            status='ENROLLED'
        ).select_related('student')
        
        created = 0
        with transaction.atomic():
            for enrollment in enrollments:
                # Create student snapshot
                StudentSnapshot.objects.get_or_create(
                    session=session,
                    student=enrollment.student,
                    defaults={
                        'course_section': session.course_section,
                        'student_batch': enrollment.student.student_batch,
                        'roll_number': enrollment.student.roll_number,
                        'full_name': enrollment.student.full_name
                    }
                )
                
                # Create attendance record
                record, created_record = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=enrollment.student,
                    defaults={'mark': 'absent', 'source': 'system'}
                )
                if created_record:
                    created += 1
        
        return Response({
            'created_records': created,
            'total_records': session.records.count(),
        }, status=status.HTTP_200_OK)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance records"""
    queryset = AttendanceRecord.objects.all().select_related('session', 'student', 'marked_by')
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        # Filter by session
        session = self.request.query_params.get('session')
        if session:
            queryset = queryset.filter(session_id=session)
        
        # Filter by mark
        mark = self.request.query_params.get('mark')
        if mark:
            queryset = queryset.filter(mark=mark)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(session__scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session__scheduled_date__lte=end_date)
        
        return queryset.order_by('-session__scheduled_date', 'student__roll_number')

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_mark(self, request):
        """Bulk mark attendance for multiple students"""
        serializer = BulkAttendanceMarkSerializer(data=request.data)
        if serializer.is_valid():
            session_id = serializer.validated_data['session_id']
            marks = serializer.validated_data['marks']
            
            try:
                session = AttendanceSession.objects.get(id=session_id)
            except AttendanceSession.DoesNotExist:
                return Response(
                    {'error': 'Session not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if session.status not in ['open', 'closed']:
                return Response(
                    {'error': 'Session must be open or closed for marking'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            updated_count = 0
            with transaction.atomic():
                for mark_data in marks:
                    student_id = mark_data['student_id']
                    mark = mark_data['mark']
                    reason = mark_data.get('reason', '')
                    
                    record, created = AttendanceRecord.objects.get_or_create(
                        session=session,
                        student_id=student_id,
                        defaults={
                            'mark': mark,
                            'source': 'manual',
                            'reason': reason,
                            'marked_by': request.user
                        }
                    )
                    
                    if not created:
                        record.mark = mark
                        record.reason = reason
                        record.marked_by = request.user
                        record.save()
                        updated_count += 1
            
            return Response({
                'updated_count': updated_count,
                'total_marks': len(marks)
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QRCheckinView(APIView):
    """View for student QR check-in"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QRCheckinSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                session_id = payload.get('session_id')
                session = AttendanceSession.objects.get(id=session_id)
            except (jwt.PyJWTError, AttendanceSession.DoesNotExist):
                return Response(
                    {'error': 'Invalid or expired token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get student from user
            try:
                student = Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Student profile not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if student is enrolled in the course section
            if not CourseEnrollment.objects.filter(
                student=student,
                course_section=session.course_section,
                status='ENROLLED'
            ).exists():
                return Response(
                    {'error': 'Student not enrolled in this course'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark attendance
            with transaction.atomic():
                record, created = AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={
                        'mark': 'present',
                        'source': 'qr',
                        'marked_by': request.user,
                        'ip_address': self.get_client_ip(request),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')
                    }
                )
                
                if not created:
                    record.mark = 'present'
                    record.source = 'qr'
                    record.marked_by = request.user
                    record.save()
            
            return Response({
                'status': 'marked',
                'student': student.full_name,
                'session': str(session)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class OfflineSyncView(APIView):
    """View for offline attendance sync"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OfflineSyncSerializer(data=request.data)
        if serializer.is_valid():
            records = serializer.validated_data['records']
            
            # Get student from user
            try:
                student = Student.objects.get(user=request.user)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Student profile not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            synced_count = 0
            with transaction.atomic():
                for record_data in records:
                    client_uuid = record_data['client_uuid']
                    session_id = record_data['session']
                    mark = record_data['mark']
                    reason = record_data.get('reason', '')
                    
                    try:
                        session = AttendanceSession.objects.get(id=session_id)
                    except AttendanceSession.DoesNotExist:
                        continue
                    
                    # Check if student is enrolled
                    if not CourseEnrollment.objects.filter(
                        student=student,
                        course_section=session.course_section,
                        status='ENROLLED'
                    ).exists():
                        continue
                    
                    # Create or update record
                    record, created = AttendanceRecord.objects.get_or_create(
                        session=session,
                        student=student,
                        defaults={
                            'mark': mark,
                            'source': 'offline',
                            'reason': reason,
                            'client_uuid': client_uuid,
                            'marked_by': request.user
                        }
                    )
                    
                    if not created and record.client_uuid != client_uuid:
                        # Update with offline data
                        record.mark = mark
                        record.source = 'offline'
                        record.reason = reason
                        record.client_uuid = client_uuid
                        record.save()
                    
                    synced_count += 1
            
            return Response({
                'status': 'synced',
                'synced_count': synced_count,
                'total_records': len(records)
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceCorrectionRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing attendance correction requests"""
    queryset = AttendanceCorrectionRequest.objects.all().select_related(
        'session', 'student', 'requested_by', 'decided_by'
    )
    serializer_class = AttendanceCorrectionRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        # Filter by requested by
        requested_by = self.request.query_params.get('requested_by')
        if requested_by:
            queryset = queryset.filter(requested_by_id=requested_by)
        
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a correction request"""
        correction_request = self.get_object()
        
        if correction_request.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update correction request
            correction_request.status = 'approved'
            correction_request.decided_by = request.user
            correction_request.decided_at = timezone.now()
            correction_request.save()
            
            # Update attendance record
            try:
                record = AttendanceRecord.objects.get(
                    session=correction_request.session,
                    student=correction_request.student
                )
                record.mark = correction_request.to_mark
                record.source = 'system'
                record.save()
            except AttendanceRecord.DoesNotExist:
                # Create new record if it doesn't exist
                AttendanceRecord.objects.create(
                    session=correction_request.session,
                    student=correction_request.student,
                    mark=correction_request.to_mark,
                    source='system',
                    marked_by=request.user
                )
        
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a correction request"""
        correction_request = self.get_object()
        
        if correction_request.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        decision_note = request.data.get('decision_note', '')
        
        correction_request.status = 'rejected'
        correction_request.decided_by = request.user
        correction_request.decided_at = timezone.now()
        correction_request.decision_note = decision_note
        correction_request.save()
        
        return Response({'status': 'rejected'})


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leave applications"""
    queryset = LeaveApplication.objects.all().select_related(
        'student', 'decided_by'
    )
    serializer_class = LeaveApplicationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by student
        student = self.request.query_params.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by leave type
        leave_type = self.request.query_params.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)
        
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a leave application"""
        leave_application = self.get_object()
        
        if leave_application.status != 'pending':
            return Response(
                {'error': 'Only pending applications can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        decision_note = request.data.get('decision_note', '')
        
        leave_application.status = 'approved'
        leave_application.decided_by = request.user
        leave_application.decided_at = timezone.now()
        leave_application.decision_note = decision_note
        leave_application.save()
        
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a leave application"""
        leave_application = self.get_object()
        
        if leave_application.status != 'pending':
            return Response(
                {'error': 'Only pending applications can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        decision_note = request.data.get('decision_note', '')
        
        leave_application.status = 'rejected'
        leave_application.decided_by = request.user
        leave_application.decided_at = timezone.now()
        leave_application.decision_note = decision_note
        leave_application.save()
        
        return Response({'status': 'rejected'})


class StudentAttendanceSummaryView(APIView):
    """View for student attendance summary"""
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get query parameters
        course_section_id = request.query_params.get('course_section')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        course_section = None
        if course_section_id:
            try:
                course_section = CourseSection.objects.get(id=course_section_id)
            except CourseSection.DoesNotExist:
                return Response(
                    {'error': 'Course section not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get attendance summary
        summary = get_student_attendance_summary(
            student=student,
            course_section=course_section,
            start_date=start_date,
            end_date=end_date
        )
        
        # Add student info
        summary.update({
            'student_id': student.id,
            'student_name': student.full_name,
            'student_roll_number': student.roll_number,
            'threshold_percent': get_attendance_settings()['THRESHOLD_PERCENT']
        })
        
        if course_section:
            summary['course_section_id'] = course_section.id
            summary['course_section_name'] = str(course_section)
        
        return Response(summary)


class AttendanceReportView(APIView):
    """View for generating attendance reports"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AttendanceReportSerializer(data=request.data)
        if serializer.is_valid():
            report_type = serializer.validated_data['report_type']
            format_type = serializer.validated_data.get('format', 'json')
            
            # Generate report based on type
            if report_type == 'eligibility':
                data = self.generate_eligibility_report(serializer.validated_data)
            elif report_type == 'summary':
                data = self.generate_summary_report(serializer.validated_data)
            elif report_type == 'defaulters':
                data = self.generate_defaulters_report(serializer.validated_data)
            else:
                data = self.generate_detailed_report(serializer.validated_data)
            
            if format_type == 'csv':
                return self.generate_csv_response(data, report_type)
            elif format_type == 'xlsx':
                return self.generate_xlsx_response(data, report_type)
            else:
                return Response(data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def generate_eligibility_report(self, params):
        """Generate exam eligibility report"""
        # Implementation for eligibility report
        return {'message': 'Eligibility report generated'}

    def generate_summary_report(self, params):
        """Generate attendance summary report"""
        # Implementation for summary report
        return {'message': 'Summary report generated'}

    def generate_defaulters_report(self, params):
        """Generate defaulters report"""
        # Implementation for defaulters report
        return {'message': 'Defaulters report generated'}

    def generate_detailed_report(self, params):
        """Generate detailed attendance report"""
        # Implementation for detailed report
        return {'message': 'Detailed report generated'}

    def generate_csv_response(self, data, report_type):
        """Generate CSV response"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
        
        writer = csv.writer(response)
        # Add CSV headers and data
        writer.writerow(['Report Type', 'Generated At'])
        writer.writerow([report_type, timezone.now()])
        
        return response

    def generate_xlsx_response(self, data, report_type):
        """Generate XLSX response"""
        # Implementation for XLSX generation
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xlsx"'
        return response


class BiometricWebhookView(APIView):
    """View for receiving biometric device webhooks"""
    permission_classes = []  # No authentication for webhooks
    
    def post(self, request):
        serializer = BiometricWebhookSerializer(data=request.data)
        if serializer.is_valid():
            # For now, return a simple response - we'll implement the task later
            return Response({
                'status': 'accepted',
                'message': 'Webhook received'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceStatisticsView(APIView):
    """View for attendance statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date:
            start_date = timezone.now().date() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()
        
        # Calculate statistics
        total_sessions = AttendanceSession.objects.filter(
            scheduled_date__range=[start_date, end_date]
        ).count()
        
        total_students = Student.objects.filter(status='ACTIVE').count()
        
        # Calculate average attendance
        records = AttendanceRecord.objects.filter(
            session__scheduled_date__range=[start_date, end_date]
        )
        total_records = records.count()
        present_records = records.filter(mark__in=['present', 'late']).count()
        average_attendance = (present_records / total_records * 100) if total_records > 0 else 0
        
        # Get eligible/ineligible counts
        threshold = get_attendance_settings()['THRESHOLD_PERCENT']
        eligible_students = 0
        ineligible_students = 0
        
        for student in Student.objects.filter(status='ACTIVE'):
            summary = get_student_attendance_summary(
                student=student,
                start_date=start_date,
                end_date=end_date
            )
            if summary['is_eligible']:
                eligible_students += 1
            else:
                ineligible_students += 1
        
        # Get pending counts
        pending_corrections = AttendanceCorrectionRequest.objects.filter(status='pending').count()
        pending_leaves = LeaveApplication.objects.filter(status='pending').count()
        
        statistics = {
            'total_sessions': total_sessions,
            'total_students': total_students,
            'average_attendance': round(average_attendance, 2),
            'eligible_students': eligible_students,
            'ineligible_students': ineligible_students,
            'pending_corrections': pending_corrections,
            'pending_leaves': pending_leaves,
            'period_start': start_date,
            'period_end': end_date
        }
        
        return Response(statistics)


# Legacy views for backward compatibility
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
