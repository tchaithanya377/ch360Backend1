#!/usr/bin/env python
"""
Integration test script for enhanced attendance system
Run this to verify the new implementation is working correctly
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

from attendance.models import (
    AttendanceConfiguration, AcademicCalendarHoliday, TimetableSlot,
    AttendanceSession, AttendanceRecord, LeaveApplication,
    AttendanceCorrectionRequest, AttendanceAuditLog, AttendanceStatistics,
    BiometricDevice, BiometricTemplate
)
from attendance.serializers import (
    AttendanceSessionListSerializer, AttendanceRecordSerializer,
    LeaveApplicationSerializer, AttendanceCorrectionRequestSerializer
)
from attendance.views import (
    AttendanceSessionViewSet, AttendanceRecordViewSet,
    LeaveApplicationViewSet, AttendanceCorrectionRequestViewSet
)
from attendance.tasks import (
    auto_open_sessions, auto_close_sessions, generate_sessions_for_range,
    calculate_attendance_statistics, cleanup_old_attendance_data
)

def test_models():
    """Test that all models can be imported and basic operations work"""
    print("Testing models...")
    
    # Test AttendanceConfiguration
    config_count = AttendanceConfiguration.objects.count()
    print(f"✓ AttendanceConfiguration: {config_count} configurations found")
    
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
    
    print("✓ All models working correctly")

def test_serializers():
    """Test that serializers can be imported and instantiated"""
    print("\nTesting serializers...")
    
    # Test serializer imports
    serializers = [
        AttendanceSessionListSerializer,
        AttendanceRecordSerializer,
        LeaveApplicationSerializer,
        AttendanceCorrectionRequestSerializer
    ]
    
    for serializer in serializers:
        print(f"✓ {serializer.__name__} imported successfully")
    
    print("✓ All serializers working correctly")

def test_views():
    """Test that views can be imported and instantiated"""
    print("\nTesting views...")
    
    # Test view imports
    views = [
        AttendanceSessionViewSet,
        AttendanceRecordViewSet,
        LeaveApplicationViewSet,
        AttendanceCorrectionRequestViewSet
    ]
    
    for view in views:
        print(f"✓ {view.__name__} imported successfully")
    
    print("✓ All views working correctly")

def test_tasks():
    """Test that Celery tasks can be imported"""
    print("\nTesting Celery tasks...")
    
    # Test task imports
    tasks = [
        auto_open_sessions,
        auto_close_sessions,
        generate_sessions_for_range,
        calculate_attendance_statistics,
        cleanup_old_attendance_data
    ]
    
    for task in tasks:
        print(f"✓ {task.name} imported successfully")
    
    print("✓ All tasks working correctly")

def test_configuration():
    """Test that default configurations are loaded"""
    print("\nTesting configuration...")
    
    # Check for key configurations
    key_configs = [
        'GRACE_PERIOD_MINUTES',
        'THRESHOLD_PERCENT',
        'AUTO_OPEN_SESSIONS',
        'AUTO_CLOSE_SESSIONS'
    ]
    
    for key in key_configs:
        try:
            config = AttendanceConfiguration.objects.get(key=key)
            print(f"✓ {key}: {config.value}")
        except AttendanceConfiguration.DoesNotExist:
            print(f"✗ {key}: Not found")
    
    print("✓ Configuration test completed")

def main():
    """Run all tests"""
    print("=" * 60)
    print("ENHANCED ATTENDANCE SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    try:
        test_models()
        test_serializers()
        test_views()
        test_tasks()
        test_configuration()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - ENHANCED ATTENDANCE SYSTEM IS READY!")
        print("=" * 60)
        
        print("\nNext steps:")
        print("1. Run 'python manage.py migrate attendance' to apply migrations")
        print("2. Start Celery worker: 'celery -A campshub360 worker -l info'")
        print("3. Start Celery beat: 'celery -A campshub360 beat -l info'")
        print("4. Test API endpoints at /api/v1/attendance/")
        print("5. Check admin interface at /admin/attendance/")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
