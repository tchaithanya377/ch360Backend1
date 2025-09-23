#!/usr/bin/env python
"""
Quick test to verify the admin interface fix
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_admin_forms():
    """Test that admin forms can be created without errors"""
    print("🔍 Testing Admin Forms...")
    
    try:
        from django.contrib import admin
        from attendance.models import AttendanceRecord, AttendanceAuditLog
        from attendance.admin import AttendanceRecordAdmin, AttendanceAuditLogAdmin
        
        # Test AttendanceRecord admin form
        record_admin = AttendanceRecordAdmin(AttendanceRecord, admin.site)
        form_class = record_admin.get_form(None)
        form = form_class()
        print("✅ AttendanceRecord admin form created successfully")
        
        # Test AttendanceAuditLog admin form
        audit_admin = AttendanceAuditLogAdmin(AttendanceAuditLog, admin.site)
        form_class = audit_admin.get_form(None)
        form = form_class()
        print("✅ AttendanceAuditLog admin form created successfully")
        
        # Test that fieldsets are valid
        record_fieldsets = record_admin.get_fieldsets(None)
        audit_fieldsets = audit_admin.get_fieldsets(None)
        print("✅ Admin fieldsets are valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin form test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_fields():
    """Test that model fields exist"""
    print("\n🔍 Testing Model Fields...")
    
    try:
        from attendance.models import AttendanceRecord, AttendanceAuditLog
        
        # Test AttendanceRecord fields
        record_fields = [f.name for f in AttendanceRecord._meta.get_fields()]
        expected_record_fields = ['session', 'student', 'mark', 'marked_at']
        for field in expected_record_fields:
            assert field in record_fields, f"Field {field} not found in AttendanceRecord"
        print("✅ AttendanceRecord fields are correct")
        
        # Test AttendanceAuditLog fields
        audit_fields = [f.name for f in AttendanceAuditLog._meta.get_fields()]
        expected_audit_fields = ['entity_type', 'entity_id', 'action', 'performed_by']
        for field in expected_audit_fields:
            assert field in audit_fields, f"Field {field} not found in AttendanceAuditLog"
        print("✅ AttendanceAuditLog fields are correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Model field test failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("🚀 Testing Admin Interface Fix...")
    print("="*50)
    
    tests = [test_model_fields, test_admin_forms]
    passed = 0
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "="*50)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED!")
        print("✅ Admin interface fix is working correctly!")
        print("✅ The FieldError has been resolved!")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
