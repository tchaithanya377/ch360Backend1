from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Assignment, AssignmentSubmission, AssignmentCategory, 
    AssignmentTemplate, AssignmentGrade, AssignmentComment
)
from students.models import AcademicYear, Semester

User = get_user_model()


class AssignmentForm(forms.ModelForm):
    """Form for creating and editing assignments"""
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'instructions', 'category', 'max_marks',
            'due_date', 'late_submission_allowed', 'is_group_assignment',
            'max_group_size', 'academic_year', 'semester',
            'assigned_to_programs', 'assigned_to_departments', 
            'assigned_to_courses', 'assigned_to_course_sections', 'assigned_to_students'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter assignment title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the assignment requirements and objectives'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Provide specific instructions for completing the assignment'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '100'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'min': '2024-01-01T00:00'
            }),
            'max_group_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-select'
            }),
            'semester': forms.Select(attrs={
                'class': 'form-select'
            }),
            'assigned_to_programs': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'assigned_to_departments': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'assigned_to_courses': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'assigned_to_course_sections': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'assigned_to_students': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'late_submission_allowed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_group_assignment': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AssignmentCategory.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Select Category"
        
        # Set up academic year and semester fields
        self.fields['academic_year'].queryset = AcademicYear.objects.filter(is_active=True)
        self.fields['academic_year'].empty_label = "Select Academic Year"
        self.fields['semester'].queryset = Semester.objects.filter(is_active=True)
        self.fields['semester'].empty_label = "Select Semester"
        
        # Make assignment target fields optional
        self.fields['assigned_to_programs'].required = False
        self.fields['assigned_to_departments'].required = False
        self.fields['assigned_to_courses'].required = False
        self.fields['assigned_to_course_sections'].required = False
        self.fields['assigned_to_students'].required = False
        self.fields['academic_year'].required = False
        self.fields['semester'].required = False
        
        # Set default values
        self.fields['max_group_size'].initial = 1
        self.fields['late_submission_allowed'].initial = False
        self.fields['is_group_assignment'].initial = False
        
        # Add data attributes for JavaScript
        self.fields['academic_year'].widget.attrs.update({
            'data-target': 'semester',
            'data-url': '/api/semesters/'  # This would be an API endpoint to get semesters
        })
    
    def clean(self):
        cleaned_data = super().clean()
        is_group_assignment = cleaned_data.get('is_group_assignment')
        max_group_size = cleaned_data.get('max_group_size')
        academic_year = cleaned_data.get('academic_year')
        semester = cleaned_data.get('semester')
        
        if is_group_assignment and max_group_size < 2:
            raise forms.ValidationError("Group assignments must have a maximum group size of at least 2.")
        
        # Validate that semester belongs to the selected academic year
        if academic_year and semester and semester.academic_year != academic_year:
            raise forms.ValidationError("The selected semester does not belong to the selected academic year.")
        
        return cleaned_data


class AssignmentSubmissionForm(forms.ModelForm):
    """Form for student assignment submissions"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['content', 'notes']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter your assignment content here. You can include text, code, explanations, or any other content required for the assignment.',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any additional notes, comments, or clarifications about your submission.'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['notes'].required = False


class AssignmentGradeForm(forms.ModelForm):
    """Form for grading assignment submissions"""
    
    class Meta:
        model = AssignmentGrade
        fields = ['marks_obtained', 'grade_letter', 'feedback']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0'
            }),
            'grade_letter': forms.Select(attrs={
                'class': 'form-select'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide constructive feedback to help the student improve...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['marks_obtained'].required = True
        self.fields['grade_letter'].required = False
        self.fields['feedback'].required = False
        
        # Add empty option for grade_letter
        self.fields['grade_letter'].empty_label = "Select Grade"


class AssignmentCategoryForm(forms.ModelForm):
    """Form for creating and editing assignment categories"""
    
    class Meta:
        model = AssignmentCategory
        fields = ['name', 'description', 'color_code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter category description (optional)'
            }),
            'color_code': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#007bff'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['description'].required = False
        self.fields['color_code'].required = True
        self.fields['is_active'].initial = True


class AssignmentTemplateForm(forms.ModelForm):
    """Form for creating and editing assignment templates"""
    
    class Meta:
        model = AssignmentTemplate
        fields = [
            'name', 'description', 'instructions', 'category', 'max_marks',
            'is_group_assignment', 'max_group_size', 'is_public'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter template description'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter default instructions for this template'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'max_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': '100'
            }),
            'max_group_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'is_group_assignment': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AssignmentCategory.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Select Category"
        self.fields['max_group_size'].initial = 1
        self.fields['is_group_assignment'].initial = False
        self.fields['is_public'].initial = False


class AssignmentCommentForm(forms.ModelForm):
    """Form for adding comments to assignments"""
    
    class Meta:
        model = AssignmentComment
        fields = ['content', 'comment_type']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...'
            }),
            'comment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['comment_type'].initial = 'GENERAL'


class AssignmentSearchForm(forms.Form):
    """Form for searching and filtering assignments"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search assignments...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Assignment.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=AssignmentCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    overdue = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Overdue Only')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class AssignmentFileUploadForm(forms.Form):
    """Form for uploading assignment files"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif,.zip,.rar'
        })
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'File description (optional)'
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("File size cannot exceed 10MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(f"File type .{file_extension} is not allowed.")
        
        return file


class BulkAssignmentForm(forms.Form):
    """Form for bulk operations on assignments"""
    
    ACTION_CHOICES = [
        ('publish', 'Publish Selected'),
        ('close', 'Close Selected'),
        ('delete', 'Delete Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    assignment_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean_assignment_ids(self):
        assignment_ids = self.cleaned_data.get('assignment_ids')
        if not assignment_ids:
            raise forms.ValidationError("No assignments selected.")
        
        try:
            # Convert comma-separated string to list of UUIDs
            ids = [id.strip() for id in assignment_ids.split(',') if id.strip()]
            if not ids:
                raise forms.ValidationError("No valid assignment IDs provided.")
            return ids
        except Exception:
            raise forms.ValidationError("Invalid assignment IDs format.")


class AssignmentStatisticsForm(forms.Form):
    """Form for filtering assignment statistics"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    faculty = forms.ModelChoiceField(
        queryset=User.objects.filter(faculty_profile__isnull=False),
        required=False,
        empty_label="All Faculty",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=AssignmentCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError("Start date cannot be after end date.")
        
        return cleaned_data
