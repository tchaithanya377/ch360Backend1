# Generated migration to create BulkAssignment table

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_add_bulk_assignment_table'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS students_bulkassignment (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                operation_type VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                criteria JSONB NOT NULL DEFAULT '{}',
                assignment_data JSONB NOT NULL DEFAULT '{}',
                total_students_found INTEGER NOT NULL DEFAULT 0,
                students_updated INTEGER NOT NULL DEFAULT 0,
                students_failed INTEGER NOT NULL DEFAULT 0,
                errors JSONB NOT NULL DEFAULT '[]',
                warnings JSONB NOT NULL DEFAULT '[]',
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_by_id UUID REFERENCES accounts_user(id) ON DELETE SET NULL
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS students_bulkassignment;"
        ),
    ]
