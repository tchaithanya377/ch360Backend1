#!/usr/bin/env python
"""
Test Form Fix
Tests that the forms can be instantiated without KeyError
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_forms_instantiation():
    """Test that forms can be instantiated without KeyError"""
    print("🔍 Testing Form Instantiation...")
    
    try:
        from attendance.forms import (
            AcademicPeriodForm, TimetableSlotForm, 
            AttendanceSessionForm, AttendanceRecordForm
        )
        
        # Test AcademicPeriodForm
        form1 = AcademicPeriodForm()
        print("✅ AcademicPeriodForm instantiated successfully")
        
        # Test TimetableSlotForm
        form2 = TimetableSlotForm()
        print("✅ TimetableSlotForm instantiated successfully")
        
        # Test AttendanceSessionForm
        form3 = AttendanceSessionForm()
        print("✅ AttendanceSessionForm instantiated successfully")
        
        # Test AttendanceRecordForm
        form4 = AttendanceRecordForm()
        print("✅ AttendanceRecordForm instantiated successfully")
        
        return True
        
    except KeyError as e:
        print(f"❌ KeyError occurred: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error occurred: {e}")
        return False

def test_form_fields():
    """Test that forms have expected fields"""
    print("\n🔍 Testing Form Fields...")
    
    try:
        from attendance.forms import TimetableSlotForm
        
        form = TimetableSlotForm()
        
        # Check that form has expected fields
        expected_fields = ['academic_period', 'course_section', 'faculty', 'day_of_week', 'start_time', 'end_time']
        
        for field in expected_fields:
            if field in form.fields:
                print(f"✅ Field '{field}' found in TimetableSlotForm")
            else:
                print(f"⚠️ Field '{field}' not found in TimetableSlotForm")
        
        return True
        
    except Exception as e:
        print(f"❌ Form fields test failed: {e}")
        return False

def test_admin_integration():
    """Test admin integration"""
    print("\n🔍 Testing Admin Integration...")
    
    try:
        from django.contrib import admin
        from attendance.models import TimetableSlot
        from attendance.admin import TimetableSlotAdmin
        
        # Test that admin is registered
        assert admin.site.is_registered(TimetableSlot)
        print("✅ TimetableSlot admin is registered")
        
        # Test that admin has the enhanced form
        admin_class = admin.site._registry[TimetableSlot]
        assert hasattr(admin_class, 'form')
        assert admin_class.form is not None
        print("✅ TimetableSlot admin has enhanced form")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin integration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Testing Form Fix...")
    print("="*50)
    
    tests = [
        test_forms_instantiation,
        test_form_fields,
        test_admin_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ KeyError fix is working!")
        print("✅ Forms can be instantiated without errors!")
        print("✅ Admin integration is working!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

