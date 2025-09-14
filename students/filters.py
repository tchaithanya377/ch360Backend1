import django_filters
from django.db.models import Q
from .models import Student, StudentEnrollmentHistory, StudentDocument, CustomField, Quota, StudentBatch


class StudentFilter(django_filters.FilterSet):
    """Filter for Student model"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up querysets for ModelChoiceFilters
        self.filters['student_batch'].queryset = StudentBatch.objects.all()
    
    # Text search filters
    search = django_filters.CharFilter(method='search_filter', label='Search')
    name = django_filters.CharFilter(method='name_filter', label='Name')
    parent_name = django_filters.CharFilter(method='parent_name_filter', label='Parent Name')
    
    # Date filters
    date_of_birth_after = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='gte')
    date_of_birth_before = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Numeric filters
    age_min = django_filters.NumberFilter(method='age_filter_min', label='Minimum Age')
    age_max = django_filters.NumberFilter(method='age_filter_max', label='Maximum Age')
    
    # Choice filters
    gender = django_filters.ChoiceFilter(choices=Student.GENDER_CHOICES)
    status = django_filters.ChoiceFilter(choices=Student.STATUS_CHOICES)
    quota = django_filters.ModelChoiceFilter(field_name='quota', queryset=Quota.objects.all())
    
    # StudentBatch related filters
    student_batch = django_filters.ModelChoiceFilter(field_name='student_batch', queryset=None)
    department = django_filters.ModelChoiceFilter(field_name='student_batch__department', queryset=None)
    academic_program = django_filters.ModelChoiceFilter(field_name='student_batch__academic_program', queryset=None)
    academic_year = django_filters.ModelChoiceFilter(field_name='student_batch__academic_year', queryset=None)
    year_of_study = django_filters.ChoiceFilter(field_name='student_batch__year_of_study', choices=Student.YEAR_OF_STUDY_CHOICES)
    semester = django_filters.ChoiceFilter(field_name='student_batch__semester', choices=Student.SEMESTER_CHOICES)
    section = django_filters.ChoiceFilter(field_name='student_batch__section', choices=Student.SECTION_CHOICES)
    
    # Boolean filters
    has_login = django_filters.BooleanFilter(method='has_login_filter', label='Has Login Account')
    has_email = django_filters.BooleanFilter(method='has_email_filter', label='Has Email')
    has_mobile = django_filters.BooleanFilter(method='has_mobile_filter', label='Has Mobile')
    
    # Range filters
    rank_min = django_filters.NumberFilter(field_name='rank', lookup_expr='gte')
    rank_max = django_filters.NumberFilter(field_name='rank', lookup_expr='lte')
    
    class Meta:
        model = Student
        fields = {
            'roll_number': ['exact', 'icontains', 'startswith'],
            'first_name': ['exact', 'icontains', 'startswith'],
            'last_name': ['exact', 'icontains', 'startswith'],
            'email': ['exact', 'icontains'],
            'student_mobile': ['exact', 'icontains'],
            'father_name': ['exact', 'icontains'],
            'mother_name': ['exact', 'icontains'],
            'father_mobile': ['exact', 'icontains'],
            'mother_mobile': ['exact', 'icontains'],
            'village': ['exact', 'icontains'],
            'city': ['exact', 'icontains'],
            'state': ['exact', 'icontains'],
            # Foreign keys: allow exact by id, name icontains via related field
            'religion': ['exact'],
            'caste': ['exact'],
            'religion__name': ['icontains'],
            'caste__name': ['icontains'],
            'subcaste': ['exact', 'icontains'],
            # StudentBatch related fields
            'student_batch': ['exact'],
            'student_batch__department': ['exact'],
            'student_batch__department__name': ['icontains'],
            'student_batch__department__code': ['exact', 'icontains'],
            'student_batch__academic_program': ['exact'],
            'student_batch__academic_program__name': ['icontains'],
            'student_batch__academic_program__code': ['exact', 'icontains'],
            'student_batch__academic_year': ['exact'],
            'student_batch__academic_year__year': ['exact', 'icontains'],
            'student_batch__year_of_study': ['exact'],
            'student_batch__semester': ['exact'],
            'student_batch__section': ['exact'],
        }
    
    def search_filter(self, queryset, name, value):
        """Search across multiple fields"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(roll_number__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(middle_name__icontains=value) |
            Q(email__icontains=value) |
            Q(father_name__icontains=value) |
            Q(mother_name__icontains=value) |
            Q(student_mobile__icontains=value) |
            Q(village__icontains=value) |
            Q(city__icontains=value) |
            Q(state__icontains=value) |
            Q(student_batch__academic_year__year__icontains=value) |
            Q(student_batch__department__name__icontains=value) |
            Q(student_batch__department__code__icontains=value) |
            Q(student_batch__academic_program__name__icontains=value) |
            Q(student_batch__academic_program__code__icontains=value) |
            Q(student_batch__batch_name__icontains=value) |
            Q(student_batch__batch_code__icontains=value)
        )
    
    def name_filter(self, queryset, name, value):
        """Filter by student name (first, last, or middle)"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(middle_name__icontains=value)
        )
    
    def parent_name_filter(self, queryset, name, value):
        """Filter by parent name (father or mother)"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(father_name__icontains=value) |
            Q(mother_name__icontains=value)
        )
    
    def age_filter_min(self, queryset, name, value):
        """Filter by minimum age"""
        if value is None:
            return queryset
        
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        max_birth_date = date.today() - relativedelta(years=value)
        return queryset.filter(date_of_birth__lte=max_birth_date)
    
    def age_filter_max(self, queryset, name, value):
        """Filter by maximum age"""
        if value is None:
            return queryset
        
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        min_birth_date = date.today() - relativedelta(years=value + 1)
        return queryset.filter(date_of_birth__gt=min_birth_date)
    
    def has_login_filter(self, queryset, name, value):
        """Filter by whether student has login account"""
        if value is None:
            return queryset
        
        if value:
            return queryset.filter(user__isnull=False)
        else:
            return queryset.filter(user__isnull=True)
    
    def has_email_filter(self, queryset, name, value):
        """Filter by whether student has email"""
        if value is None:
            return queryset
        
        if value:
            return queryset.exclude(email__isnull=True).exclude(email='')
        else:
            return queryset.filter(Q(email__isnull=True) | Q(email=''))
    
    def has_mobile_filter(self, queryset, name, value):
        """Filter by whether student has mobile number"""
        if value is None:
            return queryset
        
        if value:
            return queryset.exclude(student_mobile__isnull=True).exclude(student_mobile='')
        else:
            return queryset.filter(Q(student_mobile__isnull=True) | Q(student_mobile=''))


