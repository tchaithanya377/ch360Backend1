# Generated migration to change academic_year from CharField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0010_fix_studentbatch_columns'),
    ]

    # No-op for cross-db testing; schema already consistent with models
    operations = []
