from rest_framework import viewsets, permissions, decorators, response, status
from .models import Mentorship, Project, Meeting, Feedback
from .serializers import (
    MentorshipSerializer,
    ProjectSerializer,
    MeetingSerializer,
    FeedbackSerializer,
)
from django.db import transaction
from django.utils import timezone
from students.models import Student
from faculty.models import Faculty
from departments.models import Department


class MentorshipViewSet(viewsets.ModelViewSet):
    queryset = Mentorship.objects.select_related('mentor', 'student', 'department_ref').all()
    serializer_class = MentorshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department')
        academic_year = self.request.query_params.get('academic_year')
        grade = self.request.query_params.get('grade_level')
        section = self.request.query_params.get('section')
        is_active = self.request.query_params.get('is_active')
        if dept_id:
            qs = qs.filter(department_ref_id=dept_id)
        if academic_year:
            qs = qs.filter(academic_year=academic_year)
        if grade:
            qs = qs.filter(grade_level=grade)
        if section:
            qs = qs.filter(section=section)
        if is_active in ['true', 'false']:
            qs = qs.filter(is_active=(is_active == 'true'))
        return qs

    @decorators.action(detail=False, methods=['post'], url_path='auto-assign', permission_classes=[permissions.IsAdminUser])
    def auto_assign(self, request):
        """Bulk auto-assign mentors to students by department/year/section with simple round-robin."""
        department_id = request.data.get('department_id')
        academic_year = request.data.get('academic_year')
        grade_level = request.data.get('grade_level')
        section = request.data.get('section')
        start_date = request.data.get('start_date') or timezone.now().date()

        try:
            department = Department.objects.get(id=department_id) if department_id else None
        except Department.DoesNotExist:
            return response.Response({'detail': 'Invalid department_id'}, status=status.HTTP_400_BAD_REQUEST)

        students_qs = Student.objects.all()
        if grade_level:
            students_qs = students_qs.filter(grade_level=grade_level)
        if section:
            students_qs = students_qs.filter(section=section)
        if academic_year:
            students_qs = students_qs.filter(academic_year=academic_year)

        mentors_qs = Faculty.objects.filter(status='ACTIVE', currently_associated=True)
        if department:
            mentors_qs = mentors_qs.filter(department_ref=department)

        students = list(students_qs.order_by('last_name', 'first_name'))
        mentors = list(mentors_qs.order_by('name'))

        if not students or not mentors:
            return response.Response({'assigned': 0, 'detail': 'No students or mentors found'}, status=status.HTTP_200_OK)

        created = 0
        with transaction.atomic():
            mentor_idx = 0
            for student in students:
                # Skip if active mentorship already exists for same context
                exists = Mentorship.objects.filter(student=student, is_active=True).exists()
                if exists:
                    continue
                mentor = mentors[mentor_idx]
                mentor_idx = (mentor_idx + 1) % len(mentors)
                Mentorship.objects.create(
                    mentor=mentor,
                    student=student,
                    start_date=start_date,
                    is_active=True,
                    objective='Auto-assigned mentorship',
                    department_ref=department,
                    academic_year=academic_year,
                    grade_level=student.grade_level,
                    section=student.section,
                )
                created += 1
        return response.Response({'assigned': created}, status=status.HTTP_201_CREATED)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.select_related('mentorship').all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        return serializer.save()


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.select_related('mentorship').all()
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        return serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.select_related('mentorship', 'project', 'meeting').all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
