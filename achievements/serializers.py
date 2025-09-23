from rest_framework import serializers
from .models import Achievement, Skill, Education, Experience, Publication, Project, ResumeProfile
from django.contrib.contenttypes.models import ContentType


class OwnerMixinSerializer(serializers.ModelSerializer):
    owner_type = serializers.CharField(write_only=True)
    owner_id = serializers.UUIDField(write_only=True)

    def create(self, validated_data):
        owner_type = validated_data.pop('owner_type', None)
        owner_id = validated_data.pop('owner_id', None)
        if owner_type and owner_id:
            # owner_type expected as 'app_label.model' lowercase
            app_label, model = owner_type.split('.')
            ct = ContentType.objects.get_by_natural_key(app_label, model)
            validated_data['owner_content_type'] = ct
            validated_data['owner_object_id'] = owner_id
            validated_data['owner_type'] = owner_type
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('owner_type', None)
        validated_data.pop('owner_id', None)
        return super().update(instance, validated_data)


class AchievementSerializer(OwnerMixinSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'
        extra_kwargs = {
            'owner_content_type': {'required': False, 'read_only': True, 'allow_null': True},
            'owner_object_id': {'required': False, 'read_only': True, 'allow_null': True},
        }


class SkillSerializer(OwnerMixinSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class EducationSerializer(OwnerMixinSerializer):
    class Meta:
        model = Education
        fields = '__all__'


class ExperienceSerializer(OwnerMixinSerializer):
    class Meta:
        model = Experience
        fields = '__all__'


class PublicationSerializer(OwnerMixinSerializer):
    class Meta:
        model = Publication
        fields = '__all__'


class ProjectSerializer(OwnerMixinSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class ResumeProfileSerializer(OwnerMixinSerializer):
    class Meta:
        model = ResumeProfile
        fields = '__all__'