class StudentEnrollmentHistoryFilter(django_filters.FilterSet):
    """Filter for StudentEnrollmentHistory model"""
    
    search = django_filters.CharFilter(method='search_filter', label='Search')
    enrollment_date_after = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='gte')
    enrollment_date_before = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='lte')
    
    class Meta:
        model = StudentEnrollmentHistory
        fields = {
            'student__roll_number': ['exact', 'icontains'],
            'student__first_name': ['exact', 'icontains'],
            'student__last_name': ['exact', 'icontains'],
            'academic_year': ['exact', 'icontains'],
            'year_of_study': ['exact'],
            'semester': ['exact'],
            'status': ['exact'],
        }
    
    def search_filter(self, queryset, name, value):
        """Search across student and enrollment fields"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(student__roll_number__icontains=value) |
            Q(student__first_name__icontains=value) |
            Q(student__last_name__icontains=value) |
            Q(academic_year__icontains=value) |
            Q(remarks__icontains=value)
        )


class StudentDocumentFilter(django_filters.FilterSet):
    """Filter for StudentDocument model"""
    
    search = django_filters.CharFilter(method='search_filter', label='Search')
    uploaded_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    uploaded_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = StudentDocument
        fields = {
            'student__roll_number': ['exact', 'icontains'],
            'student__first_name': ['exact', 'icontains'],
            'student__last_name': ['exact', 'icontains'],
            'document_type': ['exact'],
            'title': ['exact', 'icontains'],
            'description': ['icontains'],
            'uploaded_by__email': ['exact', 'icontains'],
        }
    
    def search_filter(self, queryset, name, value):
        """Search across document and student fields"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(student__roll_number__icontains=value) |
            Q(student__first_name__icontains=value) |
            Q(student__last_name__icontains=value) |
            Q(title__icontains=value) |
            Q(description__icontains=value)
        )


class CustomFieldFilter(django_filters.FilterSet):
    """Filter for CustomField model"""
    
    search = django_filters.CharFilter(method='search_filter', label='Search')
    
    class Meta:
        model = CustomField
        fields = {
            'name': ['exact', 'icontains'],
            'label': ['exact', 'icontains'],
            'field_type': ['exact'],
            'required': ['exact'],
            'is_active': ['exact'],
            'help_text': ['icontains'],
        }
    
    def search_filter(self, queryset, name, value):
        """Search across custom field fields"""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(label__icontains=value) |
            Q(help_text__icontains=value)
        )
