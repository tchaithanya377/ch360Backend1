import io
import uuid
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from achievements.models import Achievement
from achievements.factories import (
	UserFactory,
	StudentFactory,
	AchievementFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
	return APIClient()


@pytest.fixture
def auth_user():
	return UserFactory()


@pytest.fixture
def auth_client(auth_user):
	client = APIClient()
	client.force_authenticate(user=auth_user)
	return client


def test_unauthenticated_is_401(api_client):
	url = reverse("achievement-list")
	resp = api_client.get(url)
	assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_list_retrieve_update_delete_achievement(auth_client):
	list_url = reverse("achievement-list")

	# Create with file upload
	student = StudentFactory()
	file_content = SimpleUploadedFile("cert.txt", b"ok", content_type="text/plain")
	payload = {
		"title": "Create Via API",
		"category": "AWARD",
		"owner_type": "students.student",
		"owner_id": str(student.id),
		"is_public": True,
		"certificate_file": file_content,
	}
	create_resp = auth_client.post(list_url, data=payload, format="multipart")
	assert create_resp.status_code == status.HTTP_201_CREATED, create_resp.data
	pk = create_resp.data["id"]

	# List
	list_resp = auth_client.get(list_url)
	assert list_resp.status_code == status.HTTP_200_OK
	assert any(item["id"] == pk for item in list_resp.data)

	# Retrieve
	detail_url = reverse("achievement-detail", args=[pk])
	detail_resp = auth_client.get(detail_url)
	assert detail_resp.status_code == status.HTTP_200_OK
	assert detail_resp.data["id"] == pk

	# Update (partial)
	patch_resp = auth_client.patch(detail_url, {"title": "Patched"}, format="json")
	assert patch_resp.status_code == status.HTTP_200_OK
	assert patch_resp.data["title"] == "Patched"

	# Delete
	del_resp = auth_client.delete(detail_url)
	assert del_resp.status_code == status.HTTP_204_NO_CONTENT
	assert not Achievement.objects.filter(id=pk).exists()


def test_filters_and_search_and_ordering(auth_client):
	# Seed data
	a1 = AchievementFactory(title="Alpha", category="AWARD")
	a2 = AchievementFactory(title="Beta", category="PROJECT", is_public=False)
	a3 = AchievementFactory(title="Gamma", category="AWARD")

	list_url = reverse("achievement-list")

	# Filter by category
	r1 = auth_client.get(list_url, {"category": "AWARD"})
	assert r1.status_code == 200
	titles = {x["title"] for x in r1.data}
	assert "Alpha" in titles and "Gamma" in titles
	assert "Beta" not in titles

	# Filter by owner_type
	r2 = auth_client.get(list_url, {"owner_type": "students.student"})
	assert r2.status_code == 200
	assert len(r2.data) >= 3

	# Filter by is_public
	r3 = auth_client.get(list_url, {"is_public": "false"})
	assert r3.status_code == 200
	assert any(x["id"] == str(a2.id) for x in r3.data)

	# Search by title
	r4 = auth_client.get(list_url, {"search": "Alpha"})
	assert r4.status_code == 200
	assert any(x["id"] == str(a1.id) for x in r4.data)

	# Ordering
	r5 = auth_client.get(list_url, {"ordering": "-achieved_on"})
	assert r5.status_code == 200


