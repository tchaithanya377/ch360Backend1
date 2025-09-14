from django import forms
from .models import Vehicle, Driver, Route, Stop, RouteStop, VehicleAssignment, TripSchedule, TransportPass


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = widget.attrs.get('class', '')
                widget.attrs['class'] = (css + ' form-select').strip()
            elif isinstance(widget, (forms.CheckboxInput,)):
                css = widget.attrs.get('class', '')
                widget.attrs['class'] = (css + ' form-check-input').strip()
            else:
                css = widget.attrs.get('class', '')
                widget.attrs['class'] = (css + ' form-control').strip()


class VehicleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'number_plate', 'registration_number', 'make', 'model',
            'capacity', 'year_of_manufacture', 'is_active'
        ]


class DriverForm(BootstrapFormMixin, forms.ModelForm):
    license_expiry = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Driver
        fields = ['full_name', 'phone', 'license_number', 'license_expiry', 'is_active', 'user']


class RouteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Route
        fields = ['name', 'description', 'distance_km', 'is_active']


class StopForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Stop
        fields = ['name', 'landmark', 'latitude', 'longitude']


class RouteStopForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = RouteStop
        fields = ['route', 'stop', 'order_index', 'arrival_offset_min']


class VehicleAssignmentForm(BootstrapFormMixin, forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = VehicleAssignment
        fields = ['vehicle', 'driver', 'route', 'start_date', 'end_date', 'is_active']

    def clean(self):
        cleaned = super().clean()
        vehicle = cleaned.get('vehicle')
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        instance_id = self.instance.pk if self.instance and self.instance.pk else None
        if vehicle and start:
            qs = VehicleAssignment.objects.filter(vehicle=vehicle, is_active=True)
            if instance_id:
                qs = qs.exclude(pk=instance_id)
            # Overlap condition: existing.start <= new.end and new.start <= existing.end (null end treated as open)
            if end:
                qs = qs.filter(start_date__lte=end).filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=start))
            else:
                qs = qs.filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=start))
            if qs.exists():
                raise forms.ValidationError('This vehicle already has an active assignment overlapping the selected dates.')
        return cleaned


class TripScheduleForm(BootstrapFormMixin, forms.ModelForm):
    departure_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    return_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    effective_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    effective_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = TripSchedule
        fields = ['assignment', 'day_of_week', 'departure_time', 'return_time', 'effective_from', 'effective_to']

    def clean(self):
        cleaned = super().clean()
        assignment = cleaned.get('assignment')
        day = cleaned.get('day_of_week')
        dep = cleaned.get('departure_time')
        eff_from = cleaned.get('effective_from')
        eff_to = cleaned.get('effective_to')
        instance_id = self.instance.pk if self.instance and self.instance.pk else None
        if assignment and day is not None and dep:
            qs = TripSchedule.objects.filter(assignment=assignment, day_of_week=day, departure_time=dep)
            if instance_id:
                qs = qs.exclude(pk=instance_id)
            if qs.exists():
                raise forms.ValidationError('A schedule with the same assignment, day, and departure time already exists.')
        if eff_to and eff_from and eff_to < eff_from:
            raise forms.ValidationError('Effective To must be on or after Effective From.')
        return cleaned


class TransportPassForm(BootstrapFormMixin, forms.ModelForm):
    valid_from = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    valid_to = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = TransportPass
        fields = ['user', 'route', 'start_stop', 'end_stop', 'pass_type', 'valid_from', 'valid_to', 'price', 'is_active']


