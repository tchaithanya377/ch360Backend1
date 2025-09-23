# Generated migration to add academic_year column to StudentBatch table

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0008_add_academic_program_to_studentbatch'),
    ]

    # No-op: academic_year handling is already part of current schema/migrations
    operations = []
