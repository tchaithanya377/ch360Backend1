from rest_framework import serializers
from .models import Mentorship, Project, Meeting, Feedback


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'


class MentorshipSerializer(serializers.ModelSerializer):
    projects = ProjectSerializer(many=True, read_only=True)
    meetings = MeetingSerializer(many=True, read_only=True)
    feedback = FeedbackSerializer(many=True, read_only=True)
    mentor_name = serializers.CharField(source='mentor.name', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    department_name = serializers.CharField(source='department_ref.name', read_only=True)

    class Meta:
        model = Mentorship
        fields = '__all__'

