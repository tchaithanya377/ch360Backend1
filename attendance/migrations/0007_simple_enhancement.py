"""
Simple enhancement migration for attendance system
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Simple enhancement migration"""
    
    dependencies = [
        ('attendance', '0002_attendanceauditlog_attendanceconfiguration_and_more'),
    ]
    
    operations = [
        # Create new models that don't exist yet
        migrations.CreateModel(
            name='AttendanceStatistics',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    'students.Student',
                    on_delete=models.CASCADE,
                    related_name="attendance_statistics"
                )),
                ('course_section', models.ForeignKey(
                    'academics.CourseSection',
                    on_delete=models.CASCADE,
                    related_name="attendance_statistics"
                )),
                ('academic_year', models.CharField(max_length=9)),
                ('semester', models.CharField(max_length=20)),
                ('total_sessions', models.PositiveIntegerField(default=0)),
                ('present_count', models.PositiveIntegerField(default=0)),
                ('absent_count', models.PositiveIntegerField(default=0)),
                ('late_count', models.PositiveIntegerField(default=0)),
                ('excused_count', models.PositiveIntegerField(default=0)),
                ('attendance_percentage', models.DecimalField(
                    max_digits=5,
                    decimal_places=2,
                    default=0.0
                )),
                ('is_eligible_for_exam', models.BooleanField(default=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('last_calculated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'attendance_statistics',
            },
        ),
        
        migrations.CreateModel(
            name='BiometricDevice',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('device_id', models.CharField(max_length=100, unique=True)),
                ('device_name', models.CharField(max_length=200)),
                ('device_type', models.CharField(
                    max_length=20,
                    choices=[
                        ("fingerprint", "Fingerprint Scanner"),
                        ("face", "Face Recognition"),
                        ("iris", "Iris Scanner"),
                        ("palm", "Palm Scanner"),
                    ]
                )),
                ('location', models.CharField(max_length=200)),
                ('room', models.CharField(max_length=64, blank=True)),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ("active", "Active"),
                        ("inactive", "Inactive"),
                        ("maintenance", "Under Maintenance"),
                        ("error", "Error"),
                    ],
                    default="active"
                )),
                ('last_seen', models.DateTimeField(null=True, blank=True)),
                ('firmware_version', models.CharField(max_length=50, blank=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('auto_sync', models.BooleanField(default=True)),
                ('sync_interval_minutes', models.PositiveIntegerField(default=5)),
                ('ip_address', models.GenericIPAddressField()),
                ('port', models.PositiveIntegerField(default=80)),
                ('api_endpoint', models.URLField(blank=True)),
                ('api_key', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'db_table': 'attendance_biometric_device',
            },
        ),
        
        migrations.CreateModel(
            name='BiometricTemplate',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    'students.Student',
                    on_delete=models.CASCADE,
                    related_name="biometric_templates"
                )),
                ('device', models.ForeignKey(
                    'BiometricDevice',
                    on_delete=models.CASCADE,
                    related_name="templates"
                )),
                ('template_data', models.TextField(help_text="Encrypted biometric template")),
                ('template_hash', models.CharField(max_length=64, db_index=True)),
                ('quality_score', models.DecimalField(
                    max_digits=3,
                    decimal_places=2,
                    null=True,
                    blank=True
                )),
                ('is_active', models.BooleanField(default=True)),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('last_used', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'attendance_biometric_template',
            },
        ),
        
        # Add constraints
        migrations.AddConstraint(
            model_name='attendancestatistics',
            constraint=models.UniqueConstraint(
                fields=['student', 'course_section', 'academic_year', 'semester', 'period_start', 'period_end'],
                name='unique_stats_student_course_period'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='biometrictemplate',
            constraint=models.UniqueConstraint(
                fields=['student', 'device'],
                name='unique_template_student_device'
            ),
        ),
    ]
