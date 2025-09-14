from rest_framework import serializers
from .models import FeedbackCategory, FeedbackTag, Feedback, FeedbackComment, FeedbackAttachment, FeedbackVote
from departments.models import Department
from academics.models import Course, CourseSection, Syllabus
from faculty.models import Faculty


class FeedbackCategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = FeedbackCategory
		fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class FeedbackTagSerializer(serializers.ModelSerializer):
	class Meta:
		model = FeedbackTag
		fields = ['id', 'name', 'created_at', 'updated_at']


class FeedbackSerializer(serializers.ModelSerializer):
	category = FeedbackCategorySerializer(read_only=True)
	category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=FeedbackCategory.objects.all(), write_only=True, required=False, allow_null=True)
	tags = FeedbackTagSerializer(many=True, read_only=True)
	tag_ids = serializers.PrimaryKeyRelatedField(source='tags', queryset=FeedbackTag.objects.all(), many=True, write_only=True, required=False)
	created_by = serializers.StringRelatedField(read_only=True)
	department_id = serializers.PrimaryKeyRelatedField(source='department', queryset=Department.objects.all(), write_only=True, required=False, allow_null=True)
	course_id = serializers.PrimaryKeyRelatedField(source='course', queryset=Course.objects.all(), write_only=True, required=False, allow_null=True)
	section_id = serializers.PrimaryKeyRelatedField(source='section', queryset=CourseSection.objects.all(), write_only=True, required=False, allow_null=True)
	faculty_id = serializers.PrimaryKeyRelatedField(source='faculty', queryset=Faculty.objects.all(), write_only=True, required=False, allow_null=True)
	syllabus_id = serializers.PrimaryKeyRelatedField(source='syllabus', queryset=Syllabus.objects.all(), write_only=True, required=False, allow_null=True)

	class Meta:
		model = Feedback
		fields = [
			'id', 'title', 'description', 'category', 'category_id', 'created_by', 'is_anonymous',
			'status', 'priority', 'rating', 'sentiment',
			'department_id', 'course_id', 'section_id', 'faculty_id', 'syllabus_id',
			'target_type', 'target_id', 'tags', 'tag_ids', 'created_at', 'updated_at'
		]

	def create(self, validated_data):
		tags = validated_data.pop('tags', [])
		feedback = Feedback.objects.create(created_by=self.context['request'].user, **validated_data)
		if tags:
			feedback.tags.set(tags)
		return feedback

	def update(self, instance, validated_data):
		tags = validated_data.pop('tags', None)
		for attr, value in validated_data.items():
			setattr(instance, attr, value)
		instance.save()
		if tags is not None:
			instance.tags.set(tags)
		return instance


class FeedbackCommentSerializer(serializers.ModelSerializer):
	commented_by = serializers.StringRelatedField(read_only=True)

	class Meta:
		model = FeedbackComment
		fields = ['id', 'feedback', 'commented_by', 'content', 'is_internal', 'created_at']
		read_only_fields = ['commented_by']

	def create(self, validated_data):
		return FeedbackComment.objects.create(commented_by=self.context['request'].user, **validated_data)


class FeedbackAttachmentSerializer(serializers.ModelSerializer):
	uploaded_by = serializers.StringRelatedField(read_only=True)

	class Meta:
		model = FeedbackAttachment
		fields = ['id', 'feedback', 'uploaded_by', 'file_url', 'description', 'created_at']
		read_only_fields = ['uploaded_by']

	def create(self, validated_data):
		return FeedbackAttachment.objects.create(uploaded_by=self.context['request'].user, **validated_data)


class FeedbackVoteSerializer(serializers.ModelSerializer):
	class Meta:
		model = FeedbackVote
		fields = ['id', 'feedback', 'voted_by', 'is_upvote', 'created_at']
		read_only_fields = ['voted_by']

	def create(self, validated_data):
		return FeedbackVote.objects.create(voted_by=self.context['request'].user, **validated_data)
