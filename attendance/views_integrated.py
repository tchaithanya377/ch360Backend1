"""
Enhanced Views for Integrated Academic System
Provides comprehensive API endpoints for Academic Periods, Timetable, and Attendance
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import date, timedelta

from .models_integrated import (
    AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord
)
from .serializers_integrated import (
    AcademicPeriodListSerializer, AcademicPeriodDetailSerializer, AcademicPeriodCreateUpdateSerializer,
    TimetableSlotListSerializer, TimetableSlotDetailSerializer, TimetableSlotCreateUpdateSerializer,
    AttendanceSessionListSerializer, AttendanceSessionDetailSerializer, AttendanceSessionCreateUpdateSerializer,
    AttendanceRecordListSerializer, AttendanceRecordDetailSerializer, AttendanceRecordCreateUpdateSerializer,
    BulkTimetableSlotCreateSerializer, BulkAttendanceSessionCreateSerializer,
    AcademicPeriodStatisticsSerializer, StudentAttendanceSummarySerializer, CourseSectionAttendanceSummarySerializer
)
from .permissions import (
    IsAdminOrReadOnly, CanManageAcademicPeriods, CanManageTimetable,
    CanManageAttendance, CanViewAttendance
)


# =============================================================================
# ACADEMIC PERIOD VIEWSETS
# =============================================================================

class AcademicPeriodViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing academic periods
    """
    queryset = AcademicPeriod.objects.all()
    permission_classes = [IsAuthenticated, CanManageAcademicPeriods]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_year', 'semester', 'is_current', 'is_active']
    search_fields = ['academic_year__year', 'semester__name', 'description']
    ordering_fields = ['period_start', 'period_end', 'created_at']
    ordering = ['-academic_year__year', '-semester__semester_type']

    def get_serializer_class(self):
        if self.action == 'list':
            return AcademicPeriodListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AcademicPeriodCreateUpdateSerializer
        return AcademicPeriodDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by current period if requested
        if self.request.query_params.get('current_only') == 'true':
            queryset = queryset.filter(is_current=True)
        
        # Filter by active periods if requested
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related('academic_year', 'semester')

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current academic period"""
        current_period = AcademicPeriod.get_current_period()
        if current_period:
            serializer = AcademicPeriodDetailSerializer(current_period)
            return Response(serializer.data)
        return Response({'detail': 'No current academic period found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Get academic period for a specific date"""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'detail': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = date.fromisoformat(date_str)
            period = AcademicPeriod.get_period_by_date(target_date)
            if period:
                serializer = AcademicPeriodDetailSerializer(period)
                return Response(serializer.data)
            return Response({'detail': 'No academic period found for this date'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'detail': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this academic period as current"""
        period = self.get_object()
        
        # Set all other periods as not current
        AcademicPeriod.objects.filter(is_current=True).update(is_current=False)
        
        # Set this period as current
        period.is_current = True
        period.save()
        
        serializer = AcademicPeriodDetailSerializer(period)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_timetable_slots(self, request, pk=None):
        """Generate timetable slots for this academic period"""
        period = self.get_object()
        
        # Get course sections for this academic period
        from academics.models import CourseSection
        course_sections = CourseSection.objects.filter(
            student_batch__academic_year=period.academic_year
        )
        
        slots_created = 0
        for section in course_sections:
            # Create basic timetable slots (customize as needed)
            for day in range(5):  # Monday to Friday
                slot, created = TimetableSlot.objects.get_or_create(
                    academic_period=period,
                    course_section=section,
                    faculty=section.faculty,
                    day_of_week=day,
                    start_time='09:00:00',
                    end_time='10:00:00',
                    defaults={
                        'slot_type': 'LECTURE',
                        'room': 'A101',
                        'is_active': True,
                        'created_by': request.user
                    }
                )
                if created:
                    slots_created += 1
        
        return Response({
            'detail': f'Generated {slots_created} timetable slots',
            'slots_created': slots_created
        })

    @action(detail=True, methods=['post'])
    def generate_attendance_sessions(self, request, pk=None):
        """Generate attendance sessions for this academic period"""
        period = self.get_object()
        
        # Generate sessions for the entire period
        from .models_integrated import generate_sessions_from_timetable
        sessions_created = generate_sessions_from_timetable(
            period, period.period_start, period.period_end
        )
        
        return Response({
            'detail': f'Generated {sessions_created} attendance sessions',
            'sessions_created': sessions_created
        })

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for this academic period"""
        period = self.get_object()
        
        # Calculate statistics
        stats = {
            'academic_period': period,
            'total_slots': period.timetable_slots.count(),
            'active_slots': period.timetable_slots.filter(is_active=True).count(),
            'total_sessions': period.attendance_sessions.count(),
            'open_sessions': period.attendance_sessions.filter(status='OPEN').count(),
            'closed_sessions': period.attendance_sessions.filter(status='CLOSED').count(),
            'total_records': period.attendance_records.count(),
            'present_count': period.attendance_records.filter(mark__in=['PRESENT', 'LATE']).count(),
            'absent_count': period.attendance_records.filter(mark='ABSENT').count(),
        }
        
        # Calculate attendance percentage
        if stats['total_records'] > 0:
            stats['attendance_percentage'] = (stats['present_count'] / stats['total_records']) * 100
        else:
            stats['attendance_percentage'] = 0.0
        
        serializer = AcademicPeriodStatisticsSerializer(stats)
        return Response(serializer.data)


# =============================================================================
# TIMETABLE SLOT VIEWSETS
# =============================================================================

class TimetableSlotViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing timetable slots
    """
    queryset = TimetableSlot.objects.all()
    permission_classes = [IsAuthenticated, CanManageTimetable]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_period', 'course_section', 'faculty', 'day_of_week', 'slot_type', 'is_active']
    search_fields = ['course_section__course__code', 'faculty__first_name', 'faculty__last_name', 'room']
    ordering_fields = ['day_of_week', 'start_time', 'created_at']
    ordering = ['academic_period', 'day_of_week', 'start_time']

    def get_serializer_class(self):
        if self.action == 'list':
            return TimetableSlotListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TimetableSlotCreateUpdateSerializer
        return TimetableSlotDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by current academic period if requested
        if self.request.query_params.get('current_period') == 'true':
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                queryset = queryset.filter(academic_period=current_period)
        
        # Filter by active slots if requested
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related('academic_period', 'course_section', 'faculty')

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create timetable slots"""
        serializer = BulkTimetableSlotCreateSerializer(data=request.data)
        if serializer.is_valid():
            academic_period_id = serializer.validated_data['academic_period_id']
            course_section_ids = serializer.validated_data['course_section_ids']
            slot_configs = serializer.validated_data['slot_configs']
            
            academic_period = AcademicPeriod.objects.get(id=academic_period_id)
            course_sections = CourseSection.objects.filter(id__in=course_section_ids)
            
            slots_created = 0
            for section in course_sections:
                for config in slot_configs:
                    slot, created = TimetableSlot.objects.get_or_create(
                        academic_period=academic_period,
                        course_section=section,
                        faculty=section.faculty,
                        day_of_week=config['day_of_week'],
                        start_time=config['start_time'],
                        end_time=config['end_time'],
                        defaults={
                            'room': config.get('room', 'A101'),
                            'slot_type': config.get('slot_type', 'LECTURE'),
                            'max_students': config.get('max_students'),
                            'is_active': True,
                            'created_by': request.user
                        }
                    )
                    if created:
                        slots_created += 1
            
            return Response({
                'detail': f'Created {slots_created} timetable slots',
                'slots_created': slots_created
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def generate_sessions(self, request, pk=None):
        """Generate attendance sessions for this timetable slot"""
        slot = self.get_object()
        
        # Generate sessions for the academic period
        from .models_integrated import generate_sessions_from_timetable
        sessions_created = generate_sessions_from_timetable(
            slot.academic_period,
            slot.academic_period.period_start,
            slot.academic_period.period_end
        )
        
        return Response({
            'detail': f'Generated {sessions_created} attendance sessions',
            'sessions_created': sessions_created
        })

    @action(detail=False, methods=['get'])
    def by_faculty(self, request):
        """Get timetable slots for a specific faculty"""
        faculty_id = request.query_params.get('faculty_id')
        if not faculty_id:
            return Response({'detail': 'faculty_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        slots = self.get_queryset().filter(faculty_id=faculty_id)
        serializer = TimetableSlotListSerializer(slots, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_course_section(self, request):
        """Get timetable slots for a specific course section"""
        course_section_id = request.query_params.get('course_section_id')
        if not course_section_id:
            return Response({'detail': 'course_section_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        slots = self.get_queryset().filter(course_section_id=course_section_id)
        serializer = TimetableSlotListSerializer(slots, many=True)
        return Response(serializer.data)


# =============================================================================
# ATTENDANCE SESSION VIEWSETS
# =============================================================================

class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance sessions
    """
    queryset = AttendanceSession.objects.all()
    permission_classes = [IsAuthenticated, CanManageAttendance]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_period', 'course_section', 'faculty', 'status', 'scheduled_date', 'makeup']
    search_fields = ['course_section__course__code', 'room', 'notes', 'faculty__first_name', 'faculty__last_name']
    ordering_fields = ['scheduled_date', 'start_datetime', 'created_at']
    ordering = ['-scheduled_date', 'start_datetime']

    def get_serializer_class(self):
        if self.action == 'list':
            return AttendanceSessionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AttendanceSessionCreateUpdateSerializer
        return AttendanceSessionDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by current academic period if requested
        if self.request.query_params.get('current_period') == 'true':
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                queryset = queryset.filter(academic_period=current_period)
        
        # Filter by today's sessions if requested
        if self.request.query_params.get('today_only') == 'true':
            queryset = queryset.filter(scheduled_date=date.today())
        
        # Filter by open sessions if requested
        if self.request.query_params.get('open_only') == 'true':
            queryset = queryset.filter(status='OPEN')
        
        return queryset.select_related('academic_period', 'course_section', 'faculty')

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create attendance sessions"""
        serializer = BulkAttendanceSessionCreateSerializer(data=request.data)
        if serializer.is_valid():
            academic_period_id = serializer.validated_data['academic_period_id']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            timetable_slot_ids = serializer.validated_data.get('timetable_slot_ids', [])
            
            academic_period = AcademicPeriod.objects.get(id=academic_period_id)
            
            if timetable_slot_ids:
                # Generate sessions for specific timetable slots
                slots = TimetableSlot.objects.filter(id__in=timetable_slot_ids)
                sessions_created = 0
                for slot in slots:
                    sessions_created += self._generate_sessions_for_slot(slot, start_date, end_date)
            else:
                # Generate sessions for all active slots in the academic period
                from .models_integrated import generate_sessions_from_timetable
                sessions_created = generate_sessions_from_timetable(academic_period, start_date, end_date)
            
            return Response({
                'detail': f'Created {sessions_created} attendance sessions',
                'sessions_created': sessions_created
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_sessions_for_slot(self, slot, start_date, end_date):
        """Generate sessions for a specific timetable slot"""
        sessions_created = 0
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() == slot.day_of_week:
                # Check if session already exists
                existing_session = AttendanceSession.objects.filter(
                    timetable_slot=slot,
                    scheduled_date=current_date
                ).first()
                
                if not existing_session:
                    # Create new session
                    start_datetime = timezone.datetime.combine(current_date, slot.start_time)
                    end_datetime = timezone.datetime.combine(current_date, slot.end_time)
                    
                    AttendanceSession.objects.create(
                        academic_period=slot.academic_period,
                        timetable_slot=slot,
                        course_section=slot.course_section,
                        faculty=slot.faculty,
                        scheduled_date=current_date,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        room=slot.room,
                        status='SCHEDULED'
                    )
                    sessions_created += 1
            
            current_date += timedelta(days=1)
        
        return sessions_created

    @action(detail=True, methods=['post'])
    def open(self, request, pk=None):
        """Open session for attendance"""
        session = self.get_object()
        
        if session.status != 'SCHEDULED':
            return Response(
                {'detail': 'Only scheduled sessions can be opened'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'OPEN'
        session.save()
        
        serializer = AttendanceSessionDetailSerializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close session"""
        session = self.get_object()
        
        if session.status != 'OPEN':
            return Response(
                {'detail': 'Only open sessions can be closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'CLOSED'
        session.save()
        
        serializer = AttendanceSessionDetailSerializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        """Generate QR code for session"""
        session = self.get_object()
        
        if session.status not in ['SCHEDULED', 'OPEN']:
            return Response(
                {'detail': 'QR codes can only be generated for scheduled or open sessions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        qr_token = session.generate_qr_token()
        
        return Response({
            'qr_token': qr_token,
            'qr_expires_at': session.qr_expires_at,
            'qr_generated_at': session.qr_generated_at
        })

    @action(detail=True, methods=['get'])
    def attendance_summary(self, request, pk=None):
        """Get attendance summary for this session"""
        session = self.get_object()
        
        records = session.attendance_records.all()
        summary = {
            'total_students': records.count(),
            'present_count': records.filter(mark__in=['PRESENT', 'LATE']).count(),
            'absent_count': records.filter(mark='ABSENT').count(),
            'excused_count': records.filter(mark='EXCUSED').count(),
            'attendance_percentage': session.get_attendance_percentage()
        }
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's attendance sessions"""
        today = date.today()
        sessions = self.get_queryset().filter(scheduled_date=today)
        serializer = AttendanceSessionListSerializer(sessions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def open_sessions(self, request):
        """Get all open attendance sessions"""
        sessions = self.get_queryset().filter(status='OPEN')
        serializer = AttendanceSessionListSerializer(sessions, many=True)
        return Response(serializer.data)


# =============================================================================
# ATTENDANCE RECORD VIEWSETS
# =============================================================================

class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records
    """
    queryset = AttendanceRecord.objects.all()
    permission_classes = [IsAuthenticated, CanViewAttendance]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['academic_period', 'session', 'student', 'mark', 'source', 'sync_status']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'client_uuid']
    ordering_fields = ['marked_at', 'created_at']
    ordering = ['-marked_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AttendanceRecordListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AttendanceRecordCreateUpdateSerializer
        return AttendanceRecordDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Filter by current academic period if requested
        if self.request.query_params.get('current_period') == 'true':
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                queryset = queryset.filter(academic_period=current_period)
        
        return queryset.select_related('academic_period', 'session', 'student')

    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """Bulk mark attendance for multiple students"""
        session_id = request.data.get('session_id')
        records = request.data.get('records', [])
        
        if not session_id or not records:
            return Response(
                {'detail': 'session_id and records are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = AttendanceSession.objects.get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'detail': 'Invalid session ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if session.status != 'OPEN':
            return Response(
                {'detail': 'Session is not open for attendance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_count = 0
        updated_count = 0
        
        for record_data in records:
            student_id = record_data.get('student_id')
            mark = record_data.get('mark')
            
            if not student_id or not mark:
                continue
            
            # Check if record already exists
            existing_record = AttendanceRecord.objects.filter(
                session=session,
                student_id=student_id
            ).first()
            
            if existing_record:
                # Update existing record
                existing_record.mark = mark
                existing_record.marked_at = timezone.now()
                existing_record.source = record_data.get('source', 'MANUAL')
                existing_record.save()
                updated_count += 1
            else:
                # Create new record
                AttendanceRecord.objects.create(
                    session=session,
                    student_id=student_id,
                    academic_period=session.academic_period,
                    mark=mark,
                    source=record_data.get('source', 'MANUAL'),
                    marked_by=request.user
                )
                created_count += 1
        
        return Response({
            'detail': f'Created {created_count} records, updated {updated_count} records',
            'created_count': created_count,
            'updated_count': updated_count
        })

    @action(detail=False, methods=['post'])
    def qr_scan(self, request):
        """Mark attendance via QR code scan"""
        qr_token = request.data.get('qr_token')
        student_id = request.data.get('student_id')
        
        if not qr_token or not student_id:
            return Response(
                {'detail': 'qr_token and student_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session = AttendanceSession.objects.get(qr_token=qr_token)
        except AttendanceSession.DoesNotExist:
            return Response(
                {'detail': 'Invalid QR token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if QR token is expired
        if session.qr_expires_at and session.qr_expires_at < timezone.now():
            return Response(
                {'detail': 'QR token has expired'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if session.status != 'OPEN':
            return Response(
                {'detail': 'Session is not open for attendance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if student is enrolled in the course section
        if not session.course_section.enrollments.filter(student_id=student_id, status='ENROLLED').exists():
            return Response(
                {'detail': 'Student is not enrolled in this course section'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update attendance record
        record, created = AttendanceRecord.objects.update_or_create(
            session=session,
            student_id=student_id,
            defaults={
                'academic_period': session.academic_period,
                'mark': 'PRESENT',
                'source': 'QR',
                'device_id': request.data.get('device_id', ''),
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'marked_by': request.user
            }
        )
        
        return Response({
            'detail': 'Attendance marked successfully',
            'record_id': record.id,
            'created': created
        })

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @action(detail=False, methods=['get'])
    def student_summary(self, request):
        """Get attendance summary for a specific student"""
        student_id = request.query_params.get('student_id')
        academic_period_id = request.query_params.get('academic_period_id')
        
        if not student_id:
            return Response(
                {'detail': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(student_id=student_id)
        
        if academic_period_id:
            queryset = queryset.filter(academic_period_id=academic_period_id)
        else:
            # Use current academic period if not specified
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                queryset = queryset.filter(academic_period=current_period)
        
        records = queryset.all()
        
        summary = {
            'student_id': student_id,
            'total_sessions': records.count(),
            'present_count': records.filter(mark__in=['PRESENT', 'LATE']).count(),
            'absent_count': records.filter(mark='ABSENT').count(),
            'excused_count': records.filter(mark='EXCUSED').count(),
        }
        
        # Calculate attendance percentage
        if summary['total_sessions'] > 0:
            effective_total = summary['total_sessions'] - summary['excused_count']
            if effective_total > 0:
                summary['attendance_percentage'] = (summary['present_count'] / effective_total) * 100
            else:
                summary['attendance_percentage'] = 100.0
        else:
            summary['attendance_percentage'] = 0.0
        
        # Check exam eligibility (assuming 75% threshold)
        summary['is_eligible_for_exam'] = summary['attendance_percentage'] >= 75.0
        
        return Response(summary)

    @action(detail=False, methods=['get'])
    def course_section_summary(self, request):
        """Get attendance summary for a specific course section"""
        course_section_id = request.query_params.get('course_section_id')
        academic_period_id = request.query_params.get('academic_period_id')
        
        if not course_section_id:
            return Response(
                {'detail': 'course_section_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(session__course_section_id=course_section_id)
        
        if academic_period_id:
            queryset = queryset.filter(academic_period_id=academic_period_id)
        else:
            # Use current academic period if not specified
            current_period = AcademicPeriod.get_current_period()
            if current_period:
                queryset = queryset.filter(academic_period=current_period)
        
        records = queryset.all()
        
        summary = {
            'course_section_id': course_section_id,
            'total_sessions': records.values('session').distinct().count(),
            'total_records': records.count(),
            'present_count': records.filter(mark__in=['PRESENT', 'LATE']).count(),
            'absent_count': records.filter(mark='ABSENT').count(),
            'excused_count': records.filter(mark='EXCUSED').count(),
        }
        
        # Calculate attendance percentage
        if summary['total_records'] > 0:
            effective_total = summary['total_records'] - summary['excused_count']
            if effective_total > 0:
                summary['attendance_percentage'] = (summary['present_count'] / effective_total) * 100
            else:
                summary['attendance_percentage'] = 100.0
        else:
            summary['attendance_percentage'] = 0.0
        
        # Get enrolled students count
        from academics.models import CourseSection
        try:
            course_section = CourseSection.objects.get(id=course_section_id)
            summary['enrolled_students_count'] = course_section.enrollments.filter(status='ENROLLED').count()
        except CourseSection.DoesNotExist:
            summary['enrolled_students_count'] = 0
        
        return Response(summary)
