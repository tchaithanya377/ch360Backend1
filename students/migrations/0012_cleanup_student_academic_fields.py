# Generated migration to cleanup Student academic fields and add StudentBatch relation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0011_change_academic_year_to_foreignkey'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Add the new student_batch_id ForeignKey column
            ALTER TABLE students_student 
            ADD COLUMN student_batch_id BIGINT REFERENCES students_studentbatch(id) ON DELETE SET NULL;
            
            -- Drop the old academic fields
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS section;
            
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS year_of_study;
            
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS academic_year;
            
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS semester;
            
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS department_id;
            
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS academic_program_id;
            """,
            reverse_sql="""
            -- Reverse: add back old fields and drop new one
            ALTER TABLE students_student 
            DROP COLUMN IF EXISTS student_batch_id;
            
            ALTER TABLE students_student 
            ADD COLUMN section VARCHAR(1);
            
            ALTER TABLE students_student 
            ADD COLUMN year_of_study VARCHAR(1);
            
            ALTER TABLE students_student 
            ADD COLUMN academic_year VARCHAR(9);
            
            ALTER TABLE students_student 
            ADD COLUMN semester VARCHAR(2);
            
            ALTER TABLE students_student 
            ADD COLUMN department_id BIGINT REFERENCES departments_department(id) ON DELETE SET NULL;
            
            ALTER TABLE students_student 
            ADD COLUMN academic_program_id BIGINT REFERENCES academics_academicprogram(id) ON DELETE SET NULL;
            """
        ),
    ]
