from rest_framework import serializers
from .models import GradeScale, MidTermGrade, SemesterGrade, SemesterGPA, CumulativeGPA
from students.models import Semester
from academics.models import CourseSection


class GradeScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeScale
        fields = ['id', 'letter', 'description', 'min_score', 'max_score', 'grade_points', 'is_active']


class MidTermGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MidTermGrade
        read_only_fields = ['percentage', 'midterm_grade', 'midterm_grade_points', 'evaluated_at', 'evaluator']
        fields = [
            'id', 'student', 'course_section', 'semester',
            'midterm_marks', 'total_marks', 'percentage', 'midterm_grade', 'midterm_grade_points',
            'evaluated_at', 'evaluator'
        ]

    def create(self, validated_data):
        # Auto-assign evaluator
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['evaluator'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Auto-assign evaluator on update if authenticated
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('evaluator', request.user)
        return super().update(instance, validated_data)


class SemesterGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterGrade
        read_only_fields = ['percentage', 'final_grade', 'final_grade_points', 'passed', 'evaluated_at', 'evaluator']
        fields = [
            'id', 'student', 'course_section', 'semester',
            'final_marks', 'total_marks', 'percentage', 'final_grade', 'final_grade_points', 'passed',
            'evaluated_at', 'evaluator'
        ]

    def create(self, validated_data):
        # Auto-assign evaluator
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['evaluator'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Auto-assign evaluator on update if authenticated
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data.setdefault('evaluator', request.user)
        return super().update(instance, validated_data)


class SemesterGPASerializer(serializers.ModelSerializer):
    class Meta:
        model = SemesterGPA
        fields = ['id', 'student', 'semester', 'sgpa', 'total_credits', 'total_quality_points', 'academic_standing', 'created_at', 'updated_at']


class CumulativeGPASerializer(serializers.ModelSerializer):
    class Meta:
        model = CumulativeGPA
        fields = ['id', 'student', 'cgpa', 'total_credits_earned', 'total_quality_points', 'classification', 'is_eligible_for_graduation', 'graduation_date', 'created_at', 'updated_at']