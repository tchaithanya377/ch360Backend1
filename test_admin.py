#!/usr/bin/env python
"""
Test script to verify the enhanced admin interface is working
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_admin_imports():
    """Test that all admin classes can be imported"""
    print("Testing admin imports...")
    
    try:
        from attendance.admin import (
            AttendanceSessionAdmin, AttendanceRecordAdmin, 
            AttendanceCorrectionRequestAdmin, LeaveApplicationAdmin,
            TimetableSlotAdmin, AcademicCalendarHolidayAdmin,
            AttendanceConfigurationAdmin, StudentSnapshotAdmin,
            AttendanceStatisticsAdmin, BiometricDeviceAdmin,
            BiometricTemplateAdmin, AttendanceAuditLogAdmin
        )
        print("✓ All admin classes imported successfully")
        return True
    except Exception as e:
        print(f"✗ Admin import failed: {e}")
        return False

def test_admin_registration():
    """Test that admin classes are properly registered"""
    print("\nTesting admin registration...")
    
    try:
        from django.contrib import admin
        from attendance.models import (
            AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest,
            LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
            AttendanceConfiguration, StudentSnapshot, AttendanceStatistics,
            BiometricDevice, BiometricTemplate, AttendanceAuditLog
        )
        
        # Check if models are registered
        registered_models = [
            AttendanceSession, AttendanceRecord, AttendanceCorrectionRequest,
            LeaveApplication, TimetableSlot, AcademicCalendarHoliday,
            AttendanceConfiguration, StudentSnapshot, AttendanceStatistics,
            BiometricDevice, BiometricTemplate, AttendanceAuditLog
        ]
        
        for model in registered_models:
            if model in admin.site._registry:
                print(f"✓ {model.__name__} is registered in admin")
            else:
                print(f"✗ {model.__name__} is NOT registered in admin")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Admin registration test failed: {e}")
        return False

def test_admin_actions():
    """Test that admin actions are available"""
    print("\nTesting admin actions...")
    
    try:
        from attendance.admin import (
            open_sessions, close_sessions, generate_qr_codes, calculate_statistics
        )
        print("✓ Admin actions imported successfully")
        
        # Test that actions are added to admin classes
        from attendance.admin import AttendanceSessionAdmin, AttendanceStatisticsAdmin
        
        if hasattr(AttendanceSessionAdmin, 'actions') and AttendanceSessionAdmin.actions:
            print("✓ AttendanceSessionAdmin has actions configured")
        else:
            print("✗ AttendanceSessionAdmin missing actions")
            return False
            
        if hasattr(AttendanceStatisticsAdmin, 'actions') and AttendanceStatisticsAdmin.actions:
            print("✓ AttendanceStatisticsAdmin has actions configured")
        else:
            print("✗ AttendanceStatisticsAdmin missing actions")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Admin actions test failed: {e}")
        return False

def test_admin_stats():
    """Test admin statistics function"""
    print("\nTesting admin statistics...")
    
    try:
        from attendance.admin import get_admin_stats
        
        stats = get_admin_stats()
        expected_keys = [
            'total_sessions', 'open_sessions', 'today_sessions', 'week_sessions',
            'total_records', 'today_records', 'pending_corrections', 'pending_leaves'
        ]
        
        for key in expected_keys:
            if key in stats:
                print(f"✓ {key}: {stats[key]}")
            else:
                print(f"✗ Missing stat: {key}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Admin stats test failed: {e}")
        return False

def main():
    """Run all admin tests"""
    print("=" * 60)
    print("ENHANCED ATTENDANCE ADMIN INTERFACE TEST")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_admin_imports():
        success = False
    
    # Test registration
    if not test_admin_registration():
        success = False
    
    # Test actions
    if not test_admin_actions():
        success = False
    
    # Test stats
    if not test_admin_stats():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL ADMIN TESTS PASSED!")
        print("=" * 60)
        
        print("\n🎉 SUCCESS! Your enhanced admin interface is ready!")
        print("\nAdmin Features Available:")
        print("• Enhanced list displays with more information")
        print("• Organized fieldsets for better data entry")
        print("• Custom admin actions (open/close sessions, generate QR codes)")
        print("• Advanced filtering and search capabilities")
        print("• Read-only audit logs for compliance")
        print("• Statistics dashboard for monitoring")
        print("• Biometric device management")
        print("• Attendance statistics tracking")
        
        print("\nAccess your admin interface at:")
        print("http://localhost:8000/admin/attendance/")
        
    else:
        print("❌ SOME ADMIN TESTS FAILED - CHECK THE ERRORS ABOVE")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()
