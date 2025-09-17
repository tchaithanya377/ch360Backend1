from django.contrib import admin, messages
from django import forms
from django.db import transaction
from django.utils import timezone
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass
from departments.models import Department
from students.models import Student, StudentBatch
from faculty.models import Faculty
from django.contrib.admin.helpers import ActionForm
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("number_plate", "registration_number", "capacity", "is_active")
    search_fields = ("number_plate", "registration_number")
    list_filter = ("is_active",)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "license_number", "is_active")
    search_fields = ("full_name", "phone", "license_number")
    list_filter = ("is_active",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "distance_km", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ("name", "landmark", "latitude", "longitude")
    search_fields = ("name", "landmark")


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ("route", "stop", "order_index", "arrival_offset_min")
    list_filter = ("route",)


@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "driver", "route", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "route")
    autocomplete_fields = ("vehicle", "driver", "route")


@admin.register(TripSchedule)
class TripScheduleAdmin(admin.ModelAdmin):
    list_display = ("assignment", "day_of_week", "departure_time", "return_time")
    list_filter = ("day_of_week",)


@admin.register(TransportPass)
class TransportPassAdmin(admin.ModelAdmin):
    list_display = ("user", "route", "start_stop", "end_stop", "valid_from", "valid_to", "price", "is_active")
    list_filter = ("is_active", "route")
    search_fields = ("user__username", "user__email")

    class action_form(ActionForm):
        # Shared pass fields
        route = forms.ModelChoiceField(queryset=Route.objects.all(), required=False)
        start_stop = forms.ModelChoiceField(queryset=Stop.objects.all(), required=False)
        end_stop = forms.ModelChoiceField(queryset=Stop.objects.all(), required=False)
        valid_from = forms.DateField(required=False)
        valid_to = forms.DateField(required=False)
        price = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
        is_active = forms.BooleanField(required=False, initial=True)
        skip_if_active_pass_exists = forms.BooleanField(required=False, initial=True)

        # Students cohort
        student_department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
        academic_year_id = forms.IntegerField(required=False)
        year_of_study = forms.ChoiceField(choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], required=False)
        section = forms.CharField(max_length=1, required=False)

        # Faculty cohort
        faculty_department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)

    actions = ["bulk_assign_students", "bulk_assign_faculty"]

    def _clean_shared_inputs(self, request):
        try:
            route = Route.objects.get(pk=request.POST.get("route"))
            start_stop = Stop.objects.get(pk=request.POST.get("start_stop"))
            end_stop = Stop.objects.get(pk=request.POST.get("end_stop"))
            valid_from = request.POST.get("valid_from") or timezone.now().date()
            valid_to = request.POST.get("valid_to")
            price = request.POST.get("price")
            is_active = bool(request.POST.get("is_active"))
            skip = bool(request.POST.get("skip_if_active_pass_exists"))
        except Exception:
            return None, None, None, None, None, None, None
        return route, start_stop, end_stop, valid_from, valid_to, price, is_active, skip

    def bulk_assign_students(self, request, queryset):
        # Collect inputs
        try:
            route = Route.objects.get(pk=request.POST.get("route"))
            start_stop = Stop.objects.get(pk=request.POST.get("start_stop"))
            end_stop = Stop.objects.get(pk=request.POST.get("end_stop"))
            valid_from = request.POST.get("valid_from") or str(timezone.now().date())
            valid_to = request.POST.get("valid_to")
            price = request.POST.get("price")
            is_active = bool(request.POST.get("is_active"))
            skip = bool(request.POST.get("skip_if_active_pass_exists"))

            department = Department.objects.get(pk=request.POST.get("student_department"))
            academic_year_id = int(request.POST.get("academic_year_id"))
            year_of_study = request.POST.get("year_of_study")
            section = request.POST.get("section")
        except Exception as exc:
            messages.error(request, f"Invalid inputs for bulk student assignment: {exc}")
            return

        # Basic validation
        if not (route and start_stop and end_stop and valid_to and price and department and year_of_study and section):
            messages.error(request, "Please provide all required fields for student bulk assignment.")
            return

        # Resolve cohort
        batches = StudentBatch.objects.filter(
            department=department,
            academic_year_id=academic_year_id,
            year_of_study=year_of_study,
            section=section,
            is_active=True,
        ).values_list("id", flat=True)

        students = Student.objects.select_related("user").filter(
            student_batch_id__in=list(batches),
            status="ACTIVE",
        ).only("id", "user_id")

        created = 0
        skipped = 0
        errors = 0

        with transaction.atomic():
            for s in students:
                if not s.user_id:
                    errors += 1
                    continue
                if skip and TransportPass.objects.filter(
                    user_id=s.user_id,
                    route=route,
                    is_active=True,
                    valid_to__gte=timezone.now().date(),
                ).exists():
                    skipped += 1
                    continue

                TransportPass.objects.create(
                    user_id=s.user_id,
                    route=route,
                    start_stop=start_stop,
                    end_stop=end_stop,
                    pass_type="STUDENT",
                    valid_from=valid_from,
                    valid_to=valid_to,
                    price=price,
                    is_active=is_active,
                )
                created += 1

        messages.success(request, f"Student passes created: {created}, skipped: {skipped}, errors: {errors}")

    bulk_assign_students.short_description = "Bulk assign passes to Students (by Department/Year/Section)"

    def bulk_assign_faculty(self, request, queryset):
        # Collect inputs
        try:
            route = Route.objects.get(pk=request.POST.get("route"))
            start_stop = Stop.objects.get(pk=request.POST.get("start_stop"))
            end_stop = Stop.objects.get(pk=request.POST.get("end_stop"))
            valid_from = request.POST.get("valid_from") or str(timezone.now().date())
            valid_to = request.POST.get("valid_to")
            price = request.POST.get("price")
            is_active = bool(request.POST.get("is_active"))
            skip = bool(request.POST.get("skip_if_active_pass_exists"))

            department = Department.objects.get(pk=request.POST.get("faculty_department"))
        except Exception as exc:
            messages.error(request, f"Invalid inputs for bulk faculty assignment: {exc}")
            return

        if not (route and start_stop and end_stop and valid_to and price and department):
            messages.error(request, "Please provide all required fields for faculty bulk assignment.")
            return

        faculty_qs = Faculty.objects.select_related("user", "department_ref").filter(
            status="ACTIVE",
            currently_associated=True,
        )

        created = 0
        skipped = 0
        errors = 0

        with transaction.atomic():
            for f in faculty_qs:
                # Match department via FK reference
                if f.department_ref_id != department.id:
                    continue
                if not f.user_id:
                    errors += 1
                    continue
                if skip and TransportPass.objects.filter(
                    user_id=f.user_id,
                    route=route,
                    is_active=True,
                    valid_to__gte=timezone.now().date(),
                ).exists():
                    skipped += 1
                    continue

                TransportPass.objects.create(
                    user_id=f.user_id,
                    route=route,
                    start_stop=start_stop,
                    end_stop=end_stop,
                    pass_type="STAFF",
                    valid_from=valid_from,
                    valid_to=valid_to,
                    price=price,
                    is_active=is_active,
                )
                created += 1

        messages.success(request, f"Faculty passes created: {created}, skipped: {skipped}, errors: {errors}")

    bulk_assign_faculty.short_description = "Bulk assign passes to Faculty (by Department)"

    # ----------------------
    # Custom admin pages
    # ----------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('assign-students/', self.admin_site.admin_view(self.assign_students_view), name='transport_pass_assign_students'),
            path('assign-faculty/', self.admin_site.admin_view(self.assign_faculty_view), name='transport_pass_assign_faculty'),
        ]
        return custom_urls + urls

    class StudentAssignFilterForm(forms.Form):
        student_department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, label="Department")
        academic_year_id = forms.IntegerField(required=True, label="Academic Year ID")
        year_of_study = forms.ChoiceField(choices=[('1','1'),('2','2'),('3','3'),('4','4'),('5','5')], required=True)
        section = forms.CharField(max_length=1, required=True)

    class FacultyAssignFilterForm(forms.Form):
        faculty_department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, label="Department")

    class PassDetailsForm(forms.Form):
        route = forms.ModelChoiceField(queryset=Route.objects.all(), required=True)
        start_stop = forms.ModelChoiceField(queryset=Stop.objects.all(), required=True)
        end_stop = forms.ModelChoiceField(queryset=Stop.objects.all(), required=True)
        valid_from = forms.DateField(required=True, initial=timezone.now)
        valid_to = forms.DateField(required=True)
        price = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
        is_active = forms.BooleanField(required=False, initial=True)
        skip_if_active_pass_exists = forms.BooleanField(required=False, initial=True)

    def assign_students_view(self, request):
        filter_form = self.StudentAssignFilterForm(request.GET or None)
        pass_form = self.PassDetailsForm(request.POST or None)

        students = []
        if filter_form.is_valid():
            cd = filter_form.cleaned_data
            batches = StudentBatch.objects.filter(
                department=cd['student_department'],
                academic_year_id=cd['academic_year_id'],
                year_of_study=cd['year_of_study'],
                section=cd['section'],
                is_active=True,
            ).values_list('id', flat=True)
            students = list(Student.objects.select_related('user').filter(
                student_batch_id__in=list(batches),
                status='ACTIVE'
            ).only('id', 'first_name', 'last_name', 'roll_number', 'user_id'))

        if request.method == 'POST' and pass_form.is_valid():
            selected_ids = request.POST.getlist('selected_ids')
            if not selected_ids:
                messages.error(request, 'Please select at least one student.')
            else:
                pd = pass_form.cleaned_data
                created = 0
                skipped = 0
                errors = 0
                with transaction.atomic():
                    for sid in selected_ids:
                        try:
                            s = Student.objects.select_related('user').only('id', 'user_id').get(id=sid)
                        except Student.DoesNotExist:
                            errors += 1
                            continue
                        if not s.user_id:
                            errors += 1
                            continue
                        if pd['skip_if_active_pass_exists'] and TransportPass.objects.filter(
                            user_id=s.user_id,
                            route=pd['route'],
                            is_active=True,
                            valid_to__gte=timezone.now().date(),
                        ).exists():
                            skipped += 1
                            continue
                        TransportPass.objects.create(
                            user_id=s.user_id,
                            route=pd['route'],
                            start_stop=pd['start_stop'],
                            end_stop=pd['end_stop'],
                            pass_type='STUDENT',
                            valid_from=pd['valid_from'],
                            valid_to=pd['valid_to'],
                            price=pd['price'],
                            is_active=pd['is_active'],
                        )
                        created += 1
                messages.success(request, f"Student passes created: {created}, skipped: {skipped}, errors: {errors}")
                return redirect('admin:transport_pass_assign_students')

        context = dict(
            self.admin_site.each_context(request),
            title='Assign Transport Passes to Students',
            filter_form=filter_form,
            pass_form=pass_form,
            students=students,
        )
        return render(request, 'admin/transportation/assign_students.html', context)

    def assign_faculty_view(self, request):
        filter_form = self.FacultyAssignFilterForm(request.GET or None)
        pass_form = self.PassDetailsForm(request.POST or None)

        faculty = []
        if filter_form.is_valid():
            cd = filter_form.cleaned_data
            faculty = list(Faculty.objects.select_related('user', 'department_ref').filter(
                department_ref=cd['faculty_department'],
                status='ACTIVE',
                currently_associated=True,
            ).only('id', 'first_name', 'last_name', 'employee_id', 'user_id'))

        if request.method == 'POST' and pass_form.is_valid():
            selected_ids = request.POST.getlist('selected_ids')
            if not selected_ids:
                messages.error(request, 'Please select at least one faculty member.')
            else:
                pd = pass_form.cleaned_data
                created = 0
                skipped = 0
                errors = 0
                with transaction.atomic():
                    for fid in selected_ids:
                        try:
                            f = Faculty.objects.select_related('user').only('id', 'user_id').get(id=fid)
                        except Faculty.DoesNotExist:
                            errors += 1
                            continue
                        if not f.user_id:
                            errors += 1
                            continue
                        if pd['skip_if_active_pass_exists'] and TransportPass.objects.filter(
                            user_id=f.user_id,
                            route=pd['route'],
                            is_active=True,
                            valid_to__gte=timezone.now().date(),
                        ).exists():
                            skipped += 1
                            continue
                        TransportPass.objects.create(
                            user_id=f.user_id,
                            route=pd['route'],
                            start_stop=pd['start_stop'],
                            end_stop=pd['end_stop'],
                            pass_type='STAFF',
                            valid_from=pd['valid_from'],
                            valid_to=pd['valid_to'],
                            price=pd['price'],
                            is_active=pd['is_active'],
                        )
                        created += 1
                messages.success(request, f"Faculty passes created: {created}, skipped: {skipped}, errors: {errors}")
                return redirect('admin:transport_pass_assign_faculty')

        context = dict(
            self.admin_site.each_context(request),
            title='Assign Transport Passes to Faculty',
            filter_form=filter_form,
            pass_form=pass_form,
            faculty=faculty,
        )
        return render(request, 'admin/transportation/assign_faculty.html', context)

