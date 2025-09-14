from django import forms
from django.core.exceptions import ValidationError
from .models import Faculty, CustomField, CustomFieldValue
from departments.models import Department


class FacultyForm(forms.ModelForm):
    """Form for creating and updating faculty members"""
    
    class Meta:
        model = Faculty
        fields = [
            'name', 'pan_no', 'apaar_faculty_id', 'highest_degree', 'university', 
            'area_of_specialization', 'date_of_joining_institution', 'designation_at_joining',
            'present_designation', 'date_designated_as_professor', 'nature_of_association',
            'contractual_full_time_part_time', 'currently_associated', 'date_of_leaving',
            'experience_in_current_institute', 'employee_id', 'first_name', 'last_name', 
            'middle_name', 'date_of_birth', 'gender', 'designation', 'department_ref', 
            'employment_type', 'date_of_joining', 'phone_number', 'alternate_phone',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 
            'country', 'highest_qualification', 'specialization', 'year_of_completion',
            'experience_years', 'previous_institution', 'achievements', 'research_interests',
            'is_head_of_department', 'is_mentor', 'mentor_for_grades', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship', 'profile_picture', 
            'bio', 'notes', 'email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_no': forms.TextInput(attrs={'class': 'form-control'}),
            'apaar_faculty_id': forms.TextInput(attrs={'class': 'form-control'}),
            'highest_degree': forms.TextInput(attrs={'class': 'form-control'}),
            'university': forms.TextInput(attrs={'class': 'form-control'}),
            'area_of_specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_joining_institution': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'designation_at_joining': forms.TextInput(attrs={'class': 'form-control'}),
            'present_designation': forms.TextInput(attrs={'class': 'form-control'}),
            'date_designated_as_professor': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nature_of_association': forms.Select(attrs={'class': 'form-control'}),
            'contractual_full_time_part_time': forms.Select(attrs={'class': 'form-control'}),
            'currently_associated': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date_of_leaving': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'experience_in_current_institute': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.Select(attrs={'class': 'form-control'}),
            'department_ref': forms.Select(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'alternate_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'highest_qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'year_of_completion': forms.NumberInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'previous_institution': forms.TextInput(attrs={'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'research_interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_head_of_department': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_mentor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mentor_for_grades': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up department choices from Department table
        self.fields['department_ref'].queryset = Department.objects.filter(
            is_active=True, 
            status='ACTIVE'
        ).order_by('name')
        self.fields['department_ref'].empty_label = "Select Department"
        self.fields['department_ref'].help_text = "Select the department from the Department table"
        
        # Make required fields more obvious
        self.fields['name'].required = True
        self.fields['apaar_faculty_id'].required = True
        self.fields['email'].required = True
        self.fields['employee_id'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['department_ref'].required = True
    
    def clean_apaar_faculty_id(self):
        apaar_faculty_id = self.cleaned_data.get('apaar_faculty_id')
        if apaar_faculty_id:
            # Check if this ID already exists (excluding current instance if updating)
            queryset = Faculty.objects.filter(apaar_faculty_id=apaar_faculty_id)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("APAAR Faculty ID already exists.")
        return apaar_faculty_id
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if this email already exists (excluding current instance if updating)
            queryset = Faculty.objects.filter(email=email)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Email already exists.")
        return email
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if employee_id:
            # Check if this employee ID already exists (excluding current instance if updating)
            queryset = Faculty.objects.filter(employee_id=employee_id)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Employee ID already exists.")
        return employee_id


class FacultyCreateForm(FacultyForm):
    """Form specifically for creating new faculty members"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Additional validation or setup for creation can go here


class FacultyUpdateForm(FacultyForm):
    """Form specifically for updating existing faculty members"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make apaar_faculty_id read-only for updates
        self.fields['apaar_faculty_id'].widget.attrs['readonly'] = True
        self.fields['apaar_faculty_id'].help_text = "APAAR Faculty ID cannot be changed after creation"


class FacultySearchForm(forms.Form):
    """Form for searching faculty members"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, employee ID, email, or phone...'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True, status='ACTIVE').order_by('name'),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Faculty.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    designation = forms.ChoiceField(
        choices=[('', 'All Designations')] + Faculty.DESIGNATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    employment_type = forms.ChoiceField(
        choices=[('', 'All Employment Types')] + Faculty.EMPLOYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
