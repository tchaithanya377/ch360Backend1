from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction
from .models import (
    Student,
    StudentEnrollmentHistory,
    StudentDocument,
    CustomField,
    StudentCustomFieldValue,
    StudentImport,
    AcademicYear,
    Semester,
    StudentBatch,
    BulkAssignment,
    Religion,
    Caste,
    Quota,
    StudentIdentifier,
)
from .forms import StudentBatchForm


class StudentEnrollmentHistoryInline(admin.TabularInline):
    """Inline admin for student enrollment history"""
    model = StudentEnrollmentHistory
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class StudentDocumentInline(admin.TabularInline):
    """Inline admin for student documents"""
    model = StudentDocument
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'uploaded_by')


class StudentCustomFieldValueInline(admin.TabularInline):
    """Inline admin for student custom field values"""
    model = StudentCustomFieldValue
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin configuration for Student model"""
    list_display = [
        'roll_number', 'full_name', 'get_batch_info', 'status', 
        'email', 'student_mobile', 'enrollment_date', 'age'
    ]
    list_filter = [
        'status', 'student_batch', 'gender', 'quota', 'religion',
        'enrollment_date', 'created_at', 'updated_at'
    ]
    search_fields = [
        'roll_number', 'first_name', 'last_name', 'email', 
        'student_mobile', 'father_name', 'mother_name', 'guardian_name'
    ]
    readonly_fields = [
        'id', 'full_name', 'age', 'full_address', 
        'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    inlines = [StudentEnrollmentHistoryInline, StudentDocumentInline, StudentCustomFieldValueInline]
    actions = ['action_assign_to_batches_with_capacity']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'roll_number', 'first_name', 'last_name', 'middle_name',
                'date_of_birth', 'gender'
            )
        }),
        ('Academic Information', {
            'fields': (
                'student_batch', 'quota', 'rank'
            )
        }),
        ('Contact Information', {
            'fields': (
                'email', 'student_mobile', 'address_line1', 'address_line2',
                'city', 'state', 'postal_code', 'country', 'village'
            )
        }),
        ('Identity Information', {
            'fields': (
                'aadhar_number', 'religion', 'caste', 'subcaste'
            )
        }),
        ('Parent Information', {
            'fields': (
                'father_name', 'mother_name', 'father_mobile', 'mother_mobile'
            )
        }),
        ('Guardian Information', {
            'fields': (
                'guardian_name', 'guardian_phone', 'guardian_email',
                'guardian_relationship'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relationship'
            )
        }),
        ('Academic Status', {
            'fields': (
                'enrollment_date', 'expected_graduation_date', 'status'
            )
        }),
        ('Medical Information', {
            'fields': ('medical_conditions', 'medications')
        }),
        ('Additional Information', {
            'fields': ('notes', 'profile_picture')
        }),
        ('System Information', {
            'fields': (
                'id', 'full_name', 'age', 'full_address',
                'created_at', 'updated_at', 'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by or updated_by based on whether this is a new object"""
        if not change:  # New object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def age(self, obj):
        """Display student age"""
        return obj.age
    age.short_description = 'Age'
    
    def full_name(self, obj):
        """Display student full name"""
        return obj.full_name
    full_name.short_description = 'Full Name'
    
    def get_batch_info(self, obj):
        """Display batch information"""
        if obj.student_batch:
            return f"{obj.student_batch.batch_name} ({obj.student_batch.department.name if obj.student_batch.department else 'N/A'})"
        return '-'
    get_batch_info.short_description = 'Batch Info'

    @admin.action(description="Create/Update Student Batches for selected students with capacity checks")
    def action_assign_to_batches_with_capacity(self, request, queryset):
        """Group students by Department-Year-Section-AcademicYear and ensure a StudentBatch exists.

        - Creates missing batches with a default max_capacity (60)
        - Increments current_count up to capacity; skips overflow and reports
        Note: There is no explicit FK from Student to StudentBatch; this action manages batches and counts only.
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        # Map to keep track of increments per batch in this run to avoid double counting
        from collections import defaultdict
        planned_increments = defaultdict(int)

        # Preload academic years
        ay_cache = {a.year: a for a in AcademicYear.objects.all()}

        with transaction.atomic():
            for student in queryset.select_related('department'):
                if not (student.department and student.year_of_study and student.section):
                    skipped += 1
                    errors.append(f"Missing grouping fields for {student.roll_number}")
                    continue

                # Determine academic year object from student's string field or current_academic_year
                ay_str = student.academic_year or (student.current_academic_year.year if student.current_academic_year else None)
                if not ay_str:
                    skipped += 1
                    errors.append(f"Missing academic_year for {student.roll_number}")
                    continue

                ay = ay_cache.get(ay_str)
                if not ay:
                    ay = AcademicYear.objects.create(year=ay_str, start_date=student.enrollment_date, end_date=student.enrollment_date)
                    ay_cache[ay_str] = ay

                batch_name = f"{student.department.short_name}-{ay.year}-{student.year_of_study}-{student.section}"
                batch, created_flag = StudentBatch.objects.get_or_create(
                    department=student.department,
                    academic_year=ay,
                    year_of_study=student.year_of_study,
                    section=student.section,
                    defaults={
                        'batch_name': batch_name,
                        'max_capacity': 60,
                        'current_count': 0,
                        'is_active': True,
                    }
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

                # Capacity enforcement per run (not persisted link)
                if (batch.current_count + planned_increments[batch.pk]) < batch.max_capacity:
                    planned_increments[batch.pk] += 1
                else:
                    skipped += 1
                    errors.append(f"Batch full: {batch.batch_name} for {student.roll_number}")

            # Apply increments
            for batch_id, inc in planned_increments.items():
                if inc > 0:
                    b = StudentBatch.objects.select_for_update().get(pk=batch_id)
                    b.current_count = min(b.max_capacity, b.current_count + inc)
                    b.save(update_fields=['current_count'])

        msg = f"Batches created: {created}, touched: {updated}, assigned: {sum(planned_increments.values())}, skipped: {skipped}"
        if errors:
            self.message_user(request, msg + f". Issues: {len(errors)}. See admin log for details.")
        else:
            self.message_user(request, msg)


@admin.register(StudentEnrollmentHistory)
class StudentEnrollmentHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for Student Enrollment History"""
    list_display = [
        'student', 'year_of_study', 'semester', 'academic_year', 
        'enrollment_date', 'completion_date', 'status'
    ]
    list_filter = [
        'year_of_study', 'semester', 'academic_year', 'status', 
        'enrollment_date', 'completion_date'
    ]
    search_fields = [
        'student__first_name', 'student__last_name', 
        'student__student_id', 'academic_year'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': (
                'student', 'year_of_study', 'semester', 'academic_year',
                'enrollment_date', 'completion_date', 'status', 'notes'
            )
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for Student Documents"""
    list_display = [
        'student', 'document_type', 'title', 
        'uploaded_by', 'created_at'
    ]
    list_filter = [
        'document_type', 'created_at', 'updated_at'
    ]
    search_fields = [
        'student__first_name', 'student__last_name', 
        'student__student_id', 'title', 'description'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'uploaded_by'
    ]
    
    fieldsets = (
        (None, {
            'fields': (
                'student', 'document_type', 'title', 
                'description', 'document_file'
            )
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'uploaded_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set uploaded_by when saving"""
        if not change:  # New object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['is_current', 'is_active']
    search_fields = ['year']
    ordering = ['-year']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'semester_type', 'start_date', 'end_date', 'is_current', 'is_active']
    list_filter = ['semester_type', 'is_current', 'is_active', 'academic_year']
    search_fields = ['name', 'academic_year__year']
    ordering = ['academic_year__year', 'semester_type']
    autocomplete_fields = ['academic_year']


