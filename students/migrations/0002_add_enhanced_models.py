# Generated migration for enhanced academic models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
        ('departments', '0001_initial'),
        ('academics', '0001_initial'),
    ]

    operations = [
        # Create StudentBatch model
        migrations.CreateModel(
            name='StudentBatch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('year_of_study', models.CharField(
                    choices=[
                        ('1', '1st Year'), ('2', '2nd Year'), ('3', '3rd Year'),
                        ('4', '4th Year'), ('5', '5th Year')
                    ],
                    max_length=1
                )),
                ('section', models.CharField(
                    choices=[
                        ('A', 'Section A'), ('B', 'Section B'), ('C', 'Section C'),
                        ('D', 'Section D'), ('E', 'Section E'), ('F', 'Section F'),
                        ('G', 'Section G'), ('H', 'Section H'), ('I', 'Section I'),
                        ('J', 'Section J'), ('K', 'Section K'), ('L', 'Section L'),
                        ('M', 'Section M'), ('N', 'Section N'), ('O', 'Section O'),
                        ('P', 'Section P'), ('Q', 'Section Q'), ('R', 'Section R'),
                        ('S', 'Section S'), ('T', 'Section T')
                    ],
                    max_length=1
                )),
                ('batch_name', models.CharField(help_text="e.g., CS-2024-1-A", max_length=100)),
                ('batch_code', models.CharField(help_text="Unique batch code", max_length=50, unique=True)),
                ('max_capacity', models.PositiveIntegerField(default=70, help_text="Maximum students per batch")),
                ('current_count', models.PositiveIntegerField(default=0, help_text="Current student count")),
                ('is_active', models.BooleanField(default=True)),
                ('academic_program', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_batches',
                    to='academics.academicprogram'
                )),
                ('academic_year', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_batches',
                    to='students.academicyear'
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_batches',
                    to='accounts.user'
                )),
                ('department', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_batches',
                    to='departments.department'
                )),
                ('semester', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_batches',
                    to='students.semester'
                )),
            ],
            options={
                'verbose_name': 'Student Batch',
                'verbose_name_plural': 'Student Batches',
                'ordering': ['department', 'academic_year', 'year_of_study', 'section'],
            },
        ),
        
        # Create BulkAssignment model
        migrations.CreateModel(
            name='BulkAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('operation_type', models.CharField(
                    choices=[
                        ('ASSIGN_DEPARTMENT', 'Assign Department'),
                        ('ASSIGN_PROGRAM', 'Assign Academic Program'),
                        ('ASSIGN_YEAR', 'Assign Academic Year'),
                        ('ASSIGN_SEMESTER', 'Assign Semester'),
                        ('ASSIGN_SECTION', 'Assign Section'),
                        ('PROMOTE_YEAR', 'Promote to Next Year'),
                        ('TRANSFER_BATCH', 'Transfer to Different Batch'),
                        ('CUSTOM', 'Custom Assignment'),
                    ],
                    max_length=20
                )),
                ('title', models.CharField(help_text="Operation title", max_length=200)),
                ('description', models.TextField(blank=True, help_text="Operation description", null=True)),
                ('criteria', models.JSONField(default=dict, help_text="Selection criteria")),
                ('assignment_data', models.JSONField(default=dict, help_text="Assignment data")),
                ('total_students_found', models.PositiveIntegerField(default=0)),
                ('students_updated', models.PositiveIntegerField(default=0)),
                ('students_failed', models.PositiveIntegerField(default=0)),
                ('errors', models.JSONField(blank=True, default=list)),
                ('warnings', models.JSONField(blank=True, default=list)),
                ('status', models.CharField(
                    choices=[
                        ('PENDING', 'Pending'),
                        ('PROCESSING', 'Processing'),
                        ('COMPLETED', 'Completed'),
                        ('FAILED', 'Failed'),
                        ('PARTIAL', 'Partially Completed'),
                    ],
                    default='PENDING',
                    max_length=20
                )),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='bulk_assignments',
                    to='accounts.user'
                )),
            ],
            options={
                'verbose_name': 'Bulk Assignment',
                'verbose_name_plural': 'Bulk Assignments',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add unique constraint for StudentBatch
        migrations.AddConstraint(
            model_name='studentbatch',
            constraint=models.UniqueConstraint(
                fields=('department', 'academic_year', 'year_of_study', 'section'),
                name='unique_batch_per_dept_year_section'
            ),
        ),
    ]
