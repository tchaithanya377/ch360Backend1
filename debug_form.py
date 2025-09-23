#!/usr/bin/env python
"""
Debug Form Issue
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

def debug_academic_period_form():
    """Debug AcademicPeriodForm"""
    print("🔍 Debugging AcademicPeriodForm...")
    
    try:
        from attendance.forms import AcademicPeriodForm
        from attendance.models import AcademicPeriod
        
        print("✅ Imports successful")
        
        # Check model fields
        model_fields = [f.name for f in AcademicPeriod._meta.get_fields()]
        print(f"Model fields: {model_fields}")
        
        # Try to create form
        form = AcademicPeriodForm()
        print("✅ Form created successfully")
        
        # Check form fields
        form_fields = list(form.fields.keys())
        print(f"Form fields: {form_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    debug_academic_period_form()

