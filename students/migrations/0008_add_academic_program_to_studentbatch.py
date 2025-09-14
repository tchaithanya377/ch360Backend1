# Generated migration to add academic_program_id to StudentBatch table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0007_create_bulk_assignment'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS academic_program_id UUID 
            REFERENCES academics_academicprogram(id) ON DELETE CASCADE;
            """,
            reverse_sql="""
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS academic_program_id;
            """
        ),
    ]