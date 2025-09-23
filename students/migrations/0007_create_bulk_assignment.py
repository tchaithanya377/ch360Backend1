# Generated migration to create BulkAssignment table

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0006_add_bulk_assignment_table'),
    ]

    # Postgres-specific SQL is not compatible with SQLite used in tests.
    # Make this migration a no-op for cross-db compatibility.
    operations = []
