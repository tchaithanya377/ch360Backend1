import django_filters
from django.db.models import Q
from .models import Assignment, AssignmentSubmission, AssignmentCategory


class AssignmentFilter(django_filters.FilterSet):
    """Filter for Assignment model"""
    
    title = django_filters.CharFilter(lookup_expr='icontains')
    faculty_name = django_filters.CharFilter(field_name='faculty__name', lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=AssignmentCategory.objects.filter(is_active=True))
    status = django_filters.ChoiceFilter(choices=Assignment.STATUS_CHOICES)
    is_group_assignment = django_filters.BooleanFilter()
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')
    due_date_after = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')
    due_date_before = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    max_marks_min = django_filters.NumberFilter(field_name='max_marks', lookup_expr='gte')
    max_marks_max = django_filters.NumberFilter(field_name='max_marks', lookup_expr='lte')
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'faculty_name', 'category', 'status', 'is_group_assignment',
            'is_overdue', 'due_date_after', 'due_date_before', 'max_marks_min', 'max_marks_max'
        ]
    
    def filter_overdue(self, queryset, name, value):
        """Filter for overdue assignments"""
        from django.utils import timezone
        if value:
            return queryset.filter(
                status='PUBLISHED',
                due_date__lt=timezone.now()
            )
        return queryset


class AssignmentSubmissionFilter(django_filters.FilterSet):
    """Filter for AssignmentSubmission model"""
    
    student_name = django_filters.CharFilter(field_name='student__name', lookup_expr='icontains')
    assignment_title = django_filters.CharFilter(field_name='assignment__title', lookup_expr='icontains')
    faculty_name = django_filters.CharFilter(field_name='assignment__faculty__name', lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=AssignmentSubmission.STATUS_CHOICES)
    is_late = django_filters.BooleanFilter()
    is_graded = django_filters.BooleanFilter(method='filter_graded')
    submission_date_after = django_filters.DateTimeFilter(field_name='submission_date', lookup_expr='gte')
    submission_date_before = django_filters.DateTimeFilter(field_name='submission_date', lookup_expr='lte')
    grade_min = django_filters.NumberFilter(field_name='grade__marks_obtained', lookup_expr='gte')
    grade_max = django_filters.NumberFilter(field_name='grade__marks_obtained', lookup_expr='lte')
    
    class Meta:
        model = AssignmentSubmission
        fields = [
            'student_name', 'assignment_title', 'faculty_name', 'status', 'is_late',
            'is_graded', 'submission_date_after', 'submission_date_before', 'grade_min', 'grade_max'
        ]
    
    def filter_graded(self, queryset, name, value):
        """Filter for graded/ungraded submissions"""
        if value:
            return queryset.filter(grade__isnull=False)
        return queryset.filter(grade__isnull=True)


class AssignmentCategoryFilter(django_filters.FilterSet):
    """Filter for AssignmentCategory model"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    
    class Meta:
        model = AssignmentCategory
        fields = ['name', 'is_active']
