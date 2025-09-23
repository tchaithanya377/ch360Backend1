"""
Enhanced Attendance Migrations for CampsHub360
Migration plan and SQL optimizations for production deployment
"""

from django.db import migrations, models
from django.db.models import Q
from django.contrib.postgres.indexes import GinIndex, BTreeIndex
from django.contrib.postgres.operations import CreateExtension


class Migration(migrations.Migration):
    """Initial migration for enhanced attendance system"""
    
    initial = True
    dependencies = [
        ('accounts', '0001_initial'),
        ('students', '0001_initial'),
        ('academics', '0001_initial'),
        ('faculty', '0001_initial'),
        ('departments', '0001_initial'),
    ]
    
    operations = [
        # Create PostgreSQL extensions
        CreateExtension('uuid-ossp'),
        CreateExtension('pg_trgm'),
        
        # Configuration table
        migrations.CreateModel(
            name='AttendanceConfiguration',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('key', models.CharField(max_length=100, unique=True, db_index=True)),
                ('value', models.TextField()),
                ('description', models.TextField(blank=True)),
                ('data_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('string', 'String'),
                        ('integer', 'Integer'),
                        ('float', 'Float'),
                        ('boolean', 'Boolean'),
                        ('json', 'JSON'),
                    ],
                    default='string'
                )),
                ('is_active', models.BooleanField(default=True)),
                ('updated_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name='updated_attendance_configs'
                )),
            ],
            options={
                'db_table': 'attendance_configuration',
                'verbose_name': 'Attendance Configuration',
                'verbose_name_plural': 'Attendance Configurations',
            },
        ),
        
        # Academic calendar holidays
        migrations.CreateModel(
            name='AcademicCalendarHoliday',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('date', models.DateField(db_index=True)),
                ('is_full_day', models.BooleanField(default=True)),
                ('academic_year', models.CharField(max_length=9, blank=True)),
                ('description', models.TextField(blank=True)),
                ('affects_attendance', models.BooleanField(
                    default=True,
                    help_text="Whether this holiday affects attendance calculation"
                )),
            ],
            options={
                'db_table': 'attendance_holiday',
            },
        ),
        
        # Timetable slots
        migrations.CreateModel(
            name='TimetableSlot',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course_section', models.ForeignKey(
                    'academics.CourseSection',
                    on_delete=models.CASCADE,
                    related_name="timetable_slots"
                )),
                ('faculty', models.ForeignKey(
                    'faculty.Faculty',
                    on_delete=models.PROTECT,
                    related_name="teaching_slots"
                )),
                ('day_of_week', models.IntegerField(
                    choices=[(i, day) for i, day in enumerate([
                        "Monday", "Tuesday", "Wednesday", "Thursday", 
                        "Friday", "Saturday", "Sunday"
                    ])],
                    db_index=True
                )),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('room', models.CharField(max_length=64, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('academic_year', models.CharField(max_length=9)),
                ('semester', models.CharField(max_length=20)),
                ('slot_type', models.CharField(
                    max_length=20,
                    choices=[
                        ('LECTURE', 'Lecture'),
                        ('LAB', 'Laboratory'),
                        ('TUTORIAL', 'Tutorial'),
                        ('SEMINAR', 'Seminar'),
                    ],
                    default='LECTURE'
                )),
                ('max_students', models.PositiveIntegerField(
                    null=True,
                    blank=True,
                    help_text="Maximum students for this slot"
                )),
            ],
            options={
                'db_table': 'attendance_timetable_slot',
            },
        ),
        
        # Attendance sessions
        migrations.CreateModel(
            name='AttendanceSession',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course_section', models.ForeignKey(
                    'academics.CourseSection',
                    on_delete=models.PROTECT,
                    related_name="attendance_sessions"
                )),
                ('faculty', models.ForeignKey(
                    'faculty.Faculty',
                    on_delete=models.PROTECT,
                    related_name="attendance_sessions"
                )),
                ('timetable_slot', models.ForeignKey(
                    'TimetableSlot',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name="sessions"
                )),
                ('scheduled_date', models.DateField(db_index=True)),
                ('start_datetime', models.DateTimeField(db_index=True)),
                ('end_datetime', models.DateTimeField(db_index=True)),
                ('actual_start_datetime', models.DateTimeField(null=True, blank=True)),
                ('actual_end_datetime', models.DateTimeField(null=True, blank=True)),
                ('room', models.CharField(max_length=64, blank=True)),
                ('status', models.CharField(
                    max_length=16,
                    choices=[
                        ("scheduled", "Scheduled"),
                        ("open", "Open for Attendance"),
                        ("closed", "Closed"),
                        ("locked", "Locked"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="scheduled",
                    db_index=True
                )),
                ('auto_opened', models.BooleanField(default=False)),
                ('auto_closed', models.BooleanField(default=False)),
                ('makeup', models.BooleanField(default=False, help_text="Is this a makeup session?")),
                ('notes', models.TextField(blank=True)),
                ('qr_token', models.CharField(max_length=255, blank=True, db_index=True)),
                ('qr_expires_at', models.DateTimeField(null=True, blank=True)),
                ('qr_generated_at', models.DateTimeField(null=True, blank=True)),
                ('biometric_enabled', models.BooleanField(default=False)),
                ('biometric_device_id', models.CharField(max_length=100, blank=True)),
                ('offline_sync_token', models.CharField(max_length=255, blank=True, db_index=True)),
                ('last_sync_at', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'attendance_session',
            },
        ),
        
        # Student snapshots
        migrations.CreateModel(
            name='StudentSnapshot',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(
                    'AttendanceSession',
                    on_delete=models.CASCADE,
                    related_name="snapshots"
                )),
                ('student', models.ForeignKey(
                    'students.Student',
                    on_delete=models.CASCADE,
                    related_name="attendance_snapshots"
                )),
                ('course_section', models.ForeignKey(
                    'academics.CourseSection',
                    on_delete=models.PROTECT
                )),
                ('student_batch', models.ForeignKey(
                    'students.StudentBatch',
                    on_delete=models.PROTECT,
                    null=True,
                    blank=True
                )),
                ('roll_number', models.CharField(max_length=20)),
                ('full_name', models.CharField(max_length=255)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(max_length=15, blank=True)),
                ('academic_year', models.CharField(max_length=9)),
                ('semester', models.CharField(max_length=20)),
                ('year_of_study', models.CharField(max_length=1)),
                ('section', models.CharField(max_length=1)),
            ],
            options={
                'db_table': 'attendance_student_snapshot',
            },
        ),
        
        # Attendance records
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(
                    'AttendanceSession',
                    on_delete=models.CASCADE,
                    related_name="records"
                )),
                ('student', models.ForeignKey(
                    'students.Student',
                    on_delete=models.CASCADE,
                    related_name="attendance_records"
                )),
                ('mark', models.CharField(
                    max_length=16,
                    choices=[
                        ("present", "Present"),
                        ("absent", "Absent"),
                        ("late", "Late"),
                        ("excused", "Excused"),
                    ]
                )),
                ('marked_at', models.DateTimeField(default=timezone.now, db_index=True)),
                ('source', models.CharField(
                    max_length=16,
                    choices=[
                        ("manual", "Manual Entry"),
                        ("qr", "QR Code Scan"),
                        ("biometric", "Biometric"),
                        ("rfid", "RFID Card"),
                        ("offline", "Offline Sync"),
                        ("import", "Bulk Import"),
                        ("system", "System Generated"),
                    ],
                    default="manual"
                )),
                ('reason', models.CharField(max_length=255, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('device_id', models.CharField(max_length=100, blank=True)),
                ('device_type', models.CharField(max_length=50, blank=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('user_agent', models.TextField(blank=True)),
                ('location_lat', models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)),
                ('location_lng', models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)),
                ('client_uuid', models.CharField(max_length=64, blank=True, db_index=True)),
                ('sync_status', models.CharField(
                    max_length=20,
                    choices=[
                        ("pending", "Pending Sync"),
                        ("synced", "Synced"),
                        ("conflict", "Sync Conflict"),
                    ],
                    default="synced"
                )),
                ('vendor_event_id', models.CharField(max_length=128, blank=True, db_index=True)),
                ('vendor_data', models.JSONField(default=dict, blank=True)),
                ('marked_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name="marked_attendance"
                )),
                ('last_modified_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
                    related_name="modified_attendance"
                )),
            ],
            options={
                'db_table': 'attendance_record',
            },
        ),
        
        # Leave applications
        migrations.CreateModel(
            name='LeaveApplication',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    'students.Student',
                    on_delete=models.CASCADE,
                    related_name="leave_applications"
                )),
                ('leave_type', models.CharField(
                    max_length=32,
                    choices=[
                        ("medical", "Medical Leave"),
                        ("maternity", "Maternity Leave"),
                        ("on_duty", "On Duty Leave"),
                        ("sport", "Sports/Cultural Leave"),
                        ("personal", "Personal Leave"),
                        ("emergency", "Emergency Leave"),
                        ("other", "Other"),
                    ]
                )),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('reason', models.TextField()),
                ('supporting_document', models.FileField(
                    upload_to="leave_documents/",
                    null=True,
                    blank=True
                )),
                ('status', models.CharField(
                    max_length=16,
                    choices=[
                        ("pending", "Pending"),
                        ("approved", "Approved"),
                        ("rejected", "Rejected"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="pending",
                    db_index=True
                )),
                ('decided_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.PROTECT,
                    null=True,
                    blank=True,
                    related_name="decided_leaves"
                )),
                ('decided_at', models.DateTimeField(null=True, blank=True)),
                ('decision_note', models.TextField(blank=True)),
                ('affects_attendance', models.BooleanField(
                    default=True,
                    help_text="Whether this leave affects attendance calculation"
                )),
                ('auto_apply_to_sessions', models.BooleanField(
                    default=True,
                    help_text="Automatically apply to relevant attendance sessions"
                )),
            ],
            options={
                'db_table': 'attendance_leave_application',
            },
        ),
        
        # Correction requests
        migrations.CreateModel(
            name='AttendanceCorrectionRequest',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(
                    'AttendanceSession',
                    on_delete=models.CASCADE,
                    related_name="correction_requests"
                )),
                ('student', models.ForeignKey(
                    'students.Student',
                    on_delete=models.CASCADE,
                    related_name="correction_requests"
                )),
                ('from_mark', models.CharField(
                    max_length=16,
                    choices=[
                        ("present", "Present"),
                        ("absent", "Absent"),
                        ("late", "Late"),
                        ("excused", "Excused"),
                    ]
                )),
                ('to_mark', models.CharField(
                    max_length=16,
                    choices=[
                        ("present", "Present"),
                        ("absent", "Absent"),
                        ("late", "Late"),
                        ("excused", "Excused"),
                    ]
                )),
                ('reason', models.TextField()),
                ('supporting_document', models.FileField(
                    upload_to="attendance_corrections/",
                    null=True,
                    blank=True
                )),
                ('requested_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.PROTECT,
                    related_name="attendance_corrections_requested"
                )),
                ('status', models.CharField(
                    max_length=16,
                    choices=[
                        ("pending", "Pending"),
                        ("approved", "Approved"),
                        ("rejected", "Rejected"),
                        ("cancelled", "Cancelled"),
                    ],
                    default="pending",
                    db_index=True
                )),
                ('decided_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.PROTECT,
                    null=True,
                    blank=True,
                    related_name="attendance_corrections_decided"
                )),
                ('decided_at', models.DateTimeField(null=True, blank=True)),
                ('decision_note', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'attendance_correction_request',
            },
        ),
        
        # Audit logs
        migrations.CreateModel(
            name='AttendanceAuditLog',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('entity_type', models.CharField(max_length=64)),
                ('entity_id', models.CharField(max_length=64)),
                ('action', models.CharField(max_length=32)),
                ('performed_by', models.ForeignKey(
                    'accounts.User',
                    on_delete=models.SET_NULL,
                    null=True,
                    related_name="attendance_audit_logs"
                )),
                ('before', models.JSONField(null=True, blank=True)),
                ('after', models.JSONField(null=True, blank=True)),
                ('reason', models.TextField(blank=True)),
                ('source', models.CharField(max_length=32, default="system")),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('user_agent', models.TextField(blank=True)),
                ('session_id', models.CharField(max_length=64, blank=True)),
                ('student_id', models.CharField(max_length=64, blank=True)),
            ],
            options={
                'db_table': 'attendance_audit_log',
            },
        ),
        
        # Statistics
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
        
        # Biometric devices
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
        
        # Biometric templates
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
            model_name='academiccalendarholiday',
            constraint=models.UniqueConstraint(
                fields=['name', 'date'],
                name='unique_holiday_name_date'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='timetableslot',
            constraint=models.UniqueConstraint(
                fields=['course_section', 'day_of_week', 'start_time'],
                name='unique_slot_course_day_time'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='timetableslot',
            constraint=models.UniqueConstraint(
                fields=['faculty', 'day_of_week', 'start_time'],
                name='unique_slot_faculty_day_time'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='attendancesession',
            constraint=models.UniqueConstraint(
                fields=['timetable_slot', 'scheduled_date'],
                name='unique_session_slot_date'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='studentsnapshot',
            constraint=models.UniqueConstraint(
                fields=['session', 'student'],
                name='unique_snapshot_session_student'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='attendancerecord',
            constraint=models.UniqueConstraint(
                fields=['session', 'student'],
                name='unique_record_session_student'
            ),
        ),
        
        migrations.AddConstraint(
            model_name='attendancecorrectionrequest',
            constraint=models.UniqueConstraint(
                fields=['session', 'student'],
                condition=models.Q(status='pending'),
                name='unique_pending_correction_session_student'
            ),
        ),
        
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
        
        # Add indexes for performance
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_session_course_date ON attendance_session (course_section_id, scheduled_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_session_course_date;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_session_status ON attendance_session (status) WHERE status IN ('open', 'closed');",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_session_status;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_student_session ON attendance_record (student_id, session_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_student_session;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_marked_at ON attendance_record (marked_at) WHERE marked_at >= CURRENT_DATE - INTERVAL '30 days';",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_marked_at;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_source ON attendance_record (source, marked_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_source;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_audit_entity ON attendance_audit_log (entity_type, entity_id, created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_audit_entity;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_stats_eligible ON attendance_statistics (is_eligible_for_exam, attendance_percentage);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_stats_eligible;"
        ),
        
        # Add GIN indexes for JSON fields
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_vendor_data_gin ON attendance_record USING GIN (vendor_data);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_vendor_data_gin;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_audit_before_gin ON attendance_audit_log USING GIN (before);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_audit_before_gin;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_audit_after_gin ON attendance_audit_log USING GIN (after);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_audit_after_gin;"
        ),
        
        # Add partial indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_present ON attendance_record (session_id, student_id) WHERE mark IN ('present', 'late');",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_present;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_absent ON attendance_record (session_id, student_id) WHERE mark = 'absent';",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_absent;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_leave_pending ON attendance_leave_application (student_id, status) WHERE status = 'pending';",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_leave_pending;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_correction_pending ON attendance_correction_request (status, created_at) WHERE status = 'pending';",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_correction_pending;"
        ),
        
        # Add composite indexes for reporting queries
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_stats_reporting ON attendance_statistics (academic_year, semester, is_eligible_for_exam, attendance_percentage);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_stats_reporting;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY idx_attendance_record_reporting ON attendance_record (session_id, mark, marked_at) WHERE marked_at >= CURRENT_DATE - INTERVAL '1 year';",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_record_reporting;"
        ),
    ]


class Migration(migrations.Migration):
    """Data migration to populate default configurations"""
    
    dependencies = [
        ('attendance', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(
            code=populate_default_configurations,
            reverse_code=remove_default_configurations,
        ),
    ]


def populate_default_configurations(apps, schema_editor):
    """Populate default attendance configurations"""
    AttendanceConfiguration = apps.get_model('attendance', 'AttendanceConfiguration')
    
    default_configs = [
        {
            'key': 'GRACE_PERIOD_MINUTES',
            'value': '5',
            'description': 'Grace period in minutes for late arrivals',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'MIN_DURATION_FOR_PRESENT_MINUTES',
            'value': '10',
            'description': 'Minimum duration in minutes to be marked present',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'THRESHOLD_PERCENT',
            'value': '75',
            'description': 'Minimum attendance percentage for exam eligibility',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'ALLOW_QR_SELF_MARK',
            'value': 'true',
            'description': 'Allow students to mark their own attendance via QR',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'OFFLINE_SYNC_MAX_DELTA_MINUTES',
            'value': '120',
            'description': 'Maximum time delta in minutes for offline sync',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'DEFAULT_TIMEZONE',
            'value': 'Asia/Kolkata',
            'description': 'Default timezone for attendance system',
            'data_type': 'string',
            'is_active': True
        },
        {
            'key': 'DATA_RETENTION_YEARS',
            'value': '7',
            'description': 'Data retention period in years',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'AUTO_OPEN_SESSIONS',
            'value': 'true',
            'description': 'Automatically open sessions based on schedule',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'AUTO_CLOSE_SESSIONS',
            'value': 'true',
            'description': 'Automatically close sessions after end time',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'QR_TOKEN_EXPIRY_MINUTES',
            'value': '60',
            'description': 'QR token expiry time in minutes',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'MAX_CORRECTION_DAYS',
            'value': '7',
            'description': 'Maximum days after session to allow corrections',
            'data_type': 'integer',
            'is_active': True
        },
        {
            'key': 'BIOMETRIC_ENABLED',
            'value': 'false',
            'description': 'Enable biometric attendance capture',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'RFID_ENABLED',
            'value': 'false',
            'description': 'Enable RFID attendance capture',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'GPS_VERIFICATION',
            'value': 'false',
            'description': 'Enable GPS location verification',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'AUTO_MARK_ABSENT',
            'value': 'true',
            'description': 'Automatically mark students absent if no attendance recorded',
            'data_type': 'boolean',
            'is_active': True
        },
        {
            'key': 'SEND_ATTENDANCE_NOTIFICATIONS',
            'value': 'true',
            'description': 'Send attendance-related notifications',
            'data_type': 'boolean',
            'is_active': True
        },
    ]
    
    for config_data in default_configs:
        AttendanceConfiguration.objects.get_or_create(
            key=config_data['key'],
            defaults=config_data
        )


def remove_default_configurations(apps, schema_editor):
    """Remove default configurations"""
    AttendanceConfiguration = apps.get_model('attendance', 'AttendanceConfiguration')
    
    default_keys = [
        'GRACE_PERIOD_MINUTES',
        'MIN_DURATION_FOR_PRESENT_MINUTES',
        'THRESHOLD_PERCENT',
        'ALLOW_QR_SELF_MARK',
        'OFFLINE_SYNC_MAX_DELTA_MINUTES',
        'DEFAULT_TIMEZONE',
        'DATA_RETENTION_YEARS',
        'AUTO_OPEN_SESSIONS',
        'AUTO_CLOSE_SESSIONS',
        'QR_TOKEN_EXPIRY_MINUTES',
        'MAX_CORRECTION_DAYS',
        'BIOMETRIC_ENABLED',
        'RFID_ENABLED',
        'GPS_VERIFICATION',
        'AUTO_MARK_ABSENT',
        'SEND_ATTENDANCE_NOTIFICATIONS',
    ]
    
    AttendanceConfiguration.objects.filter(key__in=default_keys).delete()


class Migration(migrations.Migration):
    """Migration to add performance optimizations"""
    
    dependencies = [
        ('attendance', '0002_populate_default_configurations'),
    ]
    
    operations = [
        # Add materialized view for attendance summary
        migrations.RunSQL(
            """
            CREATE MATERIALIZED VIEW attendance_summary_mv AS
            SELECT 
                s.id as session_id,
                s.course_section_id,
                s.scheduled_date,
                s.status,
                COUNT(ar.id) as total_records,
                COUNT(CASE WHEN ar.mark IN ('present', 'late') THEN 1 END) as present_count,
                COUNT(CASE WHEN ar.mark = 'absent' THEN 1 END) as absent_count,
                COUNT(CASE WHEN ar.mark = 'late' THEN 1 END) as late_count,
                COUNT(CASE WHEN ar.mark = 'excused' THEN 1 END) as excused_count,
                ROUND(
                    (COUNT(CASE WHEN ar.mark IN ('present', 'late') THEN 1 END)::DECIMAL / 
                     NULLIF(COUNT(ar.id) - COUNT(CASE WHEN ar.mark = 'excused' THEN 1 END), 0)) * 100, 
                    2
                ) as attendance_percentage
            FROM attendance_session s
            LEFT JOIN attendance_record ar ON s.id = ar.session_id
            GROUP BY s.id, s.course_section_id, s.scheduled_date, s.status;
            """,
            reverse_sql="DROP MATERIALIZED VIEW IF EXISTS attendance_summary_mv;"
        ),
        
        # Add index on materialized view
        migrations.RunSQL(
            "CREATE UNIQUE INDEX idx_attendance_summary_mv_session ON attendance_summary_mv (session_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_summary_mv_session;"
        ),
        
        migrations.RunSQL(
            "CREATE INDEX idx_attendance_summary_mv_course_date ON attendance_summary_mv (course_section_id, scheduled_date);",
            reverse_sql="DROP INDEX IF EXISTS idx_attendance_summary_mv_course_date;"
        ),
        
        # Add function to refresh materialized view
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION refresh_attendance_summary()
            RETURNS void AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY attendance_summary_mv;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS refresh_attendance_summary();"
        ),
        
        # Add trigger to auto-refresh materialized view
        migrations.RunSQL(
            """
            CREATE OR REPLACE FUNCTION trigger_refresh_attendance_summary()
            RETURNS trigger AS $$
            BEGIN
                PERFORM refresh_attendance_summary();
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS trigger_refresh_attendance_summary();"
        ),
        
        migrations.RunSQL(
            """
            CREATE TRIGGER attendance_record_refresh_trigger
            AFTER INSERT OR UPDATE OR DELETE ON attendance_record
            FOR EACH STATEMENT
            EXECUTE FUNCTION trigger_refresh_attendance_summary();
            """,
            reverse_sql="DROP TRIGGER IF EXISTS attendance_record_refresh_trigger ON attendance_record;"
        ),
    ]
