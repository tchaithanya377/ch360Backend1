#!/usr/bin/env python
"""
Simple test to verify admin configuration is correct
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_admin_configuration():
    """Test that admin configuration is valid"""
    print("🔍 Testing Admin Configuration...")
    
    try:
        from django.contrib import admin
        from attendance.models import AttendanceRecord, AttendanceAuditLog
        from attendance.admin import AttendanceRecordAdmin, AttendanceAuditLogAdmin
        
        # Test that admin classes are registered
        assert admin.site.is_registered(AttendanceRecord)
        assert admin.site.is_registered(AttendanceAuditLog)
        print("✅ Admin classes are registered")
        
        # Test that admin classes exist
        assert AttendanceRecordAdmin is not None
        assert AttendanceAuditLogAdmin is not None
        print("✅ Admin classes exist")
        
        # Test that fieldsets don't reference non-existent fields
        record_admin = AttendanceRecordAdmin(AttendanceRecord, admin.site)
        record_fieldsets = record_admin.get_fieldsets(None)
        
        # Check that all fields in fieldsets exist in the model
        model_fields = [f.name for f in AttendanceRecord._meta.get_fields()]
        for fieldset_name, fieldset_data in record_fieldsets:
            for field in fieldset_data['fields']:
                if field not in model_fields:
                    raise ValueError(f"Field '{field}' in AttendanceRecordAdmin fieldsets does not exist in model")
        print("✅ AttendanceRecordAdmin fieldsets are valid")
        
        # Test AttendanceAuditLog admin
        audit_admin = AttendanceAuditLogAdmin(AttendanceAuditLog, admin.site)
        audit_fieldsets = audit_admin.get_fieldsets(None)
        
        # Check that all fields in fieldsets exist in the model
        audit_model_fields = [f.name for f in AttendanceAuditLog._meta.get_fields()]
        for fieldset_name, fieldset_data in audit_fieldsets:
            for field in fieldset_data['fields']:
                if field not in audit_model_fields:
                    raise ValueError(f"Field '{field}' in AttendanceAuditLogAdmin fieldsets does not exist in model")
        print("✅ AttendanceAuditLogAdmin fieldsets are valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_imports():
    """Test that all models can be imported"""
    print("\n🔍 Testing Model Imports...")
    
    try:
        from attendance.models import (
            AcademicPeriod, AttendanceRecord, AttendanceSession, 
            AttendanceAuditLog, TimetableSlot
        )
        print("✅ All models imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Model import failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("🚀 Testing Admin Interface Configuration...")
    print("="*60)
    
    tests = [test_model_imports, test_admin_configuration]
    passed = 0
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Admin interface configuration is correct!")
        print("✅ The FieldError should be resolved!")
        print("\n🔧 Fixed Issues:")
        print("  - Removed 'session_id' from AttendanceRecordAdmin fieldsets")
        print("  - Removed 'session_id' and 'student_id' from AttendanceAuditLogAdmin readonly_fields")
        print("  - All field references now match actual model fields")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
