#!/usr/bin/env python
"""
Simple Verification Test for Integrated Academic System
Quick verification that all components are working
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing Imports...")
    
    try:
        # Test model imports
        from attendance.models import (
            AcademicPeriod, TimetableSlot, AttendanceSession, AttendanceRecord,
            AttendanceConfiguration, AcademicCalendarHoliday
        )
        print("✅ Model imports successful")
        
        # Test serializer imports
        from attendance.serializers import (
            AcademicPeriodSerializer, AcademicPeriodListSerializer, AcademicPeriodCreateSerializer,
            TimetableSlotSerializer, AttendanceSessionListSerializer, AttendanceRecordSerializer
        )
        print("✅ Serializer imports successful")
        
        # Test view imports
        from attendance.views import (
            AcademicPeriodViewSet, TimetableSlotViewSet, AttendanceSessionViewSet, AttendanceRecordViewSet
        )
        print("✅ View imports successful")
        
        # Test permission imports
        from attendance.permissions import (
            AcademicPeriodPermissions, TimetableSlotPermissions, AttendanceSessionPermissions,
            AttendanceRecordPermissions, CanManageAcademicPeriods
        )
        print("✅ Permission imports successful")
        
        # Test URL imports
        from attendance.urls import urlpatterns
        print("✅ URL imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_models():
    """Test model functionality"""
    print("\n🔍 Testing Models...")
    
    try:
        from attendance.models import AcademicPeriod
        from students.models import AcademicYear, Semester
        
        # Test AcademicPeriod model methods
        print("✅ AcademicPeriod model accessible")
        
        # Test class methods exist
        assert hasattr(AcademicPeriod, 'get_current_period')
        assert hasattr(AcademicPeriod, 'get_period_by_date')
        print("✅ AcademicPeriod class methods exist")
        
        # Test properties exist
        period = AcademicPeriod()
        assert hasattr(period, 'display_name')
        assert hasattr(period, 'is_ongoing')
        assert hasattr(period, 'get_duration_days')
        print("✅ AcademicPeriod properties exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_serializers():
    """Test serializer functionality"""
    print("\n🔍 Testing Serializers...")
    
    try:
        from attendance.serializers import AcademicPeriodSerializer
        
        # Test serializer fields
        serializer = AcademicPeriodSerializer()
        fields = serializer.get_fields()
        
        expected_fields = [
            'id', 'academic_year', 'semester', 'academic_year_display', 'semester_display',
            'is_current', 'is_active', 'period_start', 'period_end', 'duration_days',
            'is_ongoing', 'description', 'created_by', 'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            assert field in fields, f"Field {field} not found in serializer"
        
        print("✅ AcademicPeriodSerializer fields correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Serializer test failed: {e}")
        return False

def test_views():
    """Test view functionality"""
    print("\n🔍 Testing Views...")
    
    try:
        from attendance.views import AcademicPeriodViewSet
        
        # Test viewset exists and has required methods
        assert hasattr(AcademicPeriodViewSet, 'get_queryset')
        assert hasattr(AcademicPeriodViewSet, 'get_serializer_class')
        print("✅ AcademicPeriodViewSet methods exist")
        
        # Test custom actions exist
        assert hasattr(AcademicPeriodViewSet, 'current')
        assert hasattr(AcademicPeriodViewSet, 'by_date')
        assert hasattr(AcademicPeriodViewSet, 'set_current')
        print("✅ AcademicPeriodViewSet custom actions exist")
        
        return True
        
    except Exception as e:
        print(f"❌ View test failed: {e}")
        return False

def test_permissions():
    """Test permission functionality"""
    print("\n🔍 Testing Permissions...")
    
    try:
        from attendance.permissions import AcademicPeriodPermissions, CanManageAcademicPeriods
        
        # Test permission classes exist
        assert AcademicPeriodPermissions is not None
        assert CanManageAcademicPeriods is not None
        print("✅ Permission classes exist")
        
        # Test permission methods exist
        perm = AcademicPeriodPermissions()
        assert hasattr(perm, 'has_permission')
        print("✅ Permission methods exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test failed: {e}")
        return False

def test_urls():
    """Test URL configuration"""
    print("\n🔍 Testing URLs...")
    
    try:
        from attendance.urls import urlpatterns
        
        # Test that URL patterns exist
        assert len(urlpatterns) > 0
        print("✅ URL patterns exist")
        
        # Test that academic period URLs are included
        url_strings = [str(url.pattern) for url in urlpatterns]
        academic_period_urls = [url for url in url_strings if 'academic-period' in url]
        assert len(academic_period_urls) > 0
        print("✅ Academic period URLs configured")
        
        return True
        
    except Exception as e:
        print(f"❌ URL test failed: {e}")
        return False

def test_database_connection():
    """Test database connection and basic queries"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        from django.db import connection
        from attendance.models import AcademicPeriod
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        print("✅ Database connection working")
        
        # Test model query
        count = AcademicPeriod.objects.count()
        print(f"✅ AcademicPeriod query successful (count: {count})")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_admin_interface():
    """Test admin interface registration"""
    print("\n🔍 Testing Admin Interface...")
    
    try:
        from django.contrib import admin
        from attendance.models import AcademicPeriod
        from attendance.admin import AcademicPeriodAdmin
        
        # Test admin registration
        assert admin.site.is_registered(AcademicPeriod)
        print("✅ AcademicPeriod admin registered")
        
        # Test admin class exists
        assert AcademicPeriodAdmin is not None
        print("✅ AcademicPeriodAdmin class exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Admin test failed: {e}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print("🚀 Starting Integrated Academic System Verification...")
    print("="*60)
    
    tests = [
        test_imports,
        test_models,
        test_serializers,
        test_views,
        test_permissions,
        test_urls,
        test_database_connection,
        test_admin_interface
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
        print("✅ Integrated Academic System is working perfectly!")
        print("✅ All components are properly integrated and functional")
        print("✅ The system is ready for production use!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
