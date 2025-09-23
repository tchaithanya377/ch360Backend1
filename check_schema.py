#!/usr/bin/env python
"""
Check database schema for AcademicYear
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campshub360.settings')
django.setup()

from django.db import connection

def check_academic_year_schema():
    """Check AcademicYear table schema"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'students_academicyear'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print("AcademicYear table schema:")
        print("-" * 60)
        for column in columns:
            print(f"{column[0]:<20} {column[1]:<15} {column[2]:<10} {column[3] or 'None'}")
        print("-" * 60)

if __name__ == '__main__':
    check_academic_year_schema()
