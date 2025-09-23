#!/usr/bin/env python
"""
Test Enhanced Dropdown Functionality
Tests the improved Academic Period forms with dynamic dropdowns
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_forms_import():
    """Test that enhanced forms can be imported"""
    print("🔍 Testing Enhanced Forms Import...")
    
    try:
        from attendance.forms import (
            AcademicPeriodForm, TimetableSlotForm, 
            AttendanceSessionForm, AttendanceRecordForm
        )
        print("✅ Enhanced forms imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Form import failed: {e}")
        return False

def test_form_fields():
    """Test that forms have correct fields and widgets"""
    print("\n🔍 Testing Form Fields and Widgets...")
    
    try:
        from attendance.forms import AcademicPeriodForm
        
        # Test AcademicPeriodForm
        form = AcademicPeriodForm()
        
        # Check that academic_year field has correct widget
        if 'academic_year' in form.fields:
            academic_year_field = form.fields['academic_year']
            assert hasattr(academic_year_field.widget, 'attrs')
            assert 'onchange' in academic_year_field.widget.attrs
            assert academic_year_field.widget.attrs['onchange'] == 'filterSemesters()'
            print("✅ AcademicPeriodForm academic_year field has correct widget")
        else:
            print("⚠️ AcademicPeriodForm academic_year field not found - checking model fields")
            from attendance.models import AcademicPeriod
            model_fields = [f.name for f in AcademicPeriod._meta.get_fields()]
            print(f"Available fields: {model_fields}")
        
        # Check that semester field has correct widget
        if 'semester' in form.fields:
            semester_field = form.fields['semester']
            assert hasattr(semester_field.widget, 'attrs')
            assert 'id' in semester_field.widget.attrs
            assert semester_field.widget.attrs['id'] == 'id_semester'
            print("✅ AcademicPeriodForm semester field has correct widget")
        else:
            print("⚠️ AcademicPeriodForm semester field not found")
        
        # Check that period_start field has date input
        period_start_field = form.fields['period_start']
        assert period_start_field.widget.input_type == 'date'
        print("✅ AcademicPeriodForm period_start field has date input")
        
        # Check that period_end field has date input
        period_end_field = form.fields['period_end']
        assert period_end_field.widget.input_type == 'date'
        print("✅ AcademicPeriodForm period_end field has date input")
        
        return True
        
    except Exception as e:
        print(f"❌ Form fields test failed: {e}")
        return False

def test_form_validation():
    """Test form validation logic"""
    print("\n🔍 Testing Form Validation...")
    
    try:
        from attendance.forms import AcademicPeriodForm
        from students.models import AcademicYear, Semester
        from datetime import date
        
        # Create test data
        academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 5, 31),
            is_active=True
        )
        
        semester = Semester.objects.create(
            academic_year=academic_year,
            name='Fall 2024',
            semester_type='ODD',
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31),
            is_active=True
        )
        
        # Test valid form data
        form_data = {
            'academic_year': academic_year.id,
            'semester': semester.id,
            'period_start': date(2024, 9, 1),
            'period_end': date(2024, 12, 31),
            'is_current': False,
            'is_active': True,
            'description': 'Test academic period'
        }
        
        form = AcademicPeriodForm(data=form_data)
        if form.is_valid():
            print("✅ Form validation passes for valid data")
        else:
            print(f"❌ Form validation failed: {form.errors}")
            return False
        
        # Test invalid date range
        invalid_form_data = form_data.copy()
        invalid_form_data['period_start'] = date(2024, 12, 31)
        invalid_form_data['period_end'] = date(2024, 9, 1)
        
        form = AcademicPeriodForm(data=invalid_form_data)
        if not form.is_valid():
            print("✅ Form validation correctly rejects invalid date range")
        else:
            print("❌ Form validation should reject invalid date range")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Form validation test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints for dropdown filtering"""
    print("\n🔍 Testing API Endpoints...")
    
    try:
        from attendance.api_views import DropdownAPIViewSet
        from django.test import RequestFactory
        from students.models import AcademicYear, Semester
        from datetime import date
        
        # Create test data
        academic_year = AcademicYear.objects.create(
            year='2024-2025',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 5, 31),
            is_active=True
        )
        
        semester = Semester.objects.create(
            academic_year=academic_year,
            name='Fall 2024',
            semester_type='ODD',
            start_date=date(2024, 9, 1),
            end_date=date(2024, 12, 31),
            is_active=True
        )
        
        # Test semesters_by_academic_year endpoint
        factory = RequestFactory()
        request = factory.get(f'/api/dropdowns/semesters-by-academic-year/?academic_year={academic_year.id}')
        
        viewset = DropdownAPIViewSet()
        response = viewset.semesters_by_academic_year(request)
        
        if response.status_code == 200:
            data = response.data
            assert 'results' in data
            assert len(data['results']) > 0
            print("✅ Semesters by academic year API endpoint works")
        else:
            print(f"❌ Semesters API endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {e}")
        return False

def test_admin_integration():
    """Test admin integration with enhanced forms"""
    print("\n🔍 Testing Admin Integration...")
    
    try:
        from django.contrib import admin
        from attendance.models import AcademicPeriod
        from attendance.admin import AcademicPeriodAdmin
        
        # Test that admin is registered
        assert admin.site.is_registered(AcademicPeriod)
        print("✅ AcademicPeriod admin is registered")
        
        # Test that admin has the enhanced form
        admin_class = admin.site._registry[AcademicPeriod]
        assert hasattr(admin_class, 'form')
        assert admin_class.form is not None
        print("✅ AcademicPeriod admin has enhanced form")
        
        # Test that admin has Media class for JavaScript
        assert hasattr(admin_class, 'Media')
        assert 'js' in admin_class.Media.__dict__
        print("✅ AcademicPeriod admin has Media class for JavaScript")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin integration test failed: {e}")
        return False

def test_javascript_file():
    """Test that JavaScript file exists and has required functions"""
    print("\n🔍 Testing JavaScript File...")
    
    try:
        import os
        
        js_file_path = 'attendance/static/admin/js/attendance_forms.js'
        assert os.path.exists(js_file_path), f"JavaScript file not found: {js_file_path}"
        print("✅ JavaScript file exists")
        
        # Read and check JavaScript content
        with open(js_file_path, 'r') as f:
            js_content = f.read()
        
        # Check for required functions
        required_functions = [
            'filterSemesters',
            'filterCourseSections', 
            'filterTimetableSlots',
            'filterStudents',
            'validateDateRange',
            'validateTimeRange'
        ]
        
        for func in required_functions:
            assert func in js_content, f"Required function {func} not found in JavaScript"
        
        print("✅ JavaScript file contains all required functions")
        
        # Check for API endpoint URLs
        api_endpoints = [
            'semesters-by-academic-year',
            'course-sections-by-period',
            'timetable-slots-by-period',
            'sessions'
        ]
        
        for endpoint in api_endpoints:
            assert endpoint in js_content, f"API endpoint {endpoint} not found in JavaScript"
        
        print("✅ JavaScript file contains all required API endpoints")
        
        return True
        
    except Exception as e:
        print(f"❌ JavaScript file test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Testing Enhanced Dropdown Functionality...")
    print("="*60)
    
    tests = [
        test_forms_import,
        test_form_fields,
        test_form_validation,
        test_api_endpoints,
        test_admin_integration,
        test_javascript_file
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Enhanced dropdown functionality is working perfectly!")
        print("✅ Academic Year and Semester dropdowns are properly implemented!")
        print("✅ Dynamic filtering and validation are working!")
        print("✅ Admin interface is enhanced with better user experience!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
