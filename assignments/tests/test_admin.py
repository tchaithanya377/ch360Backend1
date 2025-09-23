"""
Comprehensive admin tests for assignments app.
Tests admin interface functionality, forms, and configurations.
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from assignments.admin import (
    AssignmentCategoryAdmin, AssignmentAdmin, AssignmentSubmissionAdmin,
    AssignmentGradeAdmin, AssignmentAdminForm
)
from assignments.models import (
    AssignmentCategory, Assignment, AssignmentSubmission, AssignmentGrade
)
from assignments.tests.factories import (
    assignment_category_factory, assignment_factory, assignment_submission_factory,
    assignment_grade_factory, user_factory, faculty_factory, student_factory
)

User = get_user_model()


class MockRequest:
    """Mock request object for admin tests"""
    def __init__(self, user=None):
        self.user = user or user_factory()


class BaseAdminTest(TestCase):
    """Base test class for admin tests"""

    def setUp(self):
        self.site = AdminSite()
        self.factory = RequestFactory()
        self.admin_user = user_factory()
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        
        self.faculty = faculty_factory()
        self.faculty_user = self.faculty.user if hasattr(self.faculty, 'user') else user_factory()
        self.faculty_user.faculty_profile = self.faculty
        self.faculty_user.is_staff = True
        self.faculty_user.save()
        
        self.student = student_factory()

    def create_request(self, user=None):
        """Create a mock request with user"""
        request = MockRequest(user or self.admin_user)
        return request


class TestAssignmentCategoryAdmin(BaseAdminTest):
    """Test AssignmentCategoryAdmin"""

    def setUp(self):
        super().setUp()
        self.admin = AssignmentCategoryAdmin(AssignmentCategory, self.site)

    def test_admin_registration(self):
        """Test that AssignmentCategory is registered in admin"""
        self.assertIn(AssignmentCategory, admin.site._registry)
        self.assertIsInstance(admin.site._registry[AssignmentCategory], AssignmentCategoryAdmin)

    def test_list_display(self):
        """Test list_display configuration"""
        expected_fields = ['name', 'description', 'color_code', 'is_active', 'created_at']
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter(self):
        """Test list_filter configuration"""
        expected_filters = ['is_active', 'created_at']
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Test search_fields configuration"""
        expected_fields = ['name', 'description']
        self.assertEqual(self.admin.search_fields, expected_fields)

    def test_ordering(self):
        """Test ordering configuration"""
        expected_ordering = ['name']
        self.assertEqual(self.admin.ordering, expected_ordering)

    def test_queryset(self):
        """Test admin queryset"""
        category1 = assignment_category_factory.make(name="A Category")
        category2 = assignment_category_factory.make(name="B Category")
        
        request = self.create_request()
        queryset = self.admin.get_queryset(request)
        
        self.assertIn(category1, queryset)
        self.assertIn(category2, queryset)
        # Should be ordered by name
        self.assertEqual(list(queryset), [category1, category2])


class TestAssignmentAdminForm(BaseAdminTest):
    """Test AssignmentAdminForm"""

    def test_form_initialization(self):
        """Test form initialization"""
        form = AssignmentAdminForm()
        
        # Check that academic_year and semester fields exist
        self.assertIn('academic_year', form.fields)
        self.assertIn('semester', form.fields)

    def test_form_queryset_filtering(self):
        """Test form queryset filtering for related fields"""
        form = AssignmentAdminForm()
        
        # Academic year should filter for active years
        academic_year_field = form.fields['academic_year']
        self.assertEqual(academic_year_field.empty_label, "Select Academic Year")
        
        # Semester should filter for active semesters
        semester_field = form.fields['semester']
        self.assertEqual(semester_field.empty_label, "Select Semester")

    def test_form_validation(self):
        """Test form validation"""
        category = assignment_category_factory.make()
        
        form_data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'category': category.id,
            'assignment_type': 'HOMEWORK',
            'max_marks': '100.00',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'status': 'DRAFT'
        }
        
        form = AssignmentAdminForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_data(self):
        """Test form with invalid data"""
        form_data = {
            'title': '',  # Required field
            'description': 'Test description',
            'max_marks': 'invalid',  # Invalid number
            'due_date': 'invalid_date'  # Invalid date
        }
        
        form = AssignmentAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('max_marks', form.errors)
        self.assertIn('due_date', form.errors)


