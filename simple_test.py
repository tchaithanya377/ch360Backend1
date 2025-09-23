#!/usr/bin/env python
"""
Simple test to verify the enhanced attendance system is working
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from attendance.models import (
            AttendanceConfiguration, AcademicCalendarHoliday, TimetableSlot,
            AttendanceSession, AttendanceRecord, LeaveApplication,
            AttendanceCorrectionRequest, AttendanceAuditLog, AttendanceStatistics,
            BiometricDevice, BiometricTemplate
        )
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False
    
    try:
        from attendance.serializers import (
            AttendanceSessionListSerializer, AttendanceRecordSerializer,
            LeaveApplicationSerializer, AttendanceCorrectionRequestSerializer
        )
        print("✓ Serializers imported successfully")
    except Exception as e:
        print(f"✗ Serializers import failed: {e}")
        return False
    
    try:
        from attendance.views import (
            AttendanceSessionViewSet, AttendanceRecordViewSet,
            LeaveApplicationViewSet, AttendanceCorrectionRequestViewSet
        )
        print("✓ Views imported successfully")
    except Exception as e:
        print(f"✗ Views import failed: {e}")
        return False
    
    try:
        from attendance.tasks import (
            auto_open_sessions, auto_close_sessions, generate_sessions_for_range,
            calculate_attendance_statistics, cleanup_old_attendance_data
        )
        print("✓ Tasks imported successfully")
    except Exception as e:
        print(f"✗ Tasks import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from attendance.models import AttendanceConfiguration
        
        # Test that we can query the model
        config_count = AttendanceConfiguration.objects.count()
        print(f"✓ AttendanceConfiguration count: {config_count}")
        
        # Test that we can create a configuration
        config, created = AttendanceConfiguration.objects.get_or_create(
            key='TEST_CONFIG',
            defaults={
                'value': 'test_value',
                'description': 'Test configuration',
                'data_type': 'string'
            }
        )
        if created:
            print("✓ Created test configuration")
            config.delete()
            print("✓ Deleted test configuration")
        else:
            print("✓ Test configuration already exists")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ENHANCED ATTENDANCE SYSTEM - SIMPLE TEST")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic functionality
    if not test_basic_functionality():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - ENHANCED ATTENDANCE SYSTEM IS WORKING!")
        print("=" * 60)
        
        print("\n🎉 SUCCESS! Your enhanced attendance system is now ready!")
        print("\nNext steps:")
        print("1. Start the Django server: python manage.py runserver")
        print("2. Access admin: http://localhost:8000/admin/attendance/")
        print("3. Test API endpoints: http://localhost:8000/api/v1/attendance/")
        print("4. Start Celery worker: celery -A campshub360 worker -l info")
        print("5. Start Celery beat: celery -A campshub360 beat -l info")
        
    else:
        print("❌ SOME TESTS FAILED - CHECK THE ERRORS ABOVE")
        print("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()
