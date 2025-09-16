from rest_framework import viewsets, permissions, decorators, response, status
from .models import Mentorship, Project, Meeting, Feedback, ActionItem
from .serializers import (
    MentorshipSerializer,
    ProjectSerializer,
    MeetingSerializer,
    FeedbackSerializer,
    ActionItemSerializer,
)
from django.db import transaction
from django.utils import timezone
from students.models import Student
from faculty.models import Faculty
from departments.models import Department
from django.db.models import Count, Avg


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
        # Role scoping: mentors see only their mentees; HOD sees their department
        user = self.request.user
        if hasattr(user, 'faculty_profile') and user.faculty_profile.is_active_faculty:
            faculty = user.faculty_profile
            if faculty.is_head_of_department and faculty.department_ref_id:
                qs = qs.filter(department_ref_id=faculty.department_ref_id)
            else:
                qs = qs.filter(mentor=faculty)
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

        mentors_qs = Faculty.objects.filter(status='ACTIVE', currently_associated=True, is_mentor=True)
        if department:
            mentors_qs = mentors_qs.filter(department_ref=department)

        students = list(students_qs.order_by('last_name', 'first_name'))
        mentors = list(mentors_qs.order_by('name'))

        if not students or not mentors:
            return response.Response({'assigned': 0, 'detail': 'No students or mentors found'}, status=status.HTTP_200_OK)

        created = 0
        max_mentees = int(request.data.get('max_mentees_per_mentor', 25))
        with transaction.atomic():
            mentor_idx = 0
            # Track current load per mentor
            mentor_load = {m.id: Mentorship.objects.filter(mentor=m, is_active=True).count() for m in mentors}
            for student in students:
                # Skip if active mentorship already exists for same context
                exists = Mentorship.objects.filter(student=student, is_active=True).exists()
                if exists:
                    continue
                # pick next mentor with capacity
                attempts = 0
                mentor = None
                while attempts < len(mentors):
                    candidate = mentors[mentor_idx]
                    mentor_idx = (mentor_idx + 1) % len(mentors)
                    if mentor_load.get(candidate.id, 0) < max_mentees:
                        mentor = candidate
                        break
                    attempts += 1
                if mentor is None:
                    break
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
                mentor_load[mentor.id] = mentor_load.get(mentor.id, 0) + 1
                created += 1
        return response.Response({'assigned': created}, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['post'], url_path='compute-risk')
    def compute_risk(self, request, pk=None):
        m: Mentorship = self.get_object()
        # Simple heuristic: attendance absences and fee overdue influence risk
        risk = 0
        factors = {}
        try:
            from attendance.models import AttendanceRecord
            total_records = AttendanceRecord.objects.filter(student=m.student).count()
            absents = AttendanceRecord.objects.filter(student=m.student, status='ABSENT').count()
            if total_records > 0:
                absence_ratio = absents / max(total_records, 1)
                absence_score = min(int(absence_ratio * 100), 100)
                risk += int(absence_score * 0.5)
                factors['attendance_absence_ratio'] = round(absence_ratio, 3)
        except Exception:
            pass
        try:
            from fees.models import StudentFee
            overdue = StudentFee.objects.filter(student=m.student, status='OVERDUE').count()
            pending = StudentFee.objects.filter(student=m.student, status__in=['PENDING', 'PARTIAL']).count()
            fee_score = min((overdue * 10) + (pending * 3), 100)
            risk += int(fee_score * 0.3)
            factors['fees_overdue_count'] = overdue
            factors['fees_pending_count'] = pending
        except Exception:
            pass
        # Academic performance proxy via assignments if available
        try:
            from assignments.models import Submission
            late = Submission.objects.filter(student=m.student, is_late=True).count()
            missing = Submission.objects.filter(student=m.student, status='MISSING').count()
            acad_score = min((late * 5) + (missing * 10), 100)
            risk += int(acad_score * 0.2)
            factors['assignments_late'] = late
            factors['assignments_missing'] = missing
        except Exception:
            pass

        risk = max(0, min(risk, 100))
        m.risk_score = risk
        m.risk_factors = factors
        m.last_risk_evaluated_at = timezone.now()
        m.save(update_fields=['risk_score', 'risk_factors', 'last_risk_evaluated_at'])
        return response.Response({'risk_score': risk, 'risk_factors': factors})

    @decorators.action(detail=False, methods=['get'], url_path='analytics/summary')
    def analytics_summary(self, request):
        qs = self.get_queryset()
        total = qs.count()
        active = qs.filter(is_active=True).count()
        by_risk = {
            'low_0_25': qs.filter(risk_score__lte=25).count(),
            'mid_26_50': qs.filter(risk_score__gt=25, risk_score__lte=50).count(),
            'high_51_75': qs.filter(risk_score__gt=50, risk_score__lte=75).count(),
            'critical_76_100': qs.filter(risk_score__gt=75).count(),
        }
        by_mentor = qs.values('mentor__name').annotate(count=Count('id'), avg_risk=Avg('risk_score')).order_by('-count')[:25]
        return response.Response({
            'total': total,
            'active': active,
            'risk_distribution': by_risk,
            'by_mentor': list(by_mentor),
        })


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


class ActionItemViewSet(viewsets.ModelViewSet):
    queryset = ActionItem.objects.select_related('mentorship', 'meeting').all()
    serializer_class = ActionItemSerializer
    permission_classes = [permissions.IsAuthenticated]