@admin.register(StudentBatch)
class StudentBatchAdmin(admin.ModelAdmin):
    form = StudentBatchForm
    list_display = ['batch_name', 'department', 'academic_year', 'semester', 'semester_name_display', 'year_of_study', 'section', 'current_count', 'max_capacity', 'is_active']
    list_filter = ['department', 'academic_year', 'semester', 'year_of_study', 'section', 'is_active']
    search_fields = ['batch_name', 'department__name', 'academic_year__year']
    ordering = ['department__name', 'academic_year__year', 'year_of_study', 'section']
    readonly_fields = ['current_count', 'created_at', 'updated_at', 'semester_name_display', 'semester_type_display', 'semester_dates_display']
    
    def semester_name_display(self, obj):
        """Display the semester name from the linked Semester object"""
        return obj.semester_name
    semester_name_display.short_description = 'Semester Name'
    
    def semester_type_display(self, obj):
        """Display the semester type from the linked Semester object"""
        return obj.semester_type or 'N/A'
    semester_type_display.short_description = 'Semester Type'
    
    def semester_dates_display(self, obj):
        """Display the semester dates from the linked Semester object"""
        if obj.semester_start_date and obj.semester_end_date:
            return f"{obj.semester_start_date} to {obj.semester_end_date}"
        return 'N/A'
    semester_dates_display.short_description = 'Semester Dates'
    
    def save_model(self, request, obj, form, change):
        """Set created_by when saving"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BulkAssignment)
class BulkAssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'operation_type', 'status', 'total_students_found', 'students_updated', 'success_rate', 'created_by', 'created_at']
    list_filter = ['operation_type', 'status', 'created_at', 'created_by']
    search_fields = ['title', 'description', 'created_by__email']
    readonly_fields = ['total_students_found', 'students_updated', 'students_failed', 'errors', 'warnings', 'started_at', 'completed_at', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation_type', 'title', 'description', 'status')
        }),
        ('Criteria & Assignment', {
            'fields': ('criteria', 'assignment_data'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('total_students_found', 'students_updated', 'students_failed', 'errors', 'warnings')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def success_rate(self, obj):
        return f"{obj.success_rate}%"
    success_rate.short_description = 'Success Rate'


@admin.register(Religion)
class ReligionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'display_name', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'display_name']
    ordering = ['display_order', 'name']
    fields = ['code', 'name', 'display_name', 'display_order', 'is_active']


@admin.register(Caste)
class CasteAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'display_name', 'display_order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category', 'display_name']
    ordering = ['display_order', 'name']
    fields = ['name', 'category', 'display_name', 'display_order', 'is_active']


@admin.register(Quota)
class QuotaAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'display_name', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name', 'display_name']
    ordering = ['display_order', 'name']
    fields = ['code', 'name', 'display_name', 'description', 'display_order', 'is_active']


@admin.register(StudentIdentifier)
class StudentIdentifierAdmin(admin.ModelAdmin):
    list_display = ['student', 'id_type', 'identifier', 'is_primary', 'is_verified']
    list_filter = ['id_type', 'is_primary', 'is_verified']
    search_fields = ['student__roll_number', 'student__first_name', 'student__last_name', 'identifier']
    ordering = ['student__roll_number', 'id_type']


@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    """Admin configuration for Custom Field model"""
    list_display = [
        'name', 'label', 'field_type', 'required', 'is_active', 'order'
    ]
    list_filter = [
        'field_type', 'required', 'is_active', 'created_at', 'updated_at'
    ]
    search_fields = ['name', 'label', 'help_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': (
                'name', 'label', 'field_type', 'required', 'help_text',
                'default_value', 'choices', 'validation_regex', 'min_value',
                'max_value', 'is_active', 'order'
            )
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentCustomFieldValue)
class StudentCustomFieldValueAdmin(admin.ModelAdmin):
    """Admin configuration for Student Custom Field Values"""
    list_display = [
        'student', 'custom_field', 'value', 'created_at'
    ]
    list_filter = [
        'custom_field__field_type', 'created_at', 'updated_at'
    ]
    search_fields = [
        'student__first_name', 'student__last_name', 'student__roll_number',
        'custom_field__name', 'custom_field__label', 'value'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': (
                'student', 'custom_field', 'value', 'file_value'
            )
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StudentImport)
class StudentImportAdmin(admin.ModelAdmin):
    """Admin configuration for Student Import model"""
    list_display = ['filename', 'status', 'success_count', 'error_count', 'total_rows', 'success_rate', 'created_by', 'created_at']
    list_filter = ['status', 'created_at', 'created_by']
    search_fields = ['filename', 'created_by__email']
    readonly_fields = ['filename', 'file_size', 'total_rows', 'success_count', 'error_count', 'warning_count', 
                      'errors', 'warnings', 'created_by', 'created_at', 'updated_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('filename', 'file_size', 'total_rows')
        }),
        ('Import Results', {
            'fields': ('status', 'success_count', 'error_count', 'warning_count')
        }),
        ('Import Options', {
            'fields': ('skip_errors', 'create_login', 'update_existing')
        }),
        ('Details', {
            'fields': ('errors', 'warnings', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def success_rate(self, obj):
        return f"{obj.success_rate}%"
    success_rate.short_description = 'Success Rate'
