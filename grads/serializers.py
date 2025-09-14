from rest_framework import serializers
from .models import GradeScale, Term, CourseResult, TermGPA, GraduateRecord


class GradeScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeScale
        fields = ['id', 'letter', 'min_score', 'max_score', 'grade_points', 'is_active', 'department', 'program']


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ['id', 'name', 'academic_year', 'semester', 'start_date', 'end_date', 'is_locked']


class CourseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseResult
        read_only_fields = ['total_marks', 'letter_grade', 'grade_points', 'passed', 'evaluated_at', 'evaluator']
        fields = [
            'id', 'student', 'term', 'course_section',
            'internal_marks', 'external_marks', 'total_marks',
            'letter_grade', 'grade_points', 'passed', 'evaluated_at', 'evaluator'
        ]


class TermGPASerializer(serializers.ModelSerializer):
    class Meta:
        model = TermGPA
        fields = ['id', 'student', 'term', 'gpa', 'total_credits']


class GraduateRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraduateRecord
        fields = ['id', 'student', 'program', 'graduation_date', 'cgpa', 'total_credits_earned', 'created_at', 'updated_at']


