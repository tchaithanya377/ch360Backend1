# Generated manually for attendance app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicCalendarHoliday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateField(db_index=True)),
                ('is_full_day', models.BooleanField(default=True)),
                ('academic_year', models.CharField(blank=True, help_text='Academic year (e.g., 2024-2025)', max_length=9)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'attendance_holiday',
                'indexes': [models.Index(fields=['date'], name='attendance_holiday_date_idx')],
                'unique_together': {('name', 'date')},
            },
        ),
    ]






