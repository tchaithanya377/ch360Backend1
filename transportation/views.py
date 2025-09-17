from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass
from .serializers import (
    VehicleSerializer,
    DriverSerializer,
    RouteSerializer,
    StopSerializer,
    RouteStopSerializer,
    VehicleAssignmentSerializer,
    TripScheduleSerializer,
    TransportPassSerializer,
    BulkStudentPassAssignSerializer,
    BulkFacultyPassAssignSerializer,
)
from .permissions import IsStaffOrReadOnly
from students.models import Student
from students.models import StudentBatch
from faculty.models import Faculty


class DefaultPermission(IsStaffOrReadOnly):
    pass


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["number_plate", "registration_number", "make", "model"]
    ordering_fields = ["number_plate", "capacity", "created_at"]


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "phone", "license_number"]
    ordering_fields = ["full_name", "license_expiry", "created_at"]


class StopViewSet(viewsets.ModelViewSet):
    queryset = Stop.objects.all()
    serializer_class = StopSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "landmark"]
    ordering_fields = ["name", "created_at"]


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]


class RouteStopViewSet(viewsets.ModelViewSet):
    queryset = RouteStop.objects.select_related("route", "stop").all()
    serializer_class = RouteStopSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["route", "stop"]
    ordering_fields = ["order_index"]


class VehicleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = VehicleAssignment.objects.select_related("vehicle", "driver", "route").all()
    serializer_class = VehicleAssignmentSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["vehicle", "driver", "route", "is_active"]
    ordering_fields = ["start_date", "end_date"]


class TripScheduleViewSet(viewsets.ModelViewSet):
    queryset = TripSchedule.objects.select_related("assignment").all()
    serializer_class = TripScheduleSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["assignment", "day_of_week"]
    ordering_fields = ["day_of_week", "departure_time"]


class TransportPassViewSet(viewsets.ModelViewSet):
    queryset = TransportPass.objects.select_related("user", "route", "start_stop", "end_stop").all()
    serializer_class = TransportPassSerializer
    permission_classes = [DefaultPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["user", "route", "pass_type", "is_active"]
    ordering_fields = ["valid_from", "valid_to", "price"]

    @action(detail=False, methods=["post"], url_path="bulk-assign-students")
    def bulk_assign_students(self, request):
        serializer = BulkStudentPassAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Resolve target cohort (students) via StudentBatch fields
        batches = StudentBatch.objects.filter(
            department_id=data["department_id"],
            academic_year_id=data["academic_year_id"],
            year_of_study=data["year_of_study"],
            section=data["section"],
            is_active=True,
        ).values_list("id", flat=True)

        students = Student.objects.select_related("user").filter(
            student_batch_id__in=list(batches),
            status="ACTIVE",
        ).only("id", "user_id")

        created = 0
        skipped = 0
        errors = []

        with transaction.atomic():
            for s in students:
                if not s.user_id:
                    skipped += 1
                    errors.append({"student_id": str(s.id), "reason": "No linked auth user"})
                    continue
                if data["skip_if_active_pass_exists"]:
                    exists = TransportPass.objects.filter(
                        user_id=s.user_id,
                        route=data["route"],
                        is_active=True,
                        valid_to__gte=timezone.now().date(),
                    ).exists()
                    if exists:
                        skipped += 1
                        continue

                TransportPass.objects.create(
                    user_id=s.user_id,
                    route=data["route"],
                    start_stop=data["start_stop"],
                    end_stop=data["end_stop"],
                    pass_type="STUDENT",
                    valid_from=data["valid_from"],
                    valid_to=data["valid_to"],
                    price=data["price"],
                    is_active=data["is_active"],
                )
                created += 1

        return Response({
            "ok": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "total_targeted": students.count(),
        })

    @action(detail=False, methods=["post"], url_path="bulk-assign-faculty")
    def bulk_assign_faculty(self, request):
        serializer = BulkFacultyPassAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        faculty_qs = Faculty.objects.select_related("user").filter(
            status="ACTIVE",
            currently_associated=True,
        )
        # department may be either legacy char or FK; use FK when present
        faculty_qs = faculty_qs.filter(department_ref_id=data["department_id"]) | faculty_qs.filter(
            department_ref_id__isnull=True
        )  # Will refine below
        # Refine: include those with department_ref match OR fallback where department_ref is null and legacy matches department by code
        # To avoid complex union logic here, fetch all and post-filter in python according to department_ref

        faculty = list(Faculty.objects.select_related("user").filter(
            status="ACTIVE",
            currently_associated=True,
        ))

        created = 0
        skipped = 0
        errors = []

        with transaction.atomic():
            for f in faculty:
                # Filter to requested department
                if str(getattr(f.department_ref_id, "__str__", lambda: None)()) != str(data["department_id"]) and getattr(f, "department_ref_id", None) != data["department_id"]:
                    continue

                if not f.user_id:
                    skipped += 1
                    errors.append({"faculty_id": str(f.id), "reason": "No linked auth user"})
                    continue
                if data["skip_if_active_pass_exists"]:
                    exists = TransportPass.objects.filter(
                        user_id=f.user_id,
                        route=data["route"],
                        is_active=True,
                        valid_to__gte=timezone.now().date(),
                    ).exists()
                    if exists:
                        skipped += 1
                        continue

                TransportPass.objects.create(
                    user_id=f.user_id,
                    route=data["route"],
                    start_stop=data["start_stop"],
                    end_stop=data["end_stop"],
                    pass_type="STAFF",
                    valid_from=data["valid_from"],
                    valid_to=data["valid_to"],
                    price=data["price"],
                    is_active=data["is_active"],
                )
                created += 1

        return Response({
            "ok": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
        })

