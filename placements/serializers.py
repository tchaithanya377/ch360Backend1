from rest_framework import serializers
from .models import Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer
from students.serializers import StudentSerializer
from students.models import Student


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'website', 'description', 'industry', 'headquarters', 'contact_email', 'contact_phone', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobPostingSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), source='company', write_only=True)

    class Meta:
        model = JobPosting
        fields = [
            'id', 'company', 'company_id', 'title', 'description', 'location',
            'work_mode', 'job_type', 'stipend', 'salary_min', 'salary_max',
            'currency', 'skills', 'eligibility_criteria', 'application_deadline',
            'openings', 'is_active', 'posted_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'posted_by', 'created_at', 'updated_at']


class ApplicationSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(source='student', queryset=Student.objects.all(), write_only=True)
    job = JobPostingSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(source='job', queryset=JobPosting.objects.all(), write_only=True)
    drive_id = serializers.PrimaryKeyRelatedField(source='drive', queryset=PlacementDrive.objects.all(), required=False, allow_null=True, write_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'student', 'student_id', 'job', 'job_id', 'drive_id', 'resume', 'cover_letter',
            'status', 'applied_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['id', 'applied_at', 'updated_at']

    
class PlacementDriveSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), source='company', write_only=True)

    class Meta:
        model = PlacementDrive
        fields = [
            'id', 'company', 'company_id', 'title', 'description', 'drive_type', 'venue',
            'start_date', 'end_date', 'min_cgpa', 'max_backlogs_allowed', 'batch_year',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InterviewRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewRound
        fields = ['id', 'drive', 'name', 'round_type', 'scheduled_at', 'location', 'instructions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['id', 'application', 'offered_role', 'package_annual_ctc', 'joining_location', 'joining_date', 'status', 'offered_at', 'updated_at', 'notes']
        read_only_fields = ['id', 'offered_at', 'updated_at']


