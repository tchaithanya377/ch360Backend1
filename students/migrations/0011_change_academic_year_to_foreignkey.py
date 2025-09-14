# Generated migration to change academic_year from CharField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0010_fix_studentbatch_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- First, drop the existing academic_year column
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS academic_year;
            
            -- Add the new academic_year_id ForeignKey column
            ALTER TABLE students_studentbatch 
            ADD COLUMN academic_year_id BIGINT REFERENCES students_academicyear(id) ON DELETE CASCADE;
            """,
            reverse_sql="""
            -- Reverse: drop ForeignKey and add back CharField
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS academic_year_id;
            
            ALTER TABLE students_studentbatch 
            ADD COLUMN academic_year VARCHAR(9);
            """
        ),
    ]
