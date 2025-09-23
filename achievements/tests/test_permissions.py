import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from achievements.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


def test_anonymous_forbidden_across_endpoints(api_client):
    list_url = reverse("achievement-list")
    detail_url = reverse("achievement-detail", args=["00000000-0000-0000-0000-000000000000"])
    assert api_client.get(list_url).status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.post(list_url, data={"title": "x", "category": "OTHER"}, format="json").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.get(detail_url).status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.patch(detail_url, data={"title": "y"}, format="json").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.delete(detail_url).status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_can_access(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    list_url = reverse("achievement-list")
    resp = api_client.get(list_url)
    assert resp.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT, status.HTTP_200_OK)


