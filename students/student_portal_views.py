from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    Student, StudentRepresentative, StudentRepresentativeActivity, 
    StudentFeedback, StudentRepresentativeType
)
from .student_portal_serializers import (
    StudentPortalLoginSerializer, StudentPortalProfileSerializer,
    StudentPortalProfileUpdateSerializer, StudentDashboardSerializer,
    StudentRepresentativeDashboardSerializer, StudentFeedbackSubmissionSerializer,
    StudentRepresentativeActivitySubmissionSerializer, StudentAnnouncementSerializer,
    StudentEventSerializer, StudentRepresentativeSerializer,
    StudentRepresentativeActivitySerializer, StudentFeedbackSerializer
)
from .student_portal_permissions import (
    IsStudent, IsClassRepresentative, IsLadiesRepresentative,
    IsStudentRepresentative, IsRepresentativeOrReadOnly,
    CanAccessRepresentedStudents, CanHandleFeedback,
    IsAPUniversityStudent, CanAccessClassData, CanAccessDepartmentData
)
from accounts.views import record_session

User = get_user_model()


class StudentPortalLoginView(APIView):
    """Student-specific login endpoint for AP University portal"""
    permission_classes = [permissions.AllowAny]
    serializer_class = StudentPortalLoginSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Get student profile
        try:
            student_profile = user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get roles and permissions
        roles = list(user.groups.values_list('name', flat=True))
        permissions = list(user.get_all_permissions())
        
        # Record session
        try:
            record_session(user, request)
        except Exception:
            pass  # Don't fail login if session recording fails
        
        # Serialize student profile
        student_serializer = StudentPortalProfileSerializer(student_profile)
        
        # Check if user is a representative
        representative_info = None
        try:
            rep_role = student_profile.representative_role
            if rep_role.is_current:
                representative_info = StudentRepresentativeSerializer(rep_role).data
        except StudentRepresentative.DoesNotExist:
            pass
        
        return Response({
            'access': str(access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'is_active': user.is_active,
                'is_verified': user.is_verified
            },
            'student_profile': student_serializer.data,
            'representative_role': representative_info,
            'roles': roles,
            'permissions': permissions
        }, status=status.HTTP_200_OK)


class StudentPortalDashboardView(APIView):
    """Student portal dashboard endpoint"""
    permission_classes = [IsAuthenticated, IsAPUniversityStudent]
    
    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get dashboard data
        dashboard_data = {
            'student': StudentPortalProfileSerializer(student).data,
            'academic_summary': self._get_academic_summary(student),
            'stats': self._get_student_stats(student),
            'recent_activities': self._get_recent_activities(student),
            'announcements': self._get_announcements(student),
            'upcoming_events': self._get_upcoming_events(student),
            'feedback_summary': self._get_feedback_summary(student)
        }
        
        return Response(dashboard_data)
    
    def _get_academic_summary(self, student):
        """Get academic summary for student"""
        if not student.student_batch:
            return {}
        
        batch = student.student_batch
        return {
            'current_semester': batch.semester,
            'year_of_study': batch.year_of_study,
            'department': batch.department.name if batch.department else None,
            'department_code': batch.department.code if batch.department else None,
            'academic_program': batch.academic_program.name if batch.academic_program else None,
            'section': batch.section,
            'batch_name': batch.batch_name,
            'academic_year': batch.academic_year.year if batch.academic_year else None
        }
    
    def _get_student_stats(self, student):
        """Get student statistics"""
        # TODO: Integrate with other apps for real data
        return {
            'total_assignments': 0,  # From assignments app
            'pending_assignments': 0,  # From assignments app
            'attendance_percentage': 0,  # From attendance app
            'upcoming_exams': 0,  # From exams app
            'library_books_issued': 0,  # From library app
            'fees_pending': 0,  # From fees app
            'feedback_submitted': StudentFeedback.objects.filter(student=student).count(),
            'feedback_resolved': StudentFeedback.objects.filter(
                student=student, status='RESOLVED'
            ).count()
        }
    
    def _get_recent_activities(self, student):
        """Get recent activities for student"""
        # TODO: Integrate with other apps for real data
        return []
    
    def _get_announcements(self, student):
        """Get relevant announcements for student"""
        # TODO: Integrate with announcements app
        return []
    
    def _get_upcoming_events(self, student):
        """Get upcoming events for student"""
        # TODO: Integrate with events app
        return []
    
    def _get_feedback_summary(self, student):
        """Get feedback summary for student"""
        feedback_queryset = StudentFeedback.objects.filter(student=student)
        
        return {
            'total_submitted': feedback_queryset.count(),
            'pending': feedback_queryset.filter(status='SUBMITTED').count(),
            'in_progress': feedback_queryset.filter(status='IN_PROGRESS').count(),
            'resolved': feedback_queryset.filter(status='RESOLVED').count(),
            'overdue': feedback_queryset.filter(
                status__in=['SUBMITTED', 'IN_PROGRESS']
            ).filter(created_at__lt=timezone.now() - timedelta(days=7)).count()
        }


