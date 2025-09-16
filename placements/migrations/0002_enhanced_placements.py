# Generated manually for enhanced placements module

from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ('placements', '0001_initial'),
        ('departments', '0001_initial'),
        ('academics', '0001_initial'),
        ('students', '0001_initial'),
    ]

    operations = [
        # Add new fields to Company model
        migrations.AddField(
            model_name='company',
            name='company_size',
            field=models.CharField(blank=True, choices=[('STARTUP', 'Startup (1-50 employees)'), ('SMALL', 'Small (51-200 employees)'), ('MEDIUM', 'Medium (201-1000 employees)'), ('LARGE', 'Large (1001-5000 employees)'), ('ENTERPRISE', 'Enterprise (5000+ employees)')], max_length=20),
        ),
        migrations.AddField(
            model_name='company',
            name='rating',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=3, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]),
        ),
        migrations.AddField(
            model_name='company',
            name='total_placements',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='company',
            name='total_drives',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='company',
            name='last_visit_date',
            field=models.DateField(blank=True, null=True),
        ),

        # Create PlacementStatistics model
        migrations.CreateModel(
            name='PlacementStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('academic_year', models.CharField(help_text='e.g., 2024-2025', max_length=9)),
                ('total_students', models.PositiveIntegerField(default=0)),
                ('eligible_students', models.PositiveIntegerField(default=0)),
                ('placed_students', models.PositiveIntegerField(default=0)),
                ('placement_percentage', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('average_salary', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('highest_salary', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('lowest_salary', models.DecimalField(decimal_places=2, default=0.0, max_digits=12)),
                ('total_companies_visited', models.PositiveIntegerField(default=0)),
                ('total_job_offers', models.PositiveIntegerField(default=0)),
                ('students_higher_studies', models.PositiveIntegerField(default=0)),
                ('students_entrepreneurship', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placement_stats', to='departments.department')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='placement_stats', to='academics.academicprogram')),
            ],
            options={
                'ordering': ['-academic_year', 'department__name'],
            },
        ),

        # Create CompanyFeedback model
        migrations.CreateModel(
            name='CompanyFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('overall_rating', models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ('student_quality_rating', models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ('process_rating', models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ('infrastructure_rating', models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])),
                ('positive_feedback', models.TextField(blank=True)),
                ('areas_for_improvement', models.TextField(blank=True)),
                ('suggestions', models.TextField(blank=True)),
                ('would_visit_again', models.BooleanField(default=True)),
                ('feedback_by', models.CharField(blank=True, max_length=255)),
                ('feedback_by_designation', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='placements.company')),
                ('drive', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='placements.placementdrive')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # Create PlacementDocument model
        migrations.CreateModel(
            name='PlacementDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('MOU', 'Memorandum of Understanding'), ('AGREEMENT', 'Placement Agreement'), ('OFFER_LETTER', 'Offer Letter'), ('JOINING_LETTER', 'Joining Letter'), ('VERIFICATION', 'Placement Verification'), ('OTHER', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='placements/documents/')),
                ('document_date', models.DateField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='placements.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
                ('drive', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='placements.placementdrive')),
                ('student', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='placement_documents', to='students.student')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # Create AlumniPlacement model
        migrations.CreateModel(
            name='AlumniPlacement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_company', models.CharField(blank=True, max_length=255)),
                ('current_designation', models.CharField(blank=True, max_length=255)),
                ('current_salary', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('current_location', models.CharField(blank=True, max_length=255)),
                ('total_experience_years', models.DecimalField(decimal_places=1, default=0.0, max_digits=4)),
                ('job_changes', models.PositiveIntegerField(default=0)),
                ('pursuing_higher_studies', models.BooleanField(default=False)),
                ('higher_studies_institution', models.CharField(blank=True, max_length=255)),
                ('higher_studies_program', models.CharField(blank=True, max_length=255)),
                ('is_entrepreneur', models.BooleanField(default=False)),
                ('startup_name', models.CharField(blank=True, max_length=255)),
                ('startup_description', models.TextField(blank=True)),
                ('linkedin_profile', models.URLField(blank=True)),
                ('email', models.EmailField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('willing_to_mentor', models.BooleanField(default=False)),
                ('willing_to_recruit', models.BooleanField(default=False)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='alumni_placement', to='students.student')),
            ],
            options={
                'ordering': ['-last_updated'],
            },
        ),

        # Add unique constraints
        migrations.AddConstraint(
            model_name='placementstatistics',
            constraint=models.UniqueConstraint(fields=('academic_year', 'department', 'program'), name='unique_placement_stats'),
        ),
        migrations.AddConstraint(
            model_name='companyfeedback',
            constraint=models.UniqueConstraint(fields=('company', 'drive'), name='unique_company_feedback'),
        ),
    ]
