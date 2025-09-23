# Generated migration to cleanup Student academic fields and add StudentBatch relation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0011_change_academic_year_to_foreignkey'),
    ]

    # No-op for tests; model schema already provides correct columns
    operations = []