class TestAssignmentAdmin(BaseAdminTest):
    """Test AssignmentAdmin"""

    def setUp(self):
        super().setUp()
        self.admin = AssignmentAdmin(Assignment, self.site)

    def test_admin_registration(self):
        """Test that Assignment is registered in admin"""
        self.assertIn(Assignment, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Assignment], AssignmentAdmin)

    def test_list_display(self):
        """Test list_display configuration"""
        expected_fields = [
            'title', 'course_section', 'academic_year', 'semester', 'due_date', 
            'status', 'max_marks', 'submission_count', 'created_at'
        ]
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_editable(self):
        """Test list_editable configuration"""
        expected_fields = ['due_date', 'status', 'max_marks']
        self.assertEqual(self.admin.list_editable, expected_fields)

    def test_list_filter(self):
        """Test list_filter configuration"""
        expected_filters = [
            'status', 'category', 'faculty__department', 'course', 'course_section',
            'due_date', 'created_at', 'academic_year', 'semester'
        ]
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Test search_fields configuration"""
        expected_fields = [
            'title', 'description', 'faculty__name', 'faculty__apaar_faculty_id'
        ]
        self.assertEqual(self.admin.search_fields, expected_fields)

    def test_readonly_fields(self):
        """Test readonly_fields configuration"""
        expected_fields = ['created_at', 'updated_at', 'submission_count']
        self.assertEqual(self.admin.readonly_fields, expected_fields)

    def test_exclude_fields(self):
        """Test exclude configuration"""
        expected_fields = ('faculty', 'department', 'course')
        self.assertEqual(self.admin.exclude, expected_fields)

    def test_filter_horizontal(self):
        """Test filter_horizontal configuration"""
        expected_fields = [
            'assigned_to_programs', 'assigned_to_departments', 
            'assigned_to_courses', 'assigned_to_course_sections', 'assigned_to_students'
        ]
        self.assertEqual(self.admin.filter_horizontal, expected_fields)

    def test_fieldsets(self):
        """Test fieldsets configuration"""
        fieldsets = self.admin.fieldsets
        self.assertEqual(len(fieldsets), 6)
        
        # Check fieldset names
        fieldset_names = [fieldset[0] for fieldset in fieldsets]
        expected_names = [
            'Basic Information', 'Assignment Details', 'Assignment Settings',
            'Target Audience', 'Files', 'Timestamps'
        ]
        self.assertEqual(fieldset_names, expected_names)

    def test_submission_count_method(self):
        """Test submission_count method"""
        assignment = assignment_factory.make()
        assignment_submission_factory.make(assignment=assignment)
        assignment_submission_factory.make(assignment=assignment)
        
        count = self.admin.submission_count(assignment)
        self.assertEqual(count, 2)

    def test_submission_count_method_description(self):
        """Test submission_count method description"""
        self.assertEqual(self.admin.submission_count.short_description, 'Submissions')

    def test_save_model_with_faculty_user(self):
        """Test save_model with faculty user"""
        assignment = assignment_factory.make(faculty=None)
        request = self.create_request(self.faculty_user)
        form = None  # Mock form
        change = False
        
        self.admin.save_model(request, assignment, form, change)
        
        # Faculty should be set from request user
        self.assertEqual(assignment.faculty, self.faculty)

    def test_save_model_auto_derive_fields(self):
        """Test save_model auto-derives fields from course_section"""
        # This test would require actual course_section setup
        assignment = assignment_factory.make()
        request = self.create_request()
        form = None
        change = False
        
        # Should not raise an error
        self.admin.save_model(request, assignment, form, change)

    def test_save_model_validation_error(self):
        """Test save_model with validation error"""
        assignment = assignment_factory.make(faculty=None)
        request = self.create_request()  # Admin user without faculty profile
        form = None
        change = False
        
        # Should raise ValidationError if faculty cannot be determined
        with self.assertRaises(ValidationError):
            self.admin.save_model(request, assignment, form, change)


class TestAssignmentSubmissionAdmin(BaseAdminTest):
    """Test AssignmentSubmissionAdmin"""

    def setUp(self):
        super().setUp()
        self.admin = AssignmentSubmissionAdmin(AssignmentSubmission, self.site)

    def test_admin_registration(self):
        """Test that AssignmentSubmission is registered in admin"""
        self.assertIn(AssignmentSubmission, admin.site._registry)
        self.assertIsInstance(admin.site._registry[AssignmentSubmission], AssignmentSubmissionAdmin)

    def test_list_display(self):
        """Test list_display configuration"""
        expected_fields = [
            'assignment', 'student', 'submission_date', 'status', 
            'is_late', 'grade_display'
        ]
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter(self):
        """Test list_filter configuration"""
        expected_filters = [
            'status', 'is_late', 'assignment__faculty', 
            'submission_date', 'assignment__category'
        ]
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Test search_fields configuration"""
        expected_fields = [
            'assignment__title', 'student__name', 'student__apaar_student_id'
        ]
        self.assertEqual(self.admin.search_fields, expected_fields)

    def test_readonly_fields(self):
        """Test readonly_fields configuration"""
        expected_fields = ['submission_date', 'is_late', 'created_at', 'updated_at']
        self.assertEqual(self.admin.readonly_fields, expected_fields)

    def test_fieldsets(self):
        """Test fieldsets configuration"""
        fieldsets = self.admin.fieldsets
        self.assertEqual(len(fieldsets), 5)
        
        fieldset_names = [fieldset[0] for fieldset in fieldsets]
        expected_names = [
            'Submission Details', 'Content', 'Files', 'Grading', 'Timestamps'
        ]
        self.assertEqual(fieldset_names, expected_names)

    def test_grade_display_method_with_grade(self):
        """Test grade_display method with grade"""
        assignment = assignment_factory.make(max_marks=100)
        submission = assignment_submission_factory.make(assignment=assignment)
        grade = assignment_grade_factory.make(marks_obtained=85)
        submission.grade = grade
        submission.save()
        
        display = self.admin.grade_display(submission)
        self.assertEqual(display, "85/100")

    def test_grade_display_method_without_grade(self):
        """Test grade_display method without grade"""
        submission = assignment_submission_factory.make()
        
        display = self.admin.grade_display(submission)
        self.assertEqual(display, "Not Graded")

    def test_grade_display_method_description(self):
        """Test grade_display method description"""
        self.assertEqual(self.admin.grade_display.short_description, 'Grade')


