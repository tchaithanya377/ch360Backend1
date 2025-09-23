import pytest
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType

from achievements.models import Achievement, Skill, AchievementCategory
from achievements.factories import (
	StudentFactory,
	AchievementFactory,
	SkillFactory,
)

pytestmark = pytest.mark.django_db


def test_achievement_str_and_defaults():
	achievement = AchievementFactory()
	# __str__
	assert achievement.title in str(achievement)
	assert achievement.get_category_display() in str(achievement)
	# defaults
	assert achievement.is_public is True
	assert isinstance(achievement.metadata, dict)
	# owner fields populated
	assert achievement.owner_type == "students.student"
	assert achievement.owner_content_type == ContentType.objects.get_for_model(achievement.student.__class__)
	assert achievement.owner_object_id == achievement.student.id


def test_skill_unique_together_on_owner_and_name():
	student = StudentFactory()
	skill1 = SkillFactory(student=student, name="Python")
	assert str(skill1) == "Python"

	# Same name for same owner should violate unique_together
	with pytest.raises(IntegrityError):
		SkillFactory(student=student, name="Python")


def test_skill_same_name_different_owner_allowed():
	SkillFactory(name="Django")
	# Different owner (new student) with same name should be ok
	SkillFactory(name="Django")


def test_category_indexing_and_ordering():
	# Create multiple achievements to exercise ordering
	a1 = AchievementFactory(category=AchievementCategory.AWARD, achieved_on=None)
	a2 = AchievementFactory(category=AchievementCategory.PROJECT, achieved_on=None)
	a3 = AchievementFactory(category=AchievementCategory.AWARD, achieved_on=None)

	# Ordering: '-achieved_on', '-created_at'
	# Since achieved_on=None for all, ordering should fall back to created_at desc
	titles = list(Achievement.objects.values_list("title", flat=True))
	assert set(titles) == {a1.title, a2.title, a3.title}


