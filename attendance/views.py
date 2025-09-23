"""
Enhanced Attendance Views for CampsHub360
DRF viewsets for production-ready attendance system
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView


class AttendanceConfigurationPagination(CursorPagination):
    """Custom pagination for AttendanceConfiguration that uses updated_at instead of created_at"""
    ordering = '-updated_at'

from .permissions import (
    AcademicPeriodPermissions,
    TimetableSlotPermissions,
    AttendanceSessionPermissions,
    AttendanceRecordPermissions,
    CanManageAcademicPeriods,
    CanManageTimetableSlots,
    CanManageAttendanceSessions,
    CanViewAttendanceRecords,
    CanMarkAttendance,
    CanManageLeaveApplications,
    CanManageCorrectionRequests,
    CanViewStatistics,
    CanExportData,
    CanManageBiometricDevices,
    CanViewAuditLogs,
)
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from datetime import datetime, timedelta
import csv
import io

from .models import (
    AcademicPeriod,
    AttendanceConfiguration,
    AcademicCalendarHoliday,
    TimetableSlot,
    AttendanceSession,
    StudentSnapshot,
    AttendanceRecord,
    LeaveApplication,
    AttendanceCorrectionRequest,
    AttendanceAuditLog,
    AttendanceStatistics,
    BiometricDevice,
    BiometricTemplate,
    get_attendance_settings,
    get_student_attendance_summary,
    generate_sessions_from_timetable,
)

from .serializers import (
    AcademicPeriodSerializer,
    AcademicPeriodListSerializer,
    AcademicPeriodCreateSerializer,
    AttendanceConfigurationSerializer,
    AcademicCalendarHolidaySerializer,
    TimetableSlotSerializer,
    AttendanceSessionListSerializer,
    AttendanceSessionDetailSerializer,
    AttendanceSessionCreateSerializer,
    AttendanceSessionActionSerializer,
    StudentSnapshotSerializer,
    AttendanceRecordSerializer,
    AttendanceRecordCreateSerializer,
    BulkAttendanceMarkSerializer,
    OfflineSyncSerializer,
    LeaveApplicationSerializer,
    LeaveApplicationCreateSerializer,
    LeaveApplicationActionSerializer,
    AttendanceCorrectionRequestSerializer,
    AttendanceCorrectionRequestCreateSerializer,
    AttendanceCorrectionRequestActionSerializer,
    AttendanceStatisticsSerializer,
    StudentAttendanceSummarySerializer,
    CourseAttendanceSummarySerializer,
    BiometricDeviceSerializer,
    BiometricTemplateSerializer,
    AttendanceAuditLogSerializer,
    QRCodeScanSerializer,
    AttendanceExportSerializer,
)


# =============================================================================
# ACADEMIC PERIOD VIEWSETS
# =============================================================================

class AcademicPeriodViewSet(viewsets.ModelViewSet):
    """ViewSet for academic period management"""
    queryset = AcademicPeriod.objects.select_related('academic_year', 'semester', 'created_by').all()
    permission_classes = [AcademicPeriodPermissions]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AcademicPeriodListSerializer
        elif self.action == 'create':
            return AcademicPeriodCreateSerializer
        return AcademicPeriodSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by academic year
        academic_year = self.request.query_params.get('academic_year')
        if academic_year:
            queryset = queryset.filter(academic_year__year=academic_year)
        
        # Filter by semester
        semester = self.request.query_params.get('semester')
        if semester:
            queryset = queryset.filter(semester__name__icontains=semester)
        
        # Filter by current status
        is_current = self.request.query_params.get('is_current')
        if is_current is not None:
            queryset = queryset.filter(is_current=is_current.lower() == 'true')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-academic_year__year', '-semester__semester_type')
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current academic period"""
        current_period = AcademicPeriod.get_current_period()
        if current_period:
            serializer = self.get_serializer(current_period)
            return Response(serializer.data)
        return Response({'detail': 'No current academic period found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Get academic period for a specific date"""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'detail': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            period = AcademicPeriod.get_period_by_date(date_obj)
            
            if period:
                serializer = self.get_serializer(period)
                return Response(serializer.data)
            return Response({'detail': 'No academic period found for the given date'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this academic period as current"""
        period = self.get_object()
        
        # Set all other periods as not current
        AcademicPeriod.objects.filter(is_current=True).update(is_current=False)
        
        # Set this period as current
        period.is_current = True
        period.save()
        
        serializer = self.get_serializer(period)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate_timetable_slots(self, request, pk=None):
        """Generate timetable slots for this academic period"""
        period = self.get_object()
        
        # Get all course sections for this academic period
        from academics.models import CourseSection
        course_sections = CourseSection.objects.filter(
            student_batch__academic_year=period.academic_year
        )
        
        slots_created = 0
        for section in course_sections:
            # Create basic timetable slots (customize as needed)
            TimetableSlot.objects.get_or_create(
                academic_period=period,
                course_section=section,
                faculty=section.faculty,
                day_of_week=0,  # Monday
                start_time='09:00:00',
                end_time='10:00:00',
                defaults={
                    'slot_type': 'LECTURE',
                    'room': 'A101',
                    'is_active': True
                }
            )
            slots_created += 1
        
        return Response({
            'detail': f'Generated {slots_created} timetable slots for {period.display_name}',
            'slots_created': slots_created
        })
    
    @action(detail=True, methods=['post'])
    def generate_attendance_sessions(self, request, pk=None):
        """Generate attendance sessions for this academic period"""
        period = self.get_object()
        
        # Generate sessions for the entire period
        sessions_created = generate_sessions_from_timetable(
            period, period.period_start, period.period_end
        )
        
        return Response({
            'detail': f'Generated {sessions_created} attendance sessions for {period.display_name}',
            'sessions_created': sessions_created
        })


# =============================================================================
# CONFIGURATION VIEWSETS
# =============================================================================

class AttendanceConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance configuration management"""
    queryset = AttendanceConfiguration.objects.all()
    serializer_class = AttendanceConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = AttendanceConfigurationPagination
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class AcademicCalendarHolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for academic calendar holidays"""
    queryset = AcademicCalendarHoliday.objects.all()
    serializer_class = AcademicCalendarHolidaySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['academic_year', 'affects_attendance']


class TimetableSlotViewSet(viewsets.ModelViewSet):
    """ViewSet for timetable slots"""
    queryset = TimetableSlot.objects.select_related('course_section', 'faculty', 'academic_period')
    serializer_class = TimetableSlotSerializer
    permission_classes = [TimetableSlotPermissions]
    filterset_fields = ['course_section', 'faculty', 'academic_period', 'academic_year', 'semester', 'is_active']


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance sessions"""
    queryset = AttendanceSession.objects.select_related('course_section', 'faculty', 'timetable_slot', 'academic_period')
    permission_classes = [AttendanceSessionPermissions]
    filterset_fields = ['course_section', 'faculty', 'status', 'scheduled_date', 'makeup']
    
    def get_queryset(self):
        """Override to add date range filtering"""
        queryset = super().get_queryset()
        
        # Add date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AttendanceSessionListSerializer
        elif self.action == 'create':
            return AttendanceSessionCreateSerializer
        else:
            return AttendanceSessionDetailSerializer
    
    @action(detail=True, methods=['post'])
    def open_session(self, request, pk=None):
        """Open an attendance session"""
        session = self.get_object()
        try:
            session.open_session(opened_by=request.user)
            return Response({'status': 'Session opened successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def close_session(self, request, pk=None):
        """Close an attendance session"""
        session = self.get_object()
        try:
            session.close_session(closed_by=request.user)
            return Response({'status': 'Session closed successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        """Generate QR code for session"""
        session = self.get_object()
        session.generate_qr_token()
        return Response({
            'qr_token': session.qr_token,
            'expires_at': session.qr_expires_at,
            'session_id': session.id
        })
    
    @action(detail=True, methods=['post'])
    def lock_session(self, request, pk=None):
        """Lock an attendance session"""
        session = self.get_object()
        try:
            session.lock_session(locked_by=request.user)
            return Response({'status': 'Session locked successfully'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def generate_records(self, request, pk=None):
        """Generate attendance records for session"""
        session = self.get_object()
        try:
            records_created = session.generate_attendance_records()
            return Response({
                'status': 'Records generated successfully',
                'records_created': records_created
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def generate_sessions(self, request):
        """Generate sessions from timetable for date range"""
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        course_sections = request.data.get('course_sections', [])
        academic_year = request.data.get('academic_year')
        semester = request.data.get('semester')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sessions_created = generate_sessions_from_timetable(
            start_date, end_date, course_sections, academic_year, semester
        )
        
        return Response({
            'sessions_created': sessions_created,
            'start_date': start_date,
            'end_date': end_date
        })


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance records"""
    queryset = AttendanceRecord.objects.select_related('session', 'student', 'marked_by', 'academic_period')
    permission_classes = [AttendanceRecordPermissions]
    filterset_fields = ['session', 'student', 'mark', 'source', 'sync_status', 'academic_period']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceRecordCreateSerializer
        else:
            return AttendanceRecordSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Bulk mark attendance for multiple students"""
        serializer = BulkAttendanceMarkSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def qr_scan(self, request):
        """Mark attendance via QR code scan"""
        serializer = QRCodeScanSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            session = serializer.context['session']
            student_id = serializer.validated_data['student_id']
            
            # Check if student is enrolled in the course section
            if not session.course_section.enrollments.filter(
                student_id=student_id, status='ENROLLED'
            ).exists():
                return Response(
                    {'error': 'Student not enrolled in this course section'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create or update attendance record
            record, created = AttendanceRecord.objects.get_or_create(
                session=session,
                student_id=student_id,
                defaults={
                    'mark': 'present',
                    'source': 'qr',
                    'device_id': serializer.validated_data.get('device_id', ''),
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'location_lat': serializer.validated_data.get('location_lat'),
                    'location_lng': serializer.validated_data.get('location_lng'),
                    'marked_by': request.user,
                }
            )
            
            if not created:
                # Update existing record
                record.mark = 'present'
                record.source = 'qr'
                record.marked_at = timezone.now()
                record.save()
            
            # Auto-mark as late if appropriate
            record.mark_late_if_appropriate()
            
            return Response({
                'status': 'Attendance marked successfully',
                'record_id': record.id,
                'mark': record.mark,
                'created': created
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def offline_sync(self, request):
        """Sync offline attendance records"""
        serializer = OfflineSyncSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            records_data = serializer.validated_data['records']
            sync_token = serializer.validated_data.get('sync_token')
            
            # Validate sync token if provided
            if sync_token:
                try:
                    session = AttendanceSession.objects.get(offline_sync_token=sync_token)
                    if not session.is_qr_valid:
                        return Response(
                            {'error': 'Sync token expired'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except AttendanceSession.DoesNotExist:
                    return Response(
                        {'error': 'Invalid sync token'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Process offline records
            created_count = 0
            updated_count = 0
            errors = []
            
            for record_data in records_data:
                try:
                    # Create or update attendance record
                    record, created = AttendanceRecord.objects.get_or_create(
                        session_id=record_data['session_id'],
                        student_id=record_data['student_id'],
                        defaults={
                            'mark': record_data.get('mark', 'present'),
                            'source': 'offline',
                            'device_id': record_data.get('device_id', ''),
                            'ip_address': self.get_client_ip(request),
                            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                            'location_lat': record_data.get('location_lat'),
                            'location_lng': record_data.get('location_lng'),
                            'marked_by': request.user,
                            'sync_status': 'synced',
                            'offline_data': record_data.get('offline_data', {}),
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        # Update existing record
                        record.mark = record_data.get('mark', 'present')
                        record.source = 'offline'
                        record.sync_status = 'synced'
                        record.offline_data = record_data.get('offline_data', {})
                        record.save()
                        updated_count += 1
                        
                except Exception as e:
                    errors.append({
                        'student_id': record_data.get('student_id'),
                        'error': str(e)
                    })
            
            return Response({
                'status': 'Sync completed',
                'created_records': created_count,
                'updated_records': updated_count,
                'errors': errors
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LeaveApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for leave applications"""
    queryset = LeaveApplication.objects.select_related('student', 'decided_by')
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'leave_type', 'status', 'affects_attendance']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveApplicationCreateSerializer
        else:
            return LeaveApplicationSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a leave application"""
        leave = self.get_object()
        decision_note = request.data.get('decision_note', '')
        leave.approve(request.user, decision_note)
        return Response({'status': 'Leave application approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a leave application"""
        leave = self.get_object()
        decision_note = request.data.get('decision_note', '')
        leave.reject(request.user, decision_note)
        return Response({'status': 'Leave application rejected'})


class AttendanceCorrectionRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for attendance correction requests"""
    queryset = AttendanceCorrectionRequest.objects.select_related(
        'session', 'student', 'requested_by', 'decided_by'
    )
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'session', 'status']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceCorrectionRequestCreateSerializer
        else:
            return AttendanceCorrectionRequestSerializer
    
    def perform_create(self, serializer):
        """Set the requested_by field to the current user"""
        serializer.save(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a correction request"""
        correction = self.get_object()
        decision_note = request.data.get('decision_note', '')
        correction.approve(request.user, decision_note)
        return Response({'status': 'Correction request approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a correction request"""
        correction = self.get_object()
        decision_note = request.data.get('decision_note', '')
        correction.reject(request.user, decision_note)
        return Response({'status': 'Correction request rejected'})


class AttendanceStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for attendance statistics"""
    queryset = AttendanceStatistics.objects.select_related('student', 'course_section')
    serializer_class = AttendanceStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'course_section', 'academic_year', 'semester', 'is_eligible_for_exam']
    
    @action(detail=False, methods=['get'])
    def student_summary(self, request, student_id=None):
        """Get attendance summary for a student"""
        # Get student_id from URL parameter or query parameter
        if not student_id:
            student_id = request.query_params.get('student_id')
        course_section_id = request.query_params.get('course_section_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not student_id:
            return Response(
                {'error': 'student_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from students.models import Student
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        course_section = None
        if course_section_id:
            try:
                from academics.models import CourseSection
                course_section = CourseSection.objects.get(id=course_section_id)
            except CourseSection.DoesNotExist:
                return Response(
                    {'error': 'Course section not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        summary = get_student_attendance_summary(
            student, course_section, start_date, end_date
        )
        
        serializer = StudentAttendanceSummarySerializer({
            'student_id': student.id,
            'student_name': student.full_name,
            'student_roll_number': student.roll_number,
            'course_section_id': course_section.id if course_section else None,
            'course_section_name': str(course_section) if course_section else None,
            'total_sessions': summary['total_sessions'],
            'present_count': summary['present'],
            'absent_count': summary['absent'],
            'late_count': summary['late'],
            'excused_count': summary['excused'],
            'attendance_percentage': summary['percentage'],
            'leave_days': summary['leave_days'],
            'is_eligible_for_exam': summary['is_eligible_for_exam'],
            'threshold_percent': summary['threshold_percent']
        })
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def attendance_statistics(self, request):
        """Get overall attendance statistics"""
        # Get query parameters
        course_section_id = request.query_params.get('course_section_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Build base query
        records_query = AttendanceRecord.objects.all()
        sessions_query = AttendanceSession.objects.all()
        
        if course_section_id:
            records_query = records_query.filter(session__course_section_id=course_section_id)
            sessions_query = sessions_query.filter(course_section_id=course_section_id)
        
        if start_date:
            records_query = records_query.filter(session__scheduled_date__gte=start_date)
            sessions_query = sessions_query.filter(scheduled_date__gte=start_date)
        
        if end_date:
            records_query = records_query.filter(session__scheduled_date__lte=end_date)
            sessions_query = sessions_query.filter(scheduled_date__lte=end_date)
        
        # Calculate statistics
        total_sessions = sessions_query.count()
        total_students = records_query.values('student').distinct().count()
        
        # Get attendance distribution
        from django.db.models import Count
        attendance_dist = records_query.values('mark').annotate(count=Count('id'))
        distribution = {item['mark']: item['count'] for item in attendance_dist}
        
        # Calculate average attendance percentage
        present_count = distribution.get('present', 0)
        total_records = sum(distribution.values())
        average_attendance = (present_count / total_records * 100) if total_records > 0 else 0
        
        # Count eligible students (assuming 75% threshold)
        eligible_students = 0
        ineligible_students = 0
        for student_id in records_query.values_list('student', flat=True).distinct():
            student_records = records_query.filter(student_id=student_id)
            student_present = student_records.filter(mark='present').count()
            student_total = student_records.count()
            student_percentage = (student_present / student_total * 100) if student_total > 0 else 0
            if student_percentage >= 75:
                eligible_students += 1
            else:
                ineligible_students += 1
        
        # Count pending corrections and leaves
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
            'attendance_distribution': distribution,
            'period_start': start_date,
            'period_end': end_date
        }
        
        return Response(statistics)
    
    @action(detail=False, methods=['get'])
    def course_summary(self, request):
        """Get attendance summary for a course section"""
        course_section_id = request.query_params.get('course_section_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not course_section_id:
            return Response(
                {'error': 'course_section_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from academics.models import CourseSection
            course_section = CourseSection.objects.get(id=course_section_id)
        except CourseSection.DoesNotExist:
            return Response(
                {'error': 'Course section not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get attendance records for the course section
        records_query = AttendanceRecord.objects.filter(
            session__course_section=course_section
        )
        
        if start_date:
            records_query = records_query.filter(session__scheduled_date__gte=start_date)
        if end_date:
            records_query = records_query.filter(session__scheduled_date__lte=end_date)
        
        # Calculate statistics
        total_students = course_section.enrollments.filter(status='ENROLLED').count()
        total_sessions = records_query.values('session').distinct().count()
        
        # Get attendance distribution
        attendance_dist = records_query.values('mark').annotate(count=Count('id'))
        distribution = {item['mark']: item['count'] for item in attendance_dist}
        
        # Calculate average attendance percentage
        student_stats = []
        for enrollment in course_section.enrollments.filter(status='ENROLLED'):
            student_summary = get_student_attendance_summary(
                enrollment.student, course_section, start_date, end_date
            )
            student_stats.append(student_summary['attendance_percentage'])
        
        avg_attendance = sum(student_stats) / len(student_stats) if student_stats else 0
        eligible_count = sum(1 for s in student_stats if s >= 75)  # Default threshold
        
        summary = {
            'course_section_id': course_section.id,
            'course_section_name': str(course_section),
            'faculty_name': course_section.faculty.name,
            'total_students': total_students,
            'total_sessions': total_sessions,
            'average_attendance_percentage': round(avg_attendance, 2),
            'eligible_students_count': eligible_count,
            'ineligible_students_count': total_students - eligible_count,
            'attendance_distribution': distribution
        }
        
        serializer = CourseAttendanceSummarySerializer(summary)
        return Response(serializer.data)


class BiometricDeviceViewSet(viewsets.ModelViewSet):
    """ViewSet for biometric devices"""
    queryset = BiometricDevice.objects.all()
    serializer_class = BiometricDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['device_type', 'status', 'is_enabled', 'location']


class BiometricTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for biometric templates"""
    queryset = BiometricTemplate.objects.select_related('student', 'device')
    serializer_class = BiometricTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'device', 'is_active']


class AttendanceAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for attendance audit logs"""
    queryset = AttendanceAuditLog.objects.select_related('performed_by')
    serializer_class = AttendanceAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['entity_type', 'action', 'performed_by', 'session_id', 'student_id']


class AttendanceExportViewSet(viewsets.ViewSet):
    """ViewSet for attendance data export"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def export_data(self, request):
        """Export attendance data in various formats"""
        serializer = AttendanceExportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        format_type = data['format']
        start_date = data['start_date']
        end_date = data['end_date']
        course_sections = data.get('course_sections', [])
        students = data.get('students', [])
        
        # Build query
        records_query = AttendanceRecord.objects.filter(
            session__scheduled_date__range=[start_date, end_date]
        ).select_related('session', 'student', 'session__course_section')
        
        if course_sections:
            records_query = records_query.filter(session__course_section__in=course_sections)
        if students:
            records_query = records_query.filter(student__in=students)
        
        if format_type == 'csv':
            return self._export_csv(records_query)
        elif format_type == 'excel':
            return self._export_excel(records_query)
        elif format_type == 'pdf':
            return self._export_pdf(records_query)
        
        return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)
    
    def _export_csv(self, queryset):
        """Export data as CSV"""
        response = Response(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student Roll Number', 'Student Name', 'Course Section', 'Faculty',
            'Date', 'Start Time', 'End Time', 'Mark', 'Source', 'Reason'
        ])
        
        for record in queryset:
            writer.writerow([
                record.student.roll_number,
                record.student.full_name,
                str(record.session.course_section),
                record.session.faculty.name,
                record.session.scheduled_date,
                record.session.start_datetime.time(),
                record.session.end_datetime.time(),
                record.mark,
                record.source,
                record.reason
            ])
        
        return response
    
    def _export_excel(self, queryset):
        """Export data as Excel (placeholder)"""
        # Implementation would use openpyxl or xlsxwriter
        return Response({'message': 'Excel export not implemented yet'})
    
    def _export_pdf(self, queryset):
        """Export data as PDF (placeholder)"""
        # Implementation would use reportlab or weasyprint
        return Response({'message': 'PDF export not implemented yet'})


class BiometricWebhookView(APIView):
    """View for receiving biometric device webhooks"""
    permission_classes = []  # No authentication for webhooks
    
    def post(self, request):
        from .serializers import BiometricWebhookSerializer
        serializer = BiometricWebhookSerializer(data=request.data)
        if serializer.is_valid():
            # For now, return a simple response - we'll implement the task later
            return Response({
                'status': 'accepted',
                'message': 'Webhook received'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
