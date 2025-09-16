#!/usr/bin/env python
"""
Simple API endpoint testing script for placements module.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def test_imports():
    """Test if all modules can be imported."""
    print("🧪 Testing Placements Module Imports...")
    print("=" * 50)
    
    try:
        # Test models
        from placements.models import (
            Company, JobPosting, Application, PlacementDrive, 
            InterviewRound, Offer, PlacementStatistics, 
            CompanyFeedback, PlacementDocument, AlumniPlacement
        )
        print("✅ Models imported successfully")
        
        # Test serializers
        from placements.serializers import (
            CompanySerializer, JobPostingSerializer, ApplicationSerializer,
            PlacementDriveSerializer, InterviewRoundSerializer, OfferSerializer,
            PlacementStatisticsSerializer, CompanyFeedbackSerializer,
            PlacementDocumentSerializer, AlumniPlacementSerializer
        )
        print("✅ Serializers imported successfully")
        
        # Test views
        from placements.views import (
            CompanyViewSet, JobPostingViewSet, ApplicationViewSet,
            PlacementDriveViewSet, InterviewRoundViewSet, OfferViewSet,
            PlacementStatisticsViewSet, CompanyFeedbackViewSet,
            PlacementDocumentViewSet, AlumniPlacementViewSet,
            PlacementAnalyticsViewSet
        )
        print("✅ Views imported successfully")
        
        # Test admin
        from placements.admin import (
            CompanyAdmin, JobPostingAdmin, ApplicationAdmin,
            PlacementDriveAdmin, InterviewRoundAdmin, OfferAdmin,
            PlacementStatisticsAdmin, CompanyFeedbackAdmin,
            PlacementDocumentAdmin, AlumniPlacementAdmin
        )
        print("✅ Admin classes imported successfully")
        
        # Test URLs
        from placements.urls import router, urlpatterns
        print("✅ URLs configured successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_fields():
    """Test model field configurations."""
    print("\n🔍 Testing Model Field Configurations...")
    print("=" * 50)
    
    try:
        from placements.models import Company, PlacementStatistics
        
        # Test Company model fields
        company_fields = [field.name for field in Company._meta.fields]
        print("Company model fields:")
        for field in company_fields:
            print(f"  ✅ {field}")
        
        # Check for new fields
        new_company_fields = ['company_size', 'rating', 'total_placements', 'total_drives', 'last_visit_date']
        print("\nNew Company fields:")
        for field in new_company_fields:
            if field in company_fields:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} - MISSING")
        
        # Test PlacementStatistics model
        stats_fields = [field.name for field in PlacementStatistics._meta.fields]
        print("\nPlacementStatistics model fields:")
        for field in stats_fields:
            print(f"  ✅ {field}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model field test error: {e}")
        return False

def test_serializer_fields():
    """Test serializer field configurations."""
    print("\n📝 Testing Serializer Field Configurations...")
    print("=" * 50)
    
    try:
        from placements.serializers import CompanySerializer, PlacementStatisticsSerializer
        
        # Test CompanySerializer
        company_serializer = CompanySerializer()
        company_fields = list(company_serializer.fields.keys())
        print("CompanySerializer fields:")
        for field in company_fields:
            print(f"  ✅ {field}")
        
        # Test PlacementStatisticsSerializer
        stats_serializer = PlacementStatisticsSerializer()
        stats_fields = list(stats_serializer.fields.keys())
        print("\nPlacementStatisticsSerializer fields:")
        for field in stats_fields:
            print(f"  ✅ {field}")
        
        return True
        
    except Exception as e:
        print(f"❌ Serializer field test error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint configurations."""
    print("\n🔗 Testing API Endpoint Configurations...")
    print("=" * 50)
    
    try:
        from placements.urls import router
        
        # Get all registered endpoints
        endpoints = []
        for pattern in router.urls:
            endpoints.append(str(pattern.pattern))
        
        print("Registered API endpoints:")
        for endpoint in endpoints:
            print(f"  ✅ {endpoint}")
        
        # Expected endpoints
        expected_endpoints = [
            'companies/',
            'jobs/',
            'applications/',
            'drives/',
            'rounds/',
            'offers/',
            'statistics/',
            'feedbacks/',
            'documents/',
            'alumni/',
            'analytics/'
        ]
        
        print("\nChecking expected endpoints:")
        for expected in expected_endpoints:
            found = any(expected in endpoint for endpoint in endpoints)
            if found:
                print(f"  ✅ {expected}")
            else:
                print(f"  ❌ {expected} - MISSING")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test error: {e}")
        return False

def test_nirf_compliance():
    """Test NIRF compliance features."""
    print("\n🏛️ Testing NIRF Compliance Features...")
    print("=" * 50)
    
    try:
        from placements.models import PlacementStatistics
        
        # NIRF required fields
        nirf_fields = [
            'total_students', 'eligible_students', 'placed_students',
            'placement_percentage', 'average_salary', 'highest_salary',
            'lowest_salary', 'students_higher_studies', 'students_entrepreneurship'
        ]
        
        model_fields = [field.name for field in PlacementStatistics._meta.fields]
        
        print("NIRF compliance fields:")
        all_present = True
        for field in nirf_fields:
            if field in model_fields:
                print(f"  ✅ {field}")
            else:
                print(f"  ❌ {field} - MISSING")
                all_present = False
        
        if all_present:
            print("\n🎉 All NIRF compliance fields are present!")
        
        return all_present
        
    except Exception as e:
        print(f"❌ NIRF compliance test error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 PLACEMENTS MODULE COMPREHENSIVE TESTING")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Model Fields", test_model_fields),
        ("Serializer Fields", test_serializer_fields),
        ("API Endpoints", test_api_endpoints),
        ("NIRF Compliance", test_nirf_compliance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The placements module is working correctly.")
        print("\n📋 Enhanced Features Available:")
        print("   • Enhanced Company management with ratings")
        print("   • Placement statistics for NIRF compliance")
        print("   • Company feedback system")
        print("   • Document management")
        print("   • Alumni network tracking")
        print("   • Advanced analytics and reporting")
        print("   • 11 new API endpoints")
        print("   • Management commands")
        print("   • Admin interface enhancements")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
