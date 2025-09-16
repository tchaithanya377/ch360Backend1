from rest_framework import serializers
from .models import (
    Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer,
    PlacementStatistics, CompanyFeedback, PlacementDocument, AlumniPlacement
)
from students.serializers import StudentSerializer
from students.models import Student
from departments.serializers import DepartmentSerializer
from departments.models import Department
from academics.models import AcademicProgram


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'website', 'description', 'industry', 'company_size',
            'headquarters', 'contact_email', 'contact_phone', 'rating',
            'total_placements', 'total_drives', 'last_visit_date', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'rating', 'total_placements', 'total_drives', 'created_at', 'updated_at']


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


class PlacementStatisticsSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), source='department', write_only=True)
    program = serializers.StringRelatedField(read_only=True)
    program_id = serializers.PrimaryKeyRelatedField(queryset=AcademicProgram.objects.all(), source='program', write_only=True)

    class Meta:
        model = PlacementStatistics
        fields = [
            'id', 'academic_year', 'department', 'department_id', 'program', 'program_id',
            'total_students', 'eligible_students', 'placed_students', 'placement_percentage',
            'average_salary', 'highest_salary', 'lowest_salary', 'total_companies_visited',
            'total_job_offers', 'students_higher_studies', 'students_entrepreneurship',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'placement_percentage', 'created_at', 'updated_at']


class CompanyFeedbackSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), source='company', write_only=True)
    drive = PlacementDriveSerializer(read_only=True)
    drive_id = serializers.PrimaryKeyRelatedField(queryset=PlacementDrive.objects.all(), source='drive', write_only=True)

    class Meta:
        model = CompanyFeedback
        fields = [
            'id', 'company', 'company_id', 'drive', 'drive_id', 'overall_rating',
            'student_quality_rating', 'process_rating', 'infrastructure_rating',
            'positive_feedback', 'areas_for_improvement', 'suggestions',
            'would_visit_again', 'feedback_by', 'feedback_by_designation', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PlacementDocumentSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), source='company', required=False, allow_null=True, write_only=True)
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), source='student', required=False, allow_null=True, write_only=True)
    drive = PlacementDriveSerializer(read_only=True)
    drive_id = serializers.PrimaryKeyRelatedField(queryset=PlacementDrive.objects.all(), source='drive', required=False, allow_null=True, write_only=True)

    class Meta:
        model = PlacementDocument
        fields = [
            'id', 'document_type', 'title', 'description', 'file', 'company', 'company_id',
            'student', 'student_id', 'drive', 'drive_id', 'document_date', 'expiry_date',
            'is_active', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class AlumniPlacementSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all(), source='student', write_only=True)

    class Meta:
        model = AlumniPlacement
        fields = [
            'id', 'student', 'student_id', 'current_company', 'current_designation',
            'current_salary', 'current_location', 'total_experience_years', 'job_changes',
            'pursuing_higher_studies', 'higher_studies_institution', 'higher_studies_program',
            'is_entrepreneur', 'startup_name', 'startup_description', 'linkedin_profile',
            'email', 'phone', 'willing_to_mentor', 'willing_to_recruit', 'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'last_updated', 'created_at']


