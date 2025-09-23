import pytest
from django.urls import reverse, resolve

pytestmark = pytest.mark.django_db


def test_router_urlnames_resolve():
	# Just ensure names are registered by the router
	assert resolve(reverse("achievement-list")).url_name == "achievement-list"
	# namespace is empty string when no namespace is set (not None)
	assert resolve(reverse("achievement-list")).namespace == ""


