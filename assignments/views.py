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
    AssignmentGroup, AssignmentTemplate
)
from .serializers import (
    AssignmentSerializer, AssignmentCreateSerializer, AssignmentSubmissionSerializer,
    AssignmentSubmissionCreateSerializer, AssignmentFileSerializer, AssignmentGradeSerializer,
    AssignmentCommentSerializer, AssignmentCategorySerializer, AssignmentGroupSerializer,
    AssignmentTemplateSerializer, AssignmentTemplateCreateSerializer,
    AssignmentStatsSerializer, StudentAssignmentStatsSerializer, FacultyAssignmentStatsSerializer
)

User = get_user_model()


class AssignmentCategoryListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment categories"""
    queryset = AssignmentCategory.objects.filter(is_active=True)
    serializer_class = AssignmentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Set permissions based on request method"""
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated, permissions.IsAdminUser]
        return [permissions.IsAuthenticated]


class AssignmentCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting assignment categories"""
    queryset = AssignmentCategory.objects.all()
    serializer_class = AssignmentCategorySerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class AssignmentListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignments"""
    permission_classes = [permissions.IsAuthenticated]
    
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
