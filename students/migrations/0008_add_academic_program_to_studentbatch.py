# Generated migration to add academic_program_id to StudentBatch table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0007_create_bulk_assignment'),
    ]

    # No-op for cross-db compatibility; field exists in current models
    operations = []