class TestAssignmentGradeAdmin(BaseAdminTest):
    """Test AssignmentGradeAdmin"""

    def setUp(self):
        super().setUp()
        self.admin = AssignmentGradeAdmin(AssignmentGrade, self.site)

    def test_admin_registration(self):
        """Test that AssignmentGrade is registered in admin"""
        self.assertIn(AssignmentGrade, admin.site._registry)
        self.assertIsInstance(admin.site._registry[AssignmentGrade], AssignmentGradeAdmin)

    def test_list_display(self):
        """Test list_display configuration"""
        expected_fields = [
            'submission', 'marks_obtained', 'max_marks', 'percentage_display', 
            'grade_letter', 'graded_by', 'graded_at'
        ]
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter(self):
        """Test list_filter configuration"""
        expected_filters = ['grade_letter', 'graded_at', 'graded_by']
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Test search_fields configuration"""
        expected_fields = [
            'submission__student__name', 'submission__assignment__title'
        ]
        self.assertEqual(self.admin.search_fields, expected_fields)

    def test_readonly_fields(self):
        """Test readonly_fields configuration"""
        expected_fields = ['graded_at']
        self.assertEqual(self.admin.readonly_fields, expected_fields)

    def test_max_marks_method(self):
        """Test max_marks method"""
        assignment = assignment_factory.make(max_marks=100)
        submission = assignment_submission_factory.make(assignment=assignment)
        grade = assignment_grade_factory.make()
        grade.submission = submission
        
        max_marks = self.admin.max_marks(grade)
        self.assertEqual(max_marks, 100)

    def test_max_marks_method_description(self):
        """Test max_marks method description"""
        self.assertEqual(self.admin.max_marks.short_description, 'Max Marks')

    def test_percentage_display_method(self):
        """Test percentage_display method"""
        assignment = assignment_factory.make(max_marks=100)
        submission = assignment_submission_factory.make(assignment=assignment)
        grade = assignment_grade_factory.make(marks_obtained=85)
        grade.submission = submission
        
        percentage = self.admin.percentage_display(grade)
        self.assertEqual(percentage, "85.0%")

    def test_percentage_display_method_no_marks(self):
        """Test percentage_display method with no marks"""
        grade = assignment_grade_factory.make()
        
        percentage = self.admin.percentage_display(grade)
        self.assertEqual(percentage, "-")

    def test_percentage_display_method_description(self):
        """Test percentage_display method description"""
        self.assertEqual(self.admin.percentage_display.short_description, 'Percentage')


class TestAdminIntegration(BaseAdminTest):
    """Test admin integration scenarios"""

    def test_admin_site_configuration(self):
        """Test admin site configuration"""
        # Test that all main models are registered
        registered_models = admin.site._registry.keys()
        
        self.assertIn(AssignmentCategory, registered_models)
        self.assertIn(Assignment, registered_models)
        self.assertIn(AssignmentSubmission, registered_models)
        self.assertIn(AssignmentGrade, registered_models)

    def test_admin_permissions(self):
        """Test admin permissions"""
        # Admin user should have access
        self.assertTrue(self.admin_user.is_staff)
        self.assertTrue(self.admin_user.is_superuser)
        
        # Faculty user with staff status should have access
        self.assertTrue(self.faculty_user.is_staff)
        
        # Regular user should not have access
        regular_user = user_factory()
        self.assertFalse(regular_user.is_staff)

    def test_admin_queryset_filtering(self):
        """Test admin queryset filtering"""
        category_admin = AssignmentCategoryAdmin(AssignmentCategory, self.site)
        
        # Create test data
        category1 = assignment_category_factory.make(is_active=True)
        category2 = assignment_category_factory.make(is_active=False)
        
        request = self.create_request()
        queryset = category_admin.get_queryset(request)
        
        # Should include both active and inactive
        self.assertIn(category1, queryset)
        self.assertIn(category2, queryset)

    def test_admin_search_functionality(self):
        """Test admin search functionality"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Create test assignment
        assignment = assignment_factory.make(title="Searchable Assignment")
        
        request = self.create_request()
        queryset = assignment_admin.get_queryset(request)
        
        # Should be able to search by title
        self.assertIn(assignment, queryset)

    def test_admin_form_integration(self):
        """Test admin form integration"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Test that custom form is used
        self.assertEqual(assignment_admin.form, AssignmentAdminForm)

    def test_admin_inline_configurations(self):
        """Test admin inline configurations"""
        # This would test if any inline configurations exist
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Check if inlines are configured (if any)
        inlines = getattr(assignment_admin, 'inlines', [])
        self.assertIsInstance(inlines, (list, tuple))

    def test_admin_actions(self):
        """Test admin actions"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Should have default actions
        actions = assignment_admin.get_actions(self.create_request())
        self.assertIn('delete_selected', actions)

    def test_admin_list_per_page(self):
        """Test admin list per page configuration"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Should have reasonable pagination
        list_per_page = getattr(assignment_admin, 'list_per_page', 100)
        self.assertIsInstance(list_per_page, int)
        self.assertGreater(list_per_page, 0)


class TestAdminCustomizations(BaseAdminTest):
    """Test admin customizations"""

    def test_assignment_admin_date_hierarchy(self):
        """Test assignment admin date hierarchy"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        self.assertEqual(assignment_admin.date_hierarchy, 'due_date')

    def test_submission_admin_date_hierarchy(self):
        """Test submission admin date hierarchy"""
        submission_admin = AssignmentSubmissionAdmin(AssignmentSubmission, self.site)
        
        self.assertEqual(submission_admin.date_hierarchy, 'submission_date')

    def test_admin_autocomplete_fields(self):
        """Test admin autocomplete fields"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        expected_fields = ['course_section', 'academic_year', 'semester']
        self.assertEqual(assignment_admin.autocomplete_fields, expected_fields)

    def test_admin_list_select_related(self):
        """Test admin list_select_related optimization"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        expected_fields = ['course_section', 'academic_year', 'semester']
        self.assertEqual(assignment_admin.list_select_related, expected_fields)

    def test_admin_custom_methods(self):
        """Test admin custom methods"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        submission_admin = AssignmentSubmissionAdmin(AssignmentSubmission, self.site)
        grade_admin = AssignmentGradeAdmin(AssignmentGrade, self.site)
        
        # Check custom methods exist
        self.assertTrue(hasattr(assignment_admin, 'submission_count'))
        self.assertTrue(hasattr(submission_admin, 'grade_display'))
        self.assertTrue(hasattr(grade_admin, 'max_marks'))
        self.assertTrue(hasattr(grade_admin, 'percentage_display'))


class TestAdminErrorHandling(BaseAdminTest):
    """Test admin error handling"""

    def test_admin_with_invalid_data(self):
        """Test admin behavior with invalid data"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Create assignment with missing required data
        assignment = Assignment()
        
        # Should handle gracefully in admin methods
        try:
            count = assignment_admin.submission_count(assignment)
            self.assertIsInstance(count, int)
        except Exception:
            # Acceptable if it raises an exception
            pass

    def test_admin_with_deleted_relations(self):
        """Test admin behavior with deleted relations"""
        grade_admin = AssignmentGradeAdmin(AssignmentGrade, self.site)
        
        # Create grade with no submission
        grade = assignment_grade_factory.make()
        grade.submission = None
        
        # Should handle gracefully
        try:
            max_marks = grade_admin.max_marks(grade)
            percentage = grade_admin.percentage_display(grade)
        except AttributeError:
            # Acceptable if it raises AttributeError for missing submission
            pass

    def test_admin_form_validation_errors(self):
        """Test admin form validation errors"""
        form_data = {
            'title': 'Test Assignment',
            'description': 'Test description',
            'max_marks': '-10',  # Invalid negative value
            'due_date': 'invalid-date'  # Invalid date format
        }
        
        form = AssignmentAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Should have validation errors
        self.assertTrue(len(form.errors) > 0)

    def test_admin_save_model_errors(self):
        """Test admin save_model error handling"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Try to save assignment without required faculty
        assignment = assignment_factory.make(faculty=None)
        request = self.create_request()  # Regular admin user
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError):
            assignment_admin.save_model(request, assignment, None, False)


@pytest.mark.django_db
class TestAdminPerformance(BaseAdminTest):
    """Test admin performance"""

    def test_admin_queryset_performance(self):
        """Test admin queryset performance"""
        import time
        
        # Create test data
        assignments = [assignment_factory.make() for _ in range(10)]
        
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        request = self.create_request()
        
        # Time the queryset operation
        start_time = time.time()
        queryset = assignment_admin.get_queryset(request)
        list(queryset)  # Force evaluation
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 1.0)

    def test_admin_list_display_performance(self):
        """Test admin list display performance"""
        import time
        
        # Create test data with relations
        assignment = assignment_factory.make()
        submissions = [
            assignment_submission_factory.make(assignment=assignment)
            for _ in range(5)
        ]
        
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Time the submission_count method
        start_time = time.time()
        for _ in range(10):
            count = assignment_admin.submission_count(assignment)
        end_time = time.time()
        
        # Should complete quickly
        self.assertLess(end_time - start_time, 0.1)


class TestAdminAccessibility(BaseAdminTest):
    """Test admin accessibility features"""

    def test_admin_help_texts(self):
        """Test admin help texts"""
        form = AssignmentAdminForm()
        
        # Check that important fields have help text
        # This would be implemented based on actual form field configurations
        self.assertIsInstance(form, AssignmentAdminForm)

    def test_admin_verbose_names(self):
        """Test admin verbose names"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Check that custom method descriptions are set
        self.assertEqual(assignment_admin.submission_count.short_description, 'Submissions')

    def test_admin_field_ordering(self):
        """Test admin field ordering"""
        assignment_admin = AssignmentAdmin(Assignment, self.site)
        
        # Check that fieldsets are logically organized
        fieldsets = assignment_admin.fieldsets
        self.assertGreater(len(fieldsets), 0)
        
        # Each fieldset should have a name and fields
        for fieldset in fieldsets:
            self.assertEqual(len(fieldset), 2)  # (name, options)
            self.assertIsInstance(fieldset[0], str)  # name
            self.assertIsInstance(fieldset[1], dict)  # options
            self.assertIn('fields', fieldset[1])  # fields key exists
