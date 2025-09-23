# Generated manually for AcademicTimetableSlot model

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0006_merge_20250919_1505'),
        ('students', '0020_merge_0002_initial_0019_add_missing_fields_to_caste'),
        ('faculty', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicTimetableSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_type', models.CharField(choices=[('LECTURE', 'Lecture'), ('LAB', 'Laboratory'), ('TUTORIAL', 'Tutorial'), ('SEMINAR', 'Seminar'), ('WORKSHOP', 'Workshop'), ('EXAM', 'Examination'), ('BREAK', 'Break'), ('FREE', 'Free Period')], default='LECTURE', max_length=20)),
                ('day_of_week', models.CharField(choices=[('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')], max_length=3)),
                ('start_time', models.TimeField(help_text='Slot start time')),
                ('end_time', models.TimeField(help_text='Slot end time')),
                ('room', models.CharField(help_text='Room or venue', max_length=100)),
                ('subject', models.CharField(blank=True, help_text='Subject or topic', max_length=200)),
                ('description', models.TextField(blank=True, help_text='Additional description')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this slot is active')),
                ('is_recurring', models.BooleanField(default=True, help_text='Whether this slot repeats weekly')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_year', models.ForeignKey(help_text='Academic year from students table', on_delete=django.db.models.deletion.CASCADE, related_name='timetable_slots', to='students.academicyear')),
                ('course', models.ForeignKey(blank=True, help_text='Course for this slot (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='timetable_slots', to='academics.course')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_timetable_slots', to=settings.AUTH_USER_MODEL)),
                ('faculty', models.ForeignKey(blank=True, help_text='Faculty member for this slot (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='timetable_slots', to='faculty.faculty')),
                ('semester', models.ForeignKey(help_text='Semester from students table', on_delete=django.db.models.deletion.CASCADE, related_name='timetable_slots', to='students.semester')),
                ('student_batch', models.ForeignKey(blank=True, help_text='Student batch for this slot (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='timetable_slots', to='students.studentbatch')),
            ],
            options={
                'verbose_name': 'Timetable Slot',
                'verbose_name_plural': 'Timetable Slots',
                'ordering': ['academic_year', 'semester', 'day_of_week', 'start_time'],
            },
        ),
        migrations.AddIndex(
            model_name='academictimetableslot',
            index=models.Index(fields=['academic_year', 'semester'], name='academics_a_academi_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='academictimetableslot',
            index=models.Index(fields=['day_of_week', 'start_time'], name='academics_a_day_of__789abc_idx'),
        ),
        migrations.AddIndex(
            model_name='academictimetableslot',
            index=models.Index(fields=['faculty', 'is_active'], name='academics_a_faculty_def456_idx'),
        ),
        migrations.AddIndex(
            model_name='academictimetableslot',
            index=models.Index(fields=['student_batch', 'is_active'], name='academics_a_student_ghi789_idx'),
        ),
    ]




