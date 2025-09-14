from django import forms
from .models import StudentBatch, Semester, AcademicYear
from departments.models import Department
from academics.models import AcademicProgram


class StudentBatchForm(forms.ModelForm):
    """Custom form for StudentBatch that uses Semester table data"""
    
    # Add a separate field for semester selection
    semester_selection = forms.ModelChoiceField(
        queryset=Semester.objects.filter(is_active=True).order_by('academic_year__year', 'semester_type'),
        empty_label="Select Semester",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select from available semesters"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make academic_year required
        self.fields['academic_year'].required = True
        
        # Add placeholder for batch_name
        self.fields['batch_name'].widget.attrs['placeholder'] = 'e.g., CS-2024-1-A'
        self.fields['batch_code'].widget.attrs['placeholder'] = 'e.g., CS20241A'
        
        # If editing an existing instance, set the initial value for semester_selection
        if self.instance and self.instance.pk:
            semester_obj = self.instance.get_semester_object()
            if semester_obj:
                self.fields['semester_selection'].initial = semester_obj.id
    
    class Meta:
        model = StudentBatch
        fields = [
            'department', 'academic_program', 'academic_year', 'semester_selection',
            'year_of_study', 'section', 'batch_name', 'batch_code',
            'max_capacity', 'is_active'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'academic_program': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'year_of_study': forms.Select(attrs={'class': 'form-select'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'batch_name': forms.TextInput(attrs={'class': 'form-control'}),
            'batch_code': forms.TextInput(attrs={'class': 'form-control'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '200'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        academic_year = cleaned_data.get('academic_year')
        semester_selection = cleaned_data.get('semester_selection')
        year_of_study = cleaned_data.get('year_of_study')
        section = cleaned_data.get('section')
        
        # Validate that the semester belongs to the selected academic year
        if semester_selection and academic_year:
            if semester_selection.academic_year != academic_year:
                raise forms.ValidationError(
                    f"Selected semester '{semester_selection.name}' does not belong to academic year '{academic_year.year}'"
                )
        
        # Auto-generate batch_name if not provided
        if not cleaned_data.get('batch_name') and all([department, academic_year, year_of_study, section]):
            semester_str = semester_selection.semester_type if semester_selection else '1'
            cleaned_data['batch_name'] = f"{department.short_name}-{academic_year.year}-{year_of_study}-{section}"
        
        # Auto-generate batch_code if not provided
        if not cleaned_data.get('batch_code') and all([department, academic_year, year_of_study, section]):
            semester_str = semester_selection.semester_type if semester_selection else '1'
            cleaned_data['batch_code'] = f"{department.code}{academic_year.year.replace('-', '')}{year_of_study}{section}"
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Get the selected semester object
        semester_selection = self.cleaned_data.get('semester_selection')
        
        # Set the semester string based on the selected semester object
        if semester_selection:
            # Map semester type to semester string
            type_mapping = {
                'ODD': '1',
                'EVEN': '2', 
                'SUMMER': '3',
            }
            instance.semester = type_mapping.get(semester_selection.semester_type, '1')
        else:
            # Default to semester 1 if no semester is selected
            instance.semester = '1'
        
        if commit:
            instance.save()
        return instance
