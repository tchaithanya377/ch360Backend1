import pytest
from django.contrib import admin
from django.contrib.admin.sites import site
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage

from achievements.admin import AchievementAdmin
from achievements.models import Achievement
from achievements.factories import AchievementFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def rf():
	return RequestFactory()


def test_admin_registered_models():
	# Ensure model is registered
	assert isinstance(site._registry.get(Achievement), admin.ModelAdmin)


def test_achievement_admin_list_display_and_search():
	ma = site._registry[Achievement]
	assert isinstance(ma, AchievementAdmin)
	assert "title" in ma.list_display
	assert any("title" in f for f in ma.search_fields)


def test_owned_entity_admin_owner_display_and_actions(rf):
	ma = site._registry[Achievement]
	obj = AchievementFactory(is_public=False)
	# owner_display
	disp = ma.owner_display(obj)
	assert obj.title or disp

	# actions make_public/make_private
	req = rf.post("/")
	user = UserFactory(is_staff=True, is_superuser=True)
	req.user = user
	# Attach session and messages so message_user works
	session_mw = SessionMiddleware(lambda r: None)
	session_mw.process_request(req)
	req.session.save()
	setattr(req, "_messages", FallbackStorage(req))
	qs = Achievement.objects.filter(id=obj.id)
	ma.make_public(req, qs)
	obj.refresh_from_db()
	assert obj.is_public is True
	ma.make_private(req, qs)
	obj.refresh_from_db()
	assert obj.is_public is False


def test_owned_entity_admin_fieldsets_and_readonly(rf):
	ma = site._registry[Achievement]
	req = rf.get("/")
	req.user = UserFactory(is_staff=True, is_superuser=True)

	# For add form (obj=None) should return base owner section
	fieldsets_add = ma.get_fieldsets(req, obj=None)
	assert isinstance(fieldsets_add, tuple)
	assert "Owner" in fieldsets_add[0][0]

	# For change form (obj present) should include meta section
	obj = AchievementFactory()
	fieldsets_change = ma.get_fieldsets(req, obj=obj)
	titles = [fs[0] for fs in fieldsets_change]
	assert "Metadata" in titles

	# readonly fields should include owner_display and inherent read-onlys
	ro = ma.get_readonly_fields(req, obj=obj)
	assert "owner_display" in ro


