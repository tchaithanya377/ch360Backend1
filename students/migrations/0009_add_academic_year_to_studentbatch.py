# Generated migration to add academic_year column to StudentBatch table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_add_academic_program_to_studentbatch'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS academic_year VARCHAR(9);
            """,
            reverse_sql="""
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS academic_year;
            """
        ),
    ]
