from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import (
    Assignment, AssignmentSubmission, AssignmentFile, 
    AssignmentGrade, AssignmentComment, AssignmentCategory,
    AssignmentGroup, AssignmentTemplate, AssignmentRubric,
    AssignmentRubricGrade, AssignmentPeerReview, AssignmentPlagiarismCheck,
    AssignmentLearningOutcome, AssignmentAnalytics, AssignmentNotification,
    AssignmentSchedule
)
from .serializers import (
    AssignmentSerializer, AssignmentCreateSerializer, AssignmentSubmissionSerializer,
    AssignmentSubmissionCreateSerializer, AssignmentFileSerializer, AssignmentGradeSerializer,
    AssignmentCommentSerializer, AssignmentCategorySerializer, AssignmentGroupSerializer,
    AssignmentTemplateSerializer, AssignmentTemplateCreateSerializer,
    AssignmentStatsSerializer, StudentAssignmentStatsSerializer, FacultyAssignmentStatsSerializer,
    AssignmentRubricSerializer, AssignmentRubricGradeSerializer, AssignmentPeerReviewSerializer,
    AssignmentPlagiarismCheckSerializer, AssignmentLearningOutcomeSerializer,
    AssignmentAnalyticsSerializer, AssignmentNotificationSerializer, AssignmentScheduleSerializer
)

User = get_user_model()


class BaseAssignmentViewMixin:
    """Base mixin for assignment views to handle common functionality"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format_kwarg = None
    
    def get_serializer_context(self):
        """Add format_kwarg to context"""
        context = super().get_serializer_context()
        context['format'] = getattr(self, 'format_kwarg', None)
        return context


class AssignmentCategoryListCreateView(BaseAssignmentViewMixin, generics.ListCreateAPIView):
    """View for listing and creating assignment categories"""
    queryset = AssignmentCategory.objects.filter(is_active=True).order_by('created_at')
    serializer_class = AssignmentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    
    def get_permissions(self):
        """Set permissions based on request method"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class AssignmentCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting assignment categories"""
    queryset = AssignmentCategory.objects.all()
    serializer_class = AssignmentCategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class AssignmentListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignments"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    
    def get_queryset(self):
        """Filter assignments based on user role"""
        user = self.request.user
        
        # Faculty can see their own assignments
        if hasattr(user, 'faculty_profile'):
            return Assignment.objects.filter(faculty=user.faculty_profile)
        
        # Students can see assignments assigned to them
        elif hasattr(user, 'student_profile'):
            student = user.student_profile
            return Assignment.objects.filter(
                Q(assigned_to_students=student) | 
                Q(assigned_to_grades__students=student)
            ).distinct()
        
        # Admin can see all assignments
        elif user.is_staff:
            return Assignment.objects.all()
        
        return Assignment.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return AssignmentCreateSerializer
        return AssignmentSerializer
    
    def perform_create(self, serializer):
        """Set faculty when creating assignment"""
        if hasattr(self.request.user, 'faculty_profile'):
            serializer.save(faculty=self.request.user.faculty_profile)
        else:
            raise permissions.PermissionDenied("Only faculty can create assignments")


class AssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting assignments"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter assignments based on user role"""
        user = self.request.user
        
        if hasattr(user, 'faculty_profile'):
            return Assignment.objects.filter(faculty=user.faculty_profile)
        elif hasattr(user, 'student_profile'):
            student = user.student_profile
            return Assignment.objects.filter(
                Q(assigned_to_students=student) | 
                Q(assigned_to_grades__students=student)
            ).distinct()
        elif user.is_staff:
            return Assignment.objects.all()
        
        return Assignment.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method in ['PUT', 'PATCH']:
            return AssignmentCreateSerializer
        return AssignmentSerializer


class AssignmentSubmissionListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment submissions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter submissions based on user role"""
        user = self.request.user
        assignment_id = self.kwargs.get('assignment_id')
        
        if hasattr(user, 'student_profile'):
            # Students can see their own submissions
            return AssignmentSubmission.objects.filter(
                student=user.student_profile,
                assignment_id=assignment_id
            )
        elif hasattr(user, 'faculty_profile'):
            # Faculty can see all submissions for their assignments
            return AssignmentSubmission.objects.filter(
                assignment__faculty=user.faculty_profile,
                assignment_id=assignment_id
            )
        elif user.is_staff:
            # Admin can see all submissions
            return AssignmentSubmission.objects.filter(assignment_id=assignment_id)
        
        return AssignmentSubmission.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return AssignmentSubmissionCreateSerializer
        return AssignmentSubmissionSerializer
    
    def perform_create(self, serializer):
        """Set student when creating submission"""
        if hasattr(self.request.user, 'student_profile'):
            serializer.save(student=self.request.user.student_profile)
        else:
            raise permissions.PermissionDenied("Only students can submit assignments")


class AssignmentSubmissionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting assignment submissions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter submissions based on user role"""
        user = self.request.user
        
        if hasattr(user, 'student_profile'):
            return AssignmentSubmission.objects.filter(student=user.student_profile)
        elif hasattr(user, 'faculty_profile'):
            return AssignmentSubmission.objects.filter(assignment__faculty=user.faculty_profile)
        elif user.is_staff:
            return AssignmentSubmission.objects.all()
        
        return AssignmentSubmission.objects.none()
    
    serializer_class = AssignmentSubmissionSerializer


class AssignmentGradeCreateUpdateView(generics.CreateAPIView, generics.UpdateAPIView):
    """View for creating and updating assignment grades"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentGradeSerializer
    
    def get_queryset(self):
        """Filter submissions based on faculty permissions"""
        user = self.request.user
        
        if hasattr(user, 'faculty_profile'):
            return AssignmentSubmission.objects.filter(assignment__faculty=user.faculty_profile)
        elif user.is_staff:
            return AssignmentSubmission.objects.all()
        
        return AssignmentSubmission.objects.none()
    
    def perform_create(self, serializer):
        """Set graded_by when creating grade"""
        submission_id = self.kwargs.get('submission_id')
        submission = get_object_or_404(self.get_queryset(), id=submission_id)
        
        # Create grade
        grade = serializer.save(graded_by=self.request.user)
        
        # Update submission with grade
        submission.grade = grade
        submission.graded_by = self.request.user
        submission.graded_at = timezone.now()
        submission.save()


class AssignmentCommentListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment comments"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentCommentSerializer
    
    def get_queryset(self):
        """Get comments for specific assignment"""
        assignment_id = self.kwargs.get('assignment_id')
        return AssignmentComment.objects.filter(
            assignment_id=assignment_id,
            parent_comment__isnull=True  # Only top-level comments
        )
    
    def perform_create(self, serializer):
        """Set author when creating comment"""
        serializer.save(author=self.request.user)


class AssignmentFileUploadView(generics.CreateAPIView):
    """View for uploading assignment files"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentFileSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        """Set uploaded_by when creating file"""
        serializer.save(uploaded_by=self.request.user)


class AssignmentTemplateListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment templates"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates based on user and public status"""
        user = self.request.user
        return AssignmentTemplate.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        )
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'POST':
            return AssignmentTemplateCreateSerializer
        return AssignmentTemplateSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating template"""
        serializer.save(created_by=self.request.user)


class AssignmentTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting assignment templates"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter templates based on user permissions"""
        user = self.request.user
        return AssignmentTemplate.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        )
    
    serializer_class = AssignmentTemplateSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assignment_stats(request):
    """Get assignment statistics"""
    user = request.user
    
    if hasattr(user, 'faculty_profile'):
        # Faculty stats
        faculty = user.faculty_profile
        assignments = Assignment.objects.filter(faculty=faculty)
        
        stats = {
            'total_assignments': assignments.count(),
            'published_assignments': assignments.filter(status='PUBLISHED').count(),
            'draft_assignments': assignments.filter(status='DRAFT').count(),
            'overdue_assignments': assignments.filter(
                status='PUBLISHED',
                due_date__lt=timezone.now()
            ).count(),
            'total_submissions': AssignmentSubmission.objects.filter(
                assignment__faculty=faculty
            ).count(),
            'graded_submissions': AssignmentSubmission.objects.filter(
                assignment__faculty=faculty,
                grade__isnull=False
            ).count(),
            'pending_grades': AssignmentSubmission.objects.filter(
                assignment__faculty=faculty,
                grade__isnull=True
            ).count(),
            'average_grade': AssignmentGrade.objects.filter(
                submission__assignment__faculty=faculty
            ).aggregate(avg=Avg('marks_obtained'))['avg']
        }
        
        serializer = FacultyAssignmentStatsSerializer(stats)
        
    elif hasattr(user, 'student_profile'):
        # Student stats
        student = user.student_profile
        submissions = AssignmentSubmission.objects.filter(student=student)
        
        stats = {
            'total_assignments': Assignment.objects.filter(
                Q(assigned_to_students=student) | 
                Q(assigned_to_grades__students=student)
            ).distinct().count(),
            'submitted_assignments': submissions.count(),
            'pending_assignments': Assignment.objects.filter(
                Q(assigned_to_students=student) | 
                Q(assigned_to_grades__students=student)
            ).exclude(
                submissions__student=student
            ).distinct().count(),
            'late_submissions': submissions.filter(is_late=True).count(),
            'average_grade': AssignmentGrade.objects.filter(
                submission__student=student
            ).aggregate(avg=Avg('marks_obtained'))['avg'],
            'total_marks_obtained': AssignmentGrade.objects.filter(
                submission__student=student
            ).aggregate(total=Sum('marks_obtained'))['total'] or 0,
            'total_max_marks': Assignment.objects.filter(
                Q(assigned_to_students=student) | 
                Q(assigned_to_grades__students=student)
            ).aggregate(total=Sum('max_marks'))['total'] or 0
        }
        
        serializer = StudentAssignmentStatsSerializer(stats)
        
    else:
        # Admin stats
        stats = {
            'total_assignments': Assignment.objects.count(),
            'published_assignments': Assignment.objects.filter(status='PUBLISHED').count(),
            'draft_assignments': Assignment.objects.filter(status='DRAFT').count(),
            'overdue_assignments': Assignment.objects.filter(
                status='PUBLISHED',
                due_date__lt=timezone.now()
            ).count(),
            'total_submissions': AssignmentSubmission.objects.count(),
            'graded_submissions': AssignmentSubmission.objects.filter(
                grade__isnull=False
            ).count(),
            'pending_grades': AssignmentSubmission.objects.filter(
                grade__isnull=True
            ).count(),
            'average_grade': AssignmentGrade.objects.aggregate(
                avg=Avg('marks_obtained')
            )['avg']
        }
        
        serializer = AssignmentStatsSerializer(stats)
    
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def publish_assignment(request, assignment_id):
    """Publish an assignment"""
    user = request.user
    
    if not hasattr(user, 'faculty_profile'):
        return Response(
            {'error': 'Only faculty can publish assignments'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    assignment = get_object_or_404(
        Assignment, 
        id=assignment_id, 
        faculty=user.faculty_profile
    )
    
    if assignment.status != 'DRAFT':
        return Response(
            {'error': 'Only draft assignments can be published'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    assignment.status = 'PUBLISHED'
    assignment.save()
    
    serializer = AssignmentSerializer(assignment)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def close_assignment(request, assignment_id):
    """Close an assignment"""
    user = request.user
    
    if not hasattr(user, 'faculty_profile'):
        return Response(
            {'error': 'Only faculty can close assignments'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    assignment = get_object_or_404(
        Assignment, 
        id=assignment_id, 
        faculty=user.faculty_profile
    )
    
    if assignment.status not in ['PUBLISHED', 'DRAFT']:
        return Response(
            {'error': 'Only published or draft assignments can be closed'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    assignment.status = 'CLOSED'
    assignment.save()
    
    serializer = AssignmentSerializer(assignment)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_assignments(request):
    """Get assignments for the current user"""
    user = request.user
    
    if hasattr(user, 'student_profile'):
        # Student assignments
        student = user.student_profile
        assignments = Assignment.objects.filter(
            Q(assigned_to_students=student) | 
            Q(assigned_to_grades__students=student)
        ).distinct().order_by('-created_at')
        
        # Add submission status for each assignment
        for assignment in assignments:
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment,
                student=student
            ).first()
            assignment.submission_status = submission.status if submission else 'NOT_SUBMITTED'
            assignment.submission_date = submission.submission_date if submission else None
            assignment.is_late = submission.is_late if submission else False
        
    elif hasattr(user, 'faculty_profile'):
        # Faculty assignments
        assignments = Assignment.objects.filter(
            faculty=user.faculty_profile
        ).order_by('-created_at')
        
    else:
        return Response(
            {'error': 'User profile not found'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = AssignmentSerializer(assignments, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assignment_submissions(request, assignment_id):
    """Get all submissions for an assignment"""
    user = request.user
    
    if not hasattr(user, 'faculty_profile') and not user.is_staff:
        return Response(
            {'error': 'Only faculty can view all submissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if hasattr(user, 'faculty_profile') and assignment.faculty != user.faculty_profile:
        return Response(
            {'error': 'You can only view submissions for your own assignments'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).order_by('-submission_date')
    
    serializer = AssignmentSubmissionSerializer(submissions, many=True, context={'request': request})
    return Response(serializer.data)


# Enhanced Views for University-Level Features

class AssignmentRubricListCreateView(BaseAssignmentViewMixin, generics.ListCreateAPIView):
    """View for listing and creating assignment rubrics"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    
    def get_queryset(self):
        """Filter rubrics based on user and public status"""
        user = self.request.user
        return AssignmentRubric.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        ).order_by('created_at')
    
    serializer_class = AssignmentRubricSerializer
    
    def perform_create(self, serializer):
        """Set created_by when creating rubric"""
        serializer.save(created_by=self.request.user)


class AssignmentRubricDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting assignment rubrics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter rubrics based on user permissions"""
        user = self.request.user
        return AssignmentRubric.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        )
    
    serializer_class = AssignmentRubricSerializer


class AssignmentRubricGradeCreateUpdateView(generics.CreateAPIView, generics.UpdateAPIView):
    """View for creating and updating rubric-based grades"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentRubricGradeSerializer
    
    def get_queryset(self):
        """Filter submissions based on faculty permissions"""
        user = self.request.user
        
        if hasattr(user, 'faculty_profile'):
            return AssignmentSubmission.objects.filter(assignment__faculty=user.faculty_profile)
        elif user.is_staff:
            return AssignmentSubmission.objects.all()
        
        return AssignmentSubmission.objects.none()
    
    def perform_create(self, serializer):
        """Set graded_by when creating rubric grade"""
        submission_id = self.kwargs.get('submission_id')
        submission = get_object_or_404(self.get_queryset(), id=submission_id)
        
        # Create rubric grade
        rubric_grade = serializer.save(graded_by=self.request.user)
        
        # Update submission with rubric grade
        submission.rubric_grade = rubric_grade
        submission.save()


class AssignmentPeerReviewListCreateView(generics.ListCreateAPIView):
    """View for listing and creating peer reviews"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    serializer_class = AssignmentPeerReviewSerializer
    
    def get_queryset(self):
        """Filter peer reviews based on user role"""
        user = self.request.user
        assignment_id = self.kwargs.get('assignment_id')
        
        if hasattr(user, 'student_profile'):
            # Students can see peer reviews they gave or received
            return AssignmentPeerReview.objects.filter(
                Q(reviewer=user.student_profile) | Q(reviewee=user.student_profile),
                assignment_id=assignment_id
            )
        elif hasattr(user, 'faculty_profile'):
            # Faculty can see all peer reviews for their assignments
            return AssignmentPeerReview.objects.filter(
                assignment__faculty=user.faculty_profile,
                assignment_id=assignment_id
            )
        elif user.is_staff:
            # Admin can see all peer reviews
            return AssignmentPeerReview.objects.filter(assignment_id=assignment_id)
        
        return AssignmentPeerReview.objects.none()
    
    def perform_create(self, serializer):
        """Set reviewer when creating peer review"""
        if hasattr(self.request.user, 'student_profile'):
            serializer.save(reviewer=self.request.user.student_profile)
        else:
            raise permissions.PermissionDenied("Only students can create peer reviews")


class AssignmentPlagiarismCheckListCreateView(generics.ListCreateAPIView):
    """View for listing and creating plagiarism checks"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    serializer_class = AssignmentPlagiarismCheckSerializer
    
    def get_queryset(self):
        """Filter plagiarism checks based on user role"""
        user = self.request.user
        assignment_id = self.kwargs.get('assignment_id')
        
        if hasattr(user, 'student_profile'):
            # Students can see plagiarism checks for their submissions
            return AssignmentPlagiarismCheck.objects.filter(
                submission__student=user.student_profile,
                submission__assignment_id=assignment_id
            )
        elif hasattr(user, 'faculty_profile'):
            # Faculty can see plagiarism checks for their assignments
            return AssignmentPlagiarismCheck.objects.filter(
                submission__assignment__faculty=user.faculty_profile,
                submission__assignment_id=assignment_id
            )
        elif user.is_staff:
            # Admin can see all plagiarism checks
            return AssignmentPlagiarismCheck.objects.filter(
                submission__assignment_id=assignment_id
            )
        
        return AssignmentPlagiarismCheck.objects.none()
    
    def perform_create(self, serializer):
        """Set checked_by when creating plagiarism check"""
        serializer.save(checked_by=self.request.user)


class AssignmentLearningOutcomeListCreateView(generics.ListCreateAPIView):
    """View for listing and creating learning outcomes"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    serializer_class = AssignmentLearningOutcomeSerializer
    
    def get_queryset(self):
        """Get learning outcomes for specific assignment"""
        assignment_id = self.kwargs.get('assignment_id')
        return AssignmentLearningOutcome.objects.filter(assignment_id=assignment_id)
    
    def perform_create(self, serializer):
        """Set assignment when creating learning outcome"""
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        serializer.save(assignment=assignment)


class AssignmentAnalyticsView(generics.RetrieveAPIView):
    """View for retrieving assignment analytics"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentAnalyticsSerializer
    
    def get_queryset(self):
        """Filter analytics based on user permissions"""
        user = self.request.user
        assignment_id = self.kwargs.get('assignment_id')
        
        if hasattr(user, 'faculty_profile'):
            return AssignmentAnalytics.objects.filter(
                assignment__faculty=user.faculty_profile,
                assignment_id=assignment_id
            )
        elif user.is_staff:
            return AssignmentAnalytics.objects.filter(assignment_id=assignment_id)
        
        return AssignmentAnalytics.objects.none()


class AssignmentNotificationListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment notifications"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    serializer_class = AssignmentNotificationSerializer
    
    def get_queryset(self):
        """Get notifications for the current user"""
        return AssignmentNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')


class AssignmentNotificationDetailView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating assignment notifications"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentNotificationSerializer
    
    def get_queryset(self):
        """Get notifications for the current user"""
        return AssignmentNotification.objects.filter(
            recipient=self.request.user
        )
    
    def perform_update(self, serializer):
        """Mark notification as read when updating"""
        if serializer.validated_data.get('is_read') and not serializer.instance.is_read:
            serializer.save(read_at=timezone.now())
        else:
            serializer.save()


class AssignmentScheduleListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment schedules"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for now
    serializer_class = AssignmentScheduleSerializer
    
    def get_queryset(self):
        """Filter schedules based on user permissions"""
        user = self.request.user
        
        if hasattr(user, 'faculty_profile'):
            return AssignmentSchedule.objects.filter(created_by=user)
        elif user.is_staff:
            return AssignmentSchedule.objects.all()
        
        return AssignmentSchedule.objects.none()
    
    def perform_create(self, serializer):
        """Set created_by when creating schedule"""
        serializer.save(created_by=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def run_plagiarism_check(request, submission_id):
    """Run plagiarism check on a submission"""
    user = request.user
    
    if not hasattr(user, 'faculty_profile') and not user.is_staff:
        return Response(
            {'error': 'Only faculty can run plagiarism checks'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    
    # Check if plagiarism check already exists
    plagiarism_check, created = AssignmentPlagiarismCheck.objects.get_or_create(
        submission=submission,
        defaults={
            'status': 'PENDING',
            'checked_by': user
        }
    )
    
    if not created:
        return Response(
            {'error': 'Plagiarism check already exists for this submission'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # TODO: Integrate with actual plagiarism detection service
    # For now, simulate the check
    plagiarism_check.status = 'CLEAN'
    plagiarism_check.similarity_percentage = 5.0
    plagiarism_check.sources = []
    plagiarism_check.save()
    
    serializer = AssignmentPlagiarismCheckSerializer(plagiarism_check)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_peer_reviews(request, assignment_id):
    """Assign peer reviews for an assignment"""
    user = request.user
    
    if not hasattr(user, 'faculty_profile'):
        return Response(
            {'error': 'Only faculty can assign peer reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    assignment = get_object_or_404(
        Assignment, 
        id=assignment_id, 
        faculty=user.faculty_profile
    )
    
    if not assignment.enable_peer_review:
        return Response(
            {'error': 'Peer review is not enabled for this assignment'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get all submissions for the assignment
    submissions = AssignmentSubmission.objects.filter(assignment=assignment)
    
    if submissions.count() < 2:
        return Response(
            {'error': 'Need at least 2 submissions for peer review'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Simple round-robin assignment
    reviewers = list(submissions.values_list('student', flat=True))
    reviewees = list(submissions.values_list('student', flat=True))
    
    created_reviews = []
    for i, reviewer_id in enumerate(reviewers):
        # Each student reviews the next student (with wraparound)
        reviewee_id = reviewees[(i + 1) % len(reviewees)]
        
        if reviewer_id != reviewee_id:  # Don't assign self-review
            submission = submissions.get(student_id=reviewee_id)
            peer_review, created = AssignmentPeerReview.objects.get_or_create(
                assignment=assignment,
                reviewer_id=reviewer_id,
                reviewee_id=reviewee_id,
                submission=submission
            )
            if created:
                created_reviews.append(peer_review)
    
    serializer = AssignmentPeerReviewSerializer(created_reviews, many=True)
    return Response({
        'message': f'Created {len(created_reviews)} peer review assignments',
        'peer_reviews': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assignment_analytics_dashboard(request, assignment_id):
    """Get comprehensive analytics dashboard for an assignment"""
    user = request.user
    
    if not hasattr(user, 'faculty_profile') and not user.is_staff:
        return Response(
            {'error': 'Only faculty can view analytics dashboard'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if hasattr(user, 'faculty_profile') and assignment.faculty != user.faculty_profile:
        return Response(
            {'error': 'You can only view analytics for your own assignments'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create analytics
    analytics, created = AssignmentAnalytics.objects.get_or_create(assignment=assignment)
    
    # Update analytics with current data
    submissions = AssignmentSubmission.objects.filter(assignment=assignment)
    grades = AssignmentGrade.objects.filter(submission__assignment=assignment)
    
    analytics.actual_submissions = submissions.count()
    analytics.submission_rate = (analytics.actual_submissions / max(analytics.total_expected_submissions, 1)) * 100
    
    if grades.exists():
        analytics.average_grade = grades.aggregate(avg=Avg('marks_obtained'))['avg']
        analytics.median_grade = grades.aggregate(median=Avg('marks_obtained'))['avg']  # Simplified median
    
    analytics.late_submission_rate = (submissions.filter(is_late=True).count() / max(analytics.actual_submissions, 1)) * 100
    
    # Plagiarism rate
    plagiarism_checks = AssignmentPlagiarismCheck.objects.filter(
        submission__assignment=assignment
    )
    if plagiarism_checks.exists():
        flagged_count = plagiarism_checks.filter(
            status__in=['SUSPICIOUS', 'PLAGIARIZED']
        ).count()
        analytics.plagiarism_rate = (flagged_count / plagiarism_checks.count()) * 100
    
    analytics.save()
    
    serializer = AssignmentAnalyticsSerializer(analytics)
    return Response(serializer.data)
