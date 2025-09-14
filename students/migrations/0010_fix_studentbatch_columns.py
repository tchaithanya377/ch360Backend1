# Generated migration to fix StudentBatch columns

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0009_add_academic_year_to_studentbatch'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Drop the old ForeignKey column if it exists
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS academic_year_id;
            
            -- Add missing columns that the model expects
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS semester VARCHAR(2) DEFAULT '1';
            
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS batch_code VARCHAR(50) UNIQUE;
            
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS created_by_id UUID REFERENCES accounts_user(id) ON DELETE SET NULL;
            """,
            reverse_sql="""
            -- Reverse operations
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS created_by_id;
            
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS updated_at;
            
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS created_at;
            
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS batch_code;
            
            ALTER TABLE students_studentbatch 
            DROP COLUMN IF EXISTS semester;
            
            ALTER TABLE students_studentbatch 
            ADD COLUMN IF NOT EXISTS academic_year_id UUID REFERENCES students_academicyear(id) ON DELETE CASCADE;
            """
        ),
    ]
