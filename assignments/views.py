from rest_framework import generics, status, permissions, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import transaction

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
    AssignmentAnalyticsSerializer, AssignmentNotificationSerializer, AssignmentScheduleSerializer,
    SimpleAssignmentSerializer, SimpleAssignmentCreateSerializer
)

User = get_user_model()
# -------------------------
# Utility: auto-group students for an assignment from a StudentBatch
# -------------------------

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def auto_create_groups_from_batch(request, assignment_id):
    """Create assignment groups from a given StudentBatch.

    Body accepts either `group_size` or `num_groups` (prefer group_size).
    Example: {"student_batch_id": "...", "group_size": 10}
    """
    if not hasattr(request.user, 'faculty_profile') and not request.user.is_staff:
        return Response({'error': 'Only faculty or admins can create groups'}, status=status.HTTP_403_FORBIDDEN)

    assignment = get_object_or_404(Assignment, id=assignment_id)

    student_batch_id = request.data.get('student_batch_id')
    group_size = request.data.get('group_size')
    num_groups = request.data.get('num_groups')

    if not student_batch_id:
        return Response({'error': 'student_batch_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from students.models import StudentBatch, Student
        batch = StudentBatch.objects.get(id=student_batch_id)
    except Exception:
        return Response({'error': 'Invalid student_batch_id'}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch active students of the batch
    students_qs = Student.objects.filter(student_batch=batch, status='ACTIVE').order_by('apaar_student_id')
    total = students_qs.count()
    if total == 0:
        return Response({'error': 'No active students in batch'}, status=status.HTTP_400_BAD_REQUEST)

    if group_size:
        try:
            group_size = int(group_size)
        except Exception:
            return Response({'error': 'group_size must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        if group_size <= 0:
            return Response({'error': 'group_size must be > 0'}, status=status.HTTP_400_BAD_REQUEST)
        import math
        num_groups = math.ceil(total / group_size)
    elif num_groups:
        try:
            num_groups = int(num_groups)
        except Exception:
            return Response({'error': 'num_groups must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        if num_groups <= 0:
            return Response({'error': 'num_groups must be > 0'}, status=status.HTTP_400_BAD_REQUEST)
        group_size = max(1, (total + num_groups - 1) // num_groups)
    else:
        # Default: 10 per group
        import math
        group_size = 10
        num_groups = math.ceil(total / group_size)

    students = list(students_qs.values_list('id', flat=True))

    created = []
    with transaction.atomic():
        for i in range(num_groups):
            start = i * group_size
            end = min(start + group_size, total)
            if start >= end:
                break
            member_ids = students[start:end]
            group = AssignmentGroup.objects.create(
                assignment=assignment,
                group_name=f"Batch {batch.batch_code} - Group {i+1}",
                leader_id=member_ids[0]
            )
            group.members.add(*member_ids)
            created.append(group)

    serializer = AssignmentGroupSerializer(created, many=True)
    return Response({
        'message': f'Created {len(created)} groups (size ~{group_size}) for {total} students',
        'groups': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_assignment_to_section(request, assignment_id):
    """Assign an existing assignment to a CourseSection and auto-link related entities.

    Body: {"course_section_id": "<uuid>", "include_students": true}
    - Sets canonical `course`, `course_section`, `department`.
    - Sets `academic_year` and `semester` from the section's `student_batch`.
    - Adds to M2M: `assigned_to_course_sections`, `assigned_to_courses`, `assigned_to_departments`.
    - Optionally adds all active students of the batch to `assigned_to_students`.
    """
    user = request.user
    if not hasattr(user, 'faculty_profile') and not user.is_staff:
        return Response({'error': 'Only faculty or admins can assign sections'}, status=status.HTTP_403_FORBIDDEN)

    assignment = get_object_or_404(Assignment, id=assignment_id)

    section_id = request.data.get('course_section_id')
    include_students = bool(request.data.get('include_students', True))
    if not section_id:
        return Response({'error': 'course_section_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    from academics.models import CourseSection
    from students.models import Student

    section = get_object_or_404(CourseSection, id=section_id)

    # Authorization: faculty must match section faculty unless admin
    if hasattr(user, 'faculty_profile') and section.faculty_id != user.faculty_profile.id:
        return Response({'error': 'You can only assign to your own course sections'}, status=status.HTTP_403_FORBIDDEN)

    with transaction.atomic():
        assignment.course_section = section
        assignment.course = section.course
        # Derive department from course
        try:
            assignment.department = section.course.department
        except Exception:
            pass
        # Derive academic year and semester from batch
        batch = section.student_batch
        if batch and hasattr(batch, 'academic_year'):
            assignment.academic_year = batch.academic_year
        if batch and hasattr(batch, 'get_semester_object'):
            sem_obj = batch.get_semester_object()
            if sem_obj:
                assignment.semester = sem_obj

        # Add to M2M sets
        assignment.save()
        assignment.assigned_to_course_sections.add(section)
        assignment.assigned_to_courses.add(section.course)
        if assignment.department_id:
            assignment.assigned_to_departments.add(assignment.department)

        # Optionally link all active students of the batch
        if include_students and batch:
            student_ids = list(Student.objects.filter(student_batch=batch, status='ACTIVE').values_list('id', flat=True))
            if student_ids:
                assignment.assigned_to_students.add(*student_ids)

    serializer = SimpleAssignmentSerializer(assignment, context={'request': request})
    return Response(serializer.data)


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
                assigned_to_students=student
            ).distinct()
        
        # Admin can see all assignments
        elif user.is_staff:
            return Assignment.objects.all()
        
        return Assignment.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        # Use create serializer for validation on input, but respond with full serializer
        if self.request.method == 'POST':
            return AssignmentCreateSerializer
        return AssignmentSerializer
    
    def perform_create(self, serializer):
        """Set faculty when creating assignment"""
        if hasattr(self.request.user, 'faculty_profile'):
            # Save using create serializer then re-serialize with full serializer for response
            assignment = serializer.save(faculty=self.request.user.faculty_profile)
            # Attach the full serializer instance to view for create() to return correctly
            self.created_instance = assignment
        else:
            raise exceptions.PermissionDenied("Only faculty can create assignments")

    def create(self, request, *args, **kwargs):
        """Override to return full AssignmentSerializer in response"""
        response = super().create(request, *args, **kwargs)
        try:
            instance = getattr(self, 'created_instance', None)
            if instance is not None and response.status_code == status.HTTP_201_CREATED:
                data = AssignmentSerializer(instance, context={'request': request}).data
                return Response(data, status=status.HTTP_201_CREATED)
        except Exception:
            pass
        return response


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
            return Assignment.objects.filter(assigned_to_students=student).distinct()
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
    pagination_class = None
    
    def get_queryset(self):
        """Filter submissions based on user role"""
        user = self.request.user
        assignment_id = self.kwargs.get('assignment_id')
        
        if hasattr(user, 'student_profile'):
            # Students can see their own submissions
            return AssignmentSubmission.objects.filter(
                student=user.student_profile,
                assignment_id=assignment_id
            ).distinct()
        elif hasattr(user, 'faculty_profile'):
            # Faculty can see all submissions for their assignments
            return AssignmentSubmission.objects.filter(
                assignment__faculty=user.faculty_profile,
                assignment_id=assignment_id
            ).distinct()
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
        if not hasattr(self.request.user, 'student_profile'):
            raise exceptions.PermissionDenied("Only students can submit assignments")

        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)

        # Determine if the submission is late and set status accordingly
        is_late = False
        status_value = 'SUBMITTED'
        if assignment.due_date and timezone.now() > assignment.due_date:
            is_late = True
            status_value = 'LATE'

        from django.db import IntegrityError
        try:
            serializer.save(student=self.request.user.student_profile, assignment=assignment, is_late=is_late, status=status_value)
        except IntegrityError:
            raise exceptions.ValidationError({"detail": "Duplicate submission for this assignment is not allowed"})

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Re-serialize with full serializer to include id and is_late
        try:
            if response.status_code == status.HTTP_201_CREATED:
                assignment_id = kwargs.get('assignment_id')
                instance = AssignmentSubmission.objects.filter(assignment_id=assignment_id, student=getattr(request.user, 'student_profile', None)).order_by('-created_at').first()
                if instance is not None:
                    data = AssignmentSubmissionSerializer(instance, context={'request': request}).data
                    return Response(data, status=status.HTTP_201_CREATED)
        except Exception:
            pass
        return response


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
        # For update() path DRF expects queryset of the object being updated.
        # We update the Grade via the Submission id in URL, so return AssignmentSubmission queryset.
        return AssignmentSubmission.objects.all()
    
    def perform_create(self, serializer):
        """Set graded_by when creating grade"""
        submission_id = self.kwargs.get('submission_id')
        # Get submission directly; permission errors handled below
        submission = get_object_or_404(AssignmentSubmission, id=submission_id)
        # Only faculty (owner) or admin can grade
        user = self.request.user
        if hasattr(user, 'student_profile'):
            raise exceptions.PermissionDenied("Students cannot grade submissions")
        if hasattr(user, 'faculty_profile') and submission.assignment.faculty_id != user.faculty_profile.id:
            raise exceptions.PermissionDenied("You can only grade your own assignment submissions")
        # Validate marks do not exceed assignment max
        marks = serializer.validated_data.get('marks_obtained')
        if marks is not None and submission.assignment.max_marks is not None and marks > submission.assignment.max_marks:
            raise exceptions.PermissionDenied("Marks obtained cannot exceed assignment max marks")
        
        # Create grade
        grade = serializer.save(graded_by=self.request.user)
        
        # Update submission with grade
        submission.grade = grade
        submission.graded_by = self.request.user
        submission.graded_at = timezone.now()
        submission.save()

    def update(self, request, *args, **kwargs):
        # PUT should update the existing grade on the submission id in URL
        submission_id = self.kwargs.get('submission_id')
        submission = get_object_or_404(AssignmentSubmission, id=submission_id)
        user = request.user
        if hasattr(user, 'student_profile'):
            raise exceptions.PermissionDenied("Students cannot grade submissions")
        if hasattr(user, 'faculty_profile') and submission.assignment.faculty_id != user.faculty_profile.id:
            raise exceptions.PermissionDenied("You can only grade your own assignment submissions")

        grade = submission.grade
        if not grade:
            # If no grade exists, treat update as create
            return self.create(request, *args, **kwargs)
        serializer = self.get_serializer(grade, data=request.data)
        serializer.is_valid(raise_exception=True)
        marks = serializer.validated_data.get('marks_obtained')
        if marks is not None and submission.assignment.max_marks is not None and marks > submission.assignment.max_marks:
            raise exceptions.PermissionDenied("Marks obtained cannot exceed assignment max marks")
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class AssignmentCommentListCreateView(generics.ListCreateAPIView):
    """View for listing and creating assignment comments"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssignmentCommentSerializer
    pagination_class = None
    
    def get_queryset(self):
        """Get comments for specific assignment"""
        assignment_id = self.kwargs.get('assignment_id')
        return AssignmentComment.objects.filter(
            assignment_id=assignment_id,
            parent_comment__isnull=True
        ).distinct()
    
    def perform_create(self, serializer):
        """Set author when creating comment"""
        assignment_id = self.kwargs.get('assignment_id')
        assignment = get_object_or_404(Assignment, id=assignment_id)
        serializer.save(author=self.request.user, assignment=assignment)


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
    pagination_class = None
    
    def get_queryset(self):
        """Filter templates based on user and public status"""
        user = self.request.user
        # Only public templates are listed
        return AssignmentTemplate.objects.filter(is_public=True).distinct()
    
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
                assigned_to_students=student
            ).distinct().count(),
            'submitted_assignments': submissions.count(),
            'pending_assignments': Assignment.objects.filter(
                assigned_to_students=student
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
                assigned_to_students=student
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


# -------------------------
# Simple views (minimal endpoints)
# -------------------------

class SimpleAssignmentListCreateView(generics.ListCreateAPIView):
    """Minimal assignment listing/creation with straightforward filters."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = Assignment.objects.all().order_by('-created_at')

        department_id = self.request.query_params.get('department')
        course_id = self.request.query_params.get('course')
        section_id = self.request.query_params.get('section')
        academic_year_id = self.request.query_params.get('academic_year')
        semester_id = self.request.query_params.get('semester')
        status_param = self.request.query_params.get('status')
        due_before = self.request.query_params.get('due_before')
        due_after = self.request.query_params.get('due_after')

        if department_id:
            qs = qs.filter(assigned_to_departments__id=department_id)
        if course_id:
            qs = qs.filter(assigned_to_courses__id=course_id)
        if section_id:
            qs = qs.filter(assigned_to_course_sections__id=section_id)
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if semester_id:
            qs = qs.filter(semester_id=semester_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if due_before:
            qs = qs.filter(due_date__lte=due_before)
        if due_after:
            qs = qs.filter(due_date__gte=due_after)

        return qs.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SimpleAssignmentCreateSerializer
        return SimpleAssignmentSerializer

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'faculty_profile'):
            serializer.save(faculty=self.request.user.faculty_profile)
        else:
            raise exceptions.PermissionDenied('Only faculty can create assignments')


class SimpleAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    queryset = Assignment.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SimpleAssignmentCreateSerializer
        return SimpleAssignmentSerializer


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
            assigned_to_students=student
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
