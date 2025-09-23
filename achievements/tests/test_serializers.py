import pytest
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from achievements.serializers import AchievementSerializer
from achievements.models import Achievement
from achievements.factories import StudentFactory, AchievementFactory

pytestmark = pytest.mark.django_db


def build_payload_for_student(student, **overrides):
	payload = dict(
		title="Inter-College Hackathon",
		category="PROJECT",
		description="Built an AI app",
		issuer_or_organizer="Tech Club",
		location="Campus",
		owner_type="students.student",
		owner_id=str(student.id),
		is_public=True,
		metadata={"score": 95},
	)
	payload.update(overrides)
	return payload


def test_achievement_serializer_create_sets_generic_owner():
	student = StudentFactory()
	data = build_payload_for_student(student)
	ser = AchievementSerializer(data=data)
	assert ser.is_valid(), ser.errors
	instance = ser.save()
	assert isinstance(instance, Achievement)
	assert instance.owner_type == "students.student"
	assert instance.owner_content_type == ContentType.objects.get_for_model(student.__class__)
	assert instance.owner_object_id == student.id
	# write_only owner_type/owner_id should not be present in output
	out = AchievementSerializer(instance).data
	assert "owner_type" not in out
	assert "owner_id" not in out


def test_achievement_serializer_update_ignores_owner_change():
	obj = AchievementFactory()
	ser = AchievementSerializer(
		obj,
		data={"title": "Updated Title", "owner_type": "faculty.faculty", "owner_id": str(obj.student.id)},
		partial=True,
	)
	assert ser.is_valid(), ser.errors
	updated = ser.save()
	assert updated.title == "Updated Title"
	# owner fields should remain unchanged due to pop in update()
	assert updated.owner_type == "students.student"


def test_achievement_serializer_create_without_owner_fields_is_invalid():
    # Owner fields are write-only required; absence should raise validation error
    ser = AchievementSerializer(data={"title": "No Owner", "category": "OTHER"})
    assert not ser.is_valid()
    assert "owner_type" in ser.errors or "owner_id" in ser.errors


def test_achievement_serializer_invalid_owner_type_raises():
	student = StudentFactory()
	bad_data = build_payload_for_student(student, owner_type="invalidformat")  # no dot
	ser = AchievementSerializer(data=bad_data)
	assert ser.is_valid(), ser.errors
	with pytest.raises(ValueError):
		ser.save()