class StudentRepresentativeDashboardView(APIView):
    """Representative dashboard endpoint"""
    permission_classes = [IsAuthenticated, IsStudentRepresentative]
    
    def get(self, request):
        try:
            student = request.user.student_profile
            representative = student.representative_role
        except (Student.DoesNotExist, StudentRepresentative.DoesNotExist):
            return Response(
                {'error': 'Representative role not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get dashboard data
        dashboard_data = {
            'representative': StudentRepresentativeSerializer(representative).data,
            'represented_students_count': representative.get_represented_students().count(),
            'recent_activities': self._get_recent_activities(representative),
            'pending_feedback': self._get_pending_feedback(representative),
            'feedback_stats': self._get_feedback_stats(representative),
            'upcoming_events': self._get_upcoming_events(representative),
            'announcements': self._get_announcements(representative)
        }
        
        return Response(dashboard_data)
    
    def _get_recent_activities(self, representative):
        """Get recent activities by representative"""
        activities = StudentRepresentativeActivity.objects.filter(
            representative=representative
        ).order_by('-activity_date')[:10]
        
        return StudentRepresentativeActivitySerializer(activities, many=True).data
    
    def _get_pending_feedback(self, representative):
        """Get pending feedback for representative"""
        feedback = StudentFeedback.objects.filter(
            representative=representative,
            status__in=['SUBMITTED', 'UNDER_REVIEW', 'IN_PROGRESS']
        ).order_by('-created_at')[:10]
        
        return StudentFeedbackSerializer(feedback, many=True).data
    
    def _get_feedback_stats(self, representative):
        """Get feedback statistics for representative"""
        feedback_queryset = StudentFeedback.objects.filter(representative=representative)
        
        return {
            'total_handled': feedback_queryset.count(),
            'pending': feedback_queryset.filter(status='SUBMITTED').count(),
            'in_progress': feedback_queryset.filter(status='IN_PROGRESS').count(),
            'resolved': feedback_queryset.filter(status='RESOLVED').count(),
            'overdue': feedback_queryset.filter(
                status__in=['SUBMITTED', 'IN_PROGRESS']
            ).filter(created_at__lt=timezone.now() - timedelta(days=7)).count()
        }
    
    def _get_upcoming_events(self, representative):
        """Get upcoming events for representative"""
        # TODO: Integrate with events app
        return []
    
    def _get_announcements(self, representative):
        """Get relevant announcements for representative"""
        # TODO: Integrate with announcements app
        return []


class StudentPortalProfileView(APIView):
    """Student profile endpoint"""
    permission_classes = [IsAuthenticated, IsAPUniversityStudent]
    
    def get(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentPortalProfileSerializer(student)
        return Response(serializer.data)
    
    def patch(self, request):
        try:
            student = request.user.student_profile
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentPortalProfileUpdateSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(updated_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for student feedback"""
    permission_classes = [IsAuthenticated, CanHandleFeedback]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StudentFeedbackSubmissionSerializer
        return StudentFeedbackSerializer
    
    def get_queryset(self):
        """Filter feedback based on user role"""
        if self.request.user.student_profile.representative_role.is_current:
            # Representatives can see feedback they're handling
            return StudentFeedback.objects.filter(
                representative=self.request.user.student_profile.representative_role
            )
        else:
            # Students can only see their own feedback
            return StudentFeedback.objects.filter(
                student=self.request.user.student_profile
            )
    
    def perform_create(self, serializer):
        """Set student when creating feedback"""
        serializer.save(student=self.request.user.student_profile)
    
    @action(detail=True, methods=['post'])
    def assign_representative(self, request, pk=None):
        """Assign a representative to handle feedback (for representatives)"""
        if not request.user.student_profile.representative_role.is_current:
            return Response(
                {'error': 'Only representatives can assign feedback'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        feedback = self.get_object()
        representative = request.user.student_profile.representative_role
        
        feedback.representative = representative
        feedback.status = 'UNDER_REVIEW'
        feedback.save()
        
        serializer = self.get_serializer(feedback)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update feedback status (for representatives)"""
        if not request.user.student_profile.representative_role.is_current:
            return Response(
                {'error': 'Only representatives can update feedback status'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        feedback = self.get_object()
        new_status = request.data.get('status')
        resolution_notes = request.data.get('resolution_notes', '')
        
        if new_status not in ['UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED']:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback.status = new_status
        feedback.resolution_notes = resolution_notes
        
        if new_status == 'RESOLVED':
            feedback.resolved_by = request.user
            feedback.resolved_date = timezone.now()
        
        feedback.save()
        
        serializer = self.get_serializer(feedback)
        return Response(serializer.data)


class StudentRepresentativeActivityViewSet(viewsets.ModelViewSet):
    """ViewSet for representative activities"""
    permission_classes = [IsAuthenticated, IsStudentRepresentative]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StudentRepresentativeActivitySubmissionSerializer
        return StudentRepresentativeActivitySerializer
    
    def get_queryset(self):
        """Filter activities by representative"""
        return StudentRepresentativeActivity.objects.filter(
            representative=self.request.user.student_profile.representative_role
        )
    
    def perform_create(self, serializer):
        """Set representative when creating activity"""
        serializer.save(representative=self.request.user.student_profile.representative_role)
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """Submit activity for review"""
        activity = self.get_object()
        activity.status = 'SUBMITTED'
        activity.save()
        
        serializer = self.get_serializer(activity)
        return Response(serializer.data)


class StudentRepresentativeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing student representatives"""
    permission_classes = [IsAuthenticated, IsAPUniversityStudent]
    serializer_class = StudentRepresentativeSerializer
    
    def get_queryset(self):
        """Filter representatives based on user's academic context"""
        student = self.request.user.student_profile
        
        if not student.student_batch:
            return StudentRepresentative.objects.none()
        
        batch = student.student_batch
        
        # Get representatives for the same academic context
        queryset = StudentRepresentative.objects.filter(
            academic_year=batch.academic_year,
            semester=batch.semester,
            is_active=True
        )
        
        # Filter by department if available
        if batch.department:
            queryset = queryset.filter(
                Q(department=batch.department) | Q(department__isnull=True)
            )
        
        # Filter by academic program if available
        if batch.academic_program:
            queryset = queryset.filter(
                Q(academic_program=batch.academic_program) | Q(academic_program__isnull=True)
            )
        
        return queryset.order_by('representative_type', 'student__roll_number')
    
    @action(detail=False, methods=['get'])
    def my_representatives(self, request):
        """Get representatives for current student's class/section"""
        student = request.user.student_profile
        
        if not student.student_batch:
            return Response({'error': 'No batch assigned'}, status=status.HTTP_400_BAD_REQUEST)
        
        batch = student.student_batch
        
        # Get representatives for the same class/section
        representatives = StudentRepresentative.objects.filter(
            academic_year=batch.academic_year,
            semester=batch.semester,
            department=batch.department,
            academic_program=batch.academic_program,
            year_of_study=batch.year_of_study,
            section=batch.section,
            is_active=True
        )
        
        serializer = self.get_serializer(representatives, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def represented_students(self, request, pk=None):
        """Get students represented by this representative"""
        representative = self.get_object()
        students = representative.get_represented_students()
        
        # Serialize basic student info
        student_data = []
        for student in students:
            student_data.append({
                'id': str(student.id),
                'roll_number': student.roll_number,
                'full_name': student.full_name,
                'email': student.email,
                'student_mobile': student.student_mobile
            })
        
        return Response({
            'representative': StudentRepresentativeSerializer(representative).data,
            'represented_students': student_data,
            'count': len(student_data)
        })


class StudentPortalStatsView(APIView):
    """Student portal statistics endpoint"""
    permission_classes = [IsAuthenticated, IsAPUniversityStudent]
    
    def get(self, request):
        student = request.user.student_profile
        
        # Get comprehensive stats
        stats = {
            'academic_stats': self._get_academic_stats(student),
            'feedback_stats': self._get_feedback_stats(student),
            'representative_stats': self._get_representative_stats(student),
            'class_stats': self._get_class_stats(student)
        }
        
        return Response(stats)
    
    def _get_academic_stats(self, student):
        """Get academic statistics"""
        if not student.student_batch:
            return {}
        
        batch = student.student_batch
        
        return {
            'current_semester': batch.semester,
            'year_of_study': batch.year_of_study,
            'department': batch.department.name if batch.department else None,
            'academic_program': batch.academic_program.name if batch.academic_program else None,
            'section': batch.section,
            'batch_strength': batch.current_count,
            'academic_year': batch.academic_year.year if batch.academic_year else None
        }
    
    def _get_feedback_stats(self, student):
        """Get feedback statistics"""
        feedback_queryset = StudentFeedback.objects.filter(student=student)
        
        return {
            'total_submitted': feedback_queryset.count(),
            'by_status': dict(feedback_queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_type': dict(feedback_queryset.values('feedback_type').annotate(count=Count('id')).values_list('feedback_type', 'count')),
            'by_priority': dict(feedback_queryset.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))
        }
    
    def _get_representative_stats(self, student):
        """Get representative statistics"""
        try:
            rep_role = student.representative_role
            if rep_role.is_current:
                activities = StudentRepresentativeActivity.objects.filter(representative=rep_role)
                feedback = StudentFeedback.objects.filter(representative=rep_role)
                
                return {
                    'is_representative': True,
                    'representative_type': rep_role.representative_type,
                    'scope_description': rep_role.scope_description,
                    'represented_students_count': rep_role.get_represented_students().count(),
                    'activities_count': activities.count(),
                    'feedback_handled': feedback.count(),
                    'feedback_resolved': feedback.filter(status='RESOLVED').count()
                }
        except StudentRepresentative.DoesNotExist:
            pass
        
        return {'is_representative': False}
    
    def _get_class_stats(self, student):
        """Get class statistics"""
        if not student.student_batch:
            return {}
        
        batch = student.student_batch
        class_students = Student.objects.filter(student_batch=batch, status='ACTIVE')
        
        return {
            'total_students': class_students.count(),
            'male_students': class_students.filter(gender='M').count(),
            'female_students': class_students.filter(gender='F').count(),
            'representatives_count': StudentRepresentative.objects.filter(
                academic_year=batch.academic_year,
                semester=batch.semester,
                department=batch.department,
                academic_program=batch.academic_program,
                year_of_study=batch.year_of_study,
                section=batch.section,
                is_active=True
            ).count()
        }
