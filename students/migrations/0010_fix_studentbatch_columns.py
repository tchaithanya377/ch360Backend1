# Generated migration to fix StudentBatch columns

from django.db import migrations


class Migration(migrations.Migration):

	dependencies = [
		('students', '0009_add_academic_year_to_studentbatch'),
	]

	# No-op: schema already aligned in prior migrations/models for tests
	operations = []
