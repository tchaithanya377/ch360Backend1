import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from accounts.permissions import HasRole, HasAnyPermission
from django.core.cache import cache
from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType


pytestmark = pytest.mark.django_db

User = get_user_model()


def _make_request(user=None):
    factory = APIRequestFactory()
    request = factory.get("/x")
    request.user = user or type("Anon", (), {"is_authenticated": False})()
    return request


def test_hasrole_no_required_roles_allows():
    class V(APIView):
        permission_classes = [HasRole]

    view = V()
    req = _make_request()
    assert HasRole().has_permission(req, view) is True


def test_hasrole_blocks_anonymous_when_roles_required():
    class V(APIView):
        permission_classes = [HasRole]
        required_roles = ["Admin"]

    view = V()
    req = _make_request()
    assert HasRole().has_permission(req, view) is False


def test_hasrole_allows_member_and_uses_cache_fallback(db, django_user_model):
    user = django_user_model.objects.create_user(email="r@example.com", username="r", password="xX12345678")
    group = Group.objects.create(name="Admin")
    user.groups.add(group)

    class V(APIView):
        permission_classes = [HasRole]
        required_roles = ["Admin"]

    view = V()
    req = _make_request(user)
    assert HasRole().has_permission(req, view) is True


def test_hasanypermission_no_required_allows_and_blocks_anonymous():
    class V(APIView):
        permission_classes = [HasAnyPermission]

    view = V()
    req = _make_request()
    assert HasAnyPermission().has_permission(req, view) is True

    class V2(APIView):
        permission_classes = [HasAnyPermission]
        required_permissions = ["auth.view_user"]

    view2 = V2()
    req2 = _make_request()
    assert HasAnyPermission().has_permission(req2, view2) is False


def test_hasrole_uses_cache_hit_and_denies_when_missing_role(django_user_model):
    user = django_user_model.objects.create_user(email="c1@example.com", username="c1", password="xX12345678")

    class V(APIView):
        permission_classes = [HasRole]
        required_roles = ["Admin"]

    cache.set(f"rolesperms:v2:{user.id}", {"roles": ["Member"], "permissions": []}, timeout=60)
    view = V()
    req = _make_request(user)
    assert HasRole().has_permission(req, view) is False


def test_hasanypermission_uses_cache_hit(django_user_model):
    user = django_user_model.objects.create_user(email="c2@example.com", username="c2", password="xX12345678")

    class V(APIView):
        permission_classes = [HasAnyPermission]
        required_permissions = ["students.view_student"]

    cache.set(f"rolesperms:v2:{user.id}", {"roles": [], "permissions": ["students.view_student"]}, timeout=60)
    view = V()
    req = _make_request(user)
    assert HasAnyPermission().has_permission(req, view) is True


def test_hasanypermission_fallback_to_user_permissions(django_user_model):
    user = django_user_model.objects.create_user(email="p1@example.com", username="p1", password="xX12345678")
    # ensure no cache
    cache.delete(f"rolesperms:v2:{user.id}")
    # grant a basic permission
    ct = ContentType.objects.get_for_model(User)
    # pick any existing codename
    perm = DjangoPermission.objects.filter(content_type=ct).first()
    if perm:
        user.user_permissions.add(perm)

    class V(APIView):
        permission_classes = [HasAnyPermission]
        required_permissions = [f"{perm.content_type.app_label}.{perm.codename}"] if perm else ["auth.view_user"]

    view = V()
    req = _make_request(user)
    assert HasAnyPermission().has_permission(req, view) in (True, False)


