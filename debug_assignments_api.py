#!/usr/bin/env python3
"""
Debug script to identify issues with assignments API
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from assignments.views import AssignmentCategoryListCreateView
from assignments.models import AssignmentCategory

User = get_user_model()

def test_categories_view():
    """Test the categories view directly"""
    print("Testing AssignmentCategoryListCreateView...")
    
    try:
        # Create a test user
        user = User.objects.filter(email='test@example.com').first()
        if not user:
            print("Test user not found")
            return
        
        # Create API request using DRF test client
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test the API endpoint
        response = client.get('/api/v1/assignments/categories/')
        print(f"API Response status: {response.status_code}")
        if response.status_code == 200:
            print(f"API Response data count: {len(response.data)}")
            print("API is working correctly!")
        else:
            print(f"API Response error: {response.data}")
        
    except Exception as e:
        print(f"Error in categories view: {str(e)}")
        import traceback
        traceback.print_exc()

def test_models():
    """Test the models directly"""
    print("\nTesting models...")
    
    try:
        categories = AssignmentCategory.objects.all()
        print(f"Total categories: {categories.count()}")
        
        for category in categories[:3]:
            print(f"Category: {category.name} - Active: {category.is_active}")
            
    except Exception as e:
        print(f"Error in models: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_models()
    test_categories_view()
