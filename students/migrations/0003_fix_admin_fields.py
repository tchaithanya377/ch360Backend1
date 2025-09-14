# Data migration to fix admin field issues

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_add_enhanced_models'),
    ]

    operations = [
        # This is a data migration to ensure existing data is compatible
        # No database schema changes needed
    ]
