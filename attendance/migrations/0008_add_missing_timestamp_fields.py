"""
Add missing timestamp fields to existing tables
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add missing timestamp fields"""
    
    dependencies = [
        ('attendance', '0007_simple_enhancement'),
    ]
    
    operations = [
        # Add created_at and updated_at to existing tables if they don't exist
        migrations.RunSQL(
            """
            DO $$
            BEGIN
                -- Add created_at to attendance_configuration if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_configuration' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_configuration 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_configuration if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_configuration' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_configuration 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_holiday if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_holiday' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_holiday 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_holiday if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_holiday' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_holiday 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_timetable_slot if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_timetable_slot' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_timetable_slot 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_timetable_slot if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_timetable_slot' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_timetable_slot 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_session if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_session' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_session 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_session if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_session' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_session 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_student_snapshot if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_student_snapshot' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_student_snapshot 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_student_snapshot if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_student_snapshot' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_student_snapshot 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_record if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_record' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_record 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_record if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_record' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_record 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_leave_application if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_leave_application' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_leave_application 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_leave_application if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_leave_application' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_leave_application 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_correction_request if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_correction_request' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_correction_request 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_correction_request if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_correction_request' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_correction_request 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add created_at to attendance_audit_log if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_audit_log' 
                              AND column_name = 'created_at') THEN
                    ALTER TABLE attendance_audit_log 
                    ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
                
                -- Add updated_at to attendance_audit_log if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'attendance_audit_log' 
                              AND column_name = 'updated_at') THEN
                    ALTER TABLE attendance_audit_log 
                    ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                END IF;
            END $$;
            """,
            reverse_sql="-- Cannot reverse this operation safely"
        ),
    ]
