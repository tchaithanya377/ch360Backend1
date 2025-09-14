from django.http import JsonResponse
from rest_framework import viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import GradeScale, Term, CourseResult, TermGPA, GraduateRecord
from .serializers import (
    GradeScaleSerializer,
    TermSerializer,
    CourseResultSerializer,
    TermGPASerializer,
    GraduateRecordSerializer,
)


def health(request):
    return JsonResponse({"status": "ok", "app": "grads"})


class IsFacultyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_staff or user.is_superuser


class IsAssignedFacultyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True
        # Allow only the faculty assigned to the course section to write
        section = obj.course_section
        faculty_user = getattr(section.faculty, 'user', None)
        if request.method in permissions.SAFE_METHODS:
            return True
        return faculty_user and faculty_user_id_equals(faculty_user, request.user)


def faculty_user_id_equals(faculty_user, user):
    try:
        return faculty_user.id == user.id
    except Exception:
        return False


class GradeScaleViewSet(viewsets.ModelViewSet):
    queryset = GradeScale.objects.all()
    serializer_class = GradeScaleSerializer
    permission_classes = [IsFacultyOrAdmin]


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.all()
    serializer_class = TermSerializer
    permission_classes = [IsFacultyOrAdmin]


class CourseResultViewSet(viewsets.ModelViewSet):
    queryset = CourseResult.objects.select_related('student', 'term', 'course_section', 'course_section__course')
    serializer_class = CourseResultSerializer
    permission_classes = [IsAssignedFacultyOrAdmin]

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_student(self, request):
        student_id = request.query_params.get('student')
        qs = self.get_queryset()
        if student_id:
            qs = qs.filter(student_id=student_id)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class TermGPAViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TermGPA.objects.select_related('student', 'term')
    serializer_class = TermGPASerializer
    permission_classes = [permissions.IsAuthenticated]


class GraduateRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GraduateRecord.objects.select_related('student', 'program')
    serializer_class = GraduateRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
