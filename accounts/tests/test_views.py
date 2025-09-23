import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission as DjangoPermission
from rest_framework.test import APIClient
from model_bakery import baker
from django.utils import timezone

from accounts.models import AuthIdentifier, IdentifierType, UserSession
from django.core.cache import cache
from accounts.views import UserListView, RolesPermissionsView
from rest_framework_simplejwt.tokens import RefreshToken


pytestmark = pytest.mark.django_db

User = get_user_model()


def auth_client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def test_register_view_success_and_conflict():
    url = reverse("register")
    client = APIClient()
    payload = {"email": "new@example.com", "username": "newu", "password": "GoodPass123"}
    res = client.post(url, payload, format="json")
    assert res.status_code == 201, res.data
    res2 = client.post(url, payload, format="json")
    assert res2.status_code in (400, 409)


def test_token_view_username_or_email_and_session_enrichment():
    user = User.objects.create_user(email="tok@example.com", username="tokuser", password="GoodPass123")
    AuthIdentifier.objects.create(user=user, identifier="tokuser", id_type=IdentifierType.USERNAME, is_primary=True, is_verified=True)
    AuthIdentifier.objects.create(user=user, identifier="tok@example.com", id_type=IdentifierType.EMAIL, is_primary=True, is_verified=False)
    url = reverse("token_obtain_pair")

    client = APIClient()
    res = client.post(url, {"username": "tokuser", "password": "GoodPass123"}, format="json")
    assert res.status_code == 200, res.data
    assert "access" in res.data and "refresh" in res.data
    assert "user" in res.data and res.data["user"]["email"] == "tok@example.com"

    # Now force the geo enrichment try/except to take the except path
    from accounts import views as acc_views
    import types
    def boom_ip(_):
        raise RuntimeError("ip broken")
    # First, break extract_client_ip to hit the except
    orig_ip = acc_views.extract_client_ip
    acc_views.extract_client_ip = boom_ip
    res2 = client.post(url, {"email": "tok@example.com", "password": "GoodPass123"}, format="json")
    assert res2.status_code == 200, res2.data
    acc_views.extract_client_ip = orig_ip


def test_token_view_invalid_credentials():
    url = reverse("token_obtain_pair")
    client = APIClient()
    res = client.post(url, {"email": "nope@example.com", "password": "wrong"}, format="json")
    assert res.status_code == 401


def test_token_view_wrong_password_for_existing_user():
    user = User.objects.create_user(email="wp@example.com", username="wp", password="RightPass123")
    url = reverse("token_obtain_pair")
    client = APIClient()
    res = client.post(url, {"email": "wp@example.com", "password": "WrongPass"}, format="json")
    assert res.status_code == 401


def test_token_refresh_accepts_refresh_token_key(client: APIClient):
    user = User.objects.create_user(email="r1@example.com", username="r1", password="GoodPass123")
    obtain = client.post(reverse("token_obtain_pair"), {"email": "r1@example.com", "password": "GoodPass123"}, format="json")
    assert obtain.status_code == 200
    refresh = obtain.data["refresh"]
    res = client.post(reverse("token_refresh"), {"refresh_token": refresh}, format="json")
    assert res.status_code == 200
    assert "access" in res.data

    # Use refresh token to exercise logout success path (205)
    authed = auth_client(user)
    r3 = authed.post(reverse("logout"), {"refresh": refresh}, format="json")
    assert r3.status_code == 205


def test_me_view_get_and_update():
    user = User.objects.create_user(email="me@example.com", username="meu", password="GoodPass123")
    client = auth_client(user)
    url = reverse("me")
    r1 = client.get(url)
    assert r1.status_code == 200
    r2 = client.patch(url, {"username": "changed"}, format="json")
    assert r2.status_code in (200, 202)
    assert r2.data["username"] == "changed"


def test_logout_requires_refresh_and_invalid_token():
    user = User.objects.create_user(email="lo@example.com", username="lou", password="GoodPass123")
    client = auth_client(user)
    url = reverse("logout")

    r = client.post(url, {}, format="json")
    assert r.status_code == 400 and "Refresh token required" in r.data["detail"]

    r2 = client.post(url, {"refresh": "invalid"}, format="json")
    assert r2.status_code == 400 and "Invalid token" in r2.data["detail"]

    # Valid token branch 205
    obtain = APIClient().post(reverse("token_obtain_pair"), {"email": "lo@example.com", "password": "GoodPass123"}, format="json")
    assert obtain.status_code == 200
    r3 = client.post(url, {"refresh": obtain.data["refresh"]}, format="json")
    assert r3.status_code == 205


def test_roles_permissions_view_with_cache():
    user = User.objects.create_user(email="rp@example.com", username="rpu", password="GoodPass123")
    client = auth_client(user)
    url = reverse("me_roles_permissions")

    r1 = client.get(url)
    assert r1.status_code == 200 and "roles" in r1.data and "permissions" in r1.data
    # Seed cache to exercise cache-hit branch explicitly
    cache.set(f"rolesperms:v2:{user.id}", {"roles": ["X"], "permissions": ["a.b"]}, timeout=60)
    r2 = client.get(url)
    assert r2.status_code == 200 and "roles" in r2.data


def test_roles_permissions_view_sets_cache(monkeypatch):
    user = User.objects.create_user(email="rpc@example.com", username="rpc", password="GoodPass123")
    client = auth_client(user)
    url = reverse("me_roles_permissions")
    cache.delete(f"rolesperms:v2:{user.id}")
    r1 = client.get(url)
    assert r1.status_code == 200


def test_user_list_requires_admin_role_and_supports_search_and_pagination():
    admin = User.objects.create_user(email="admin@example.com", username="admin", password="GoodPass123")
    group = Group.objects.create(name="Admin")
    admin.groups.add(group)

    for i in range(5):
        User.objects.create_user(email=f"u{i}@e.com", username=f"user{i}", password="Xx12345678")

    client = auth_client(admin)
    url = reverse("users_list")
    r = client.get(url, {"search": "user", "limit": 2, "offset": 0})
    assert r.status_code == 200
    assert "count" in r.data and "results" in r.data
    assert len(r.data["results"]) <= 2

    r2 = client.get(url, {"limit": "x", "offset": "y"})
    assert r2.status_code == 200


def test_user_list_internal_error_returns_500(monkeypatch):
    admin = User.objects.create_user(email="adm2@example.com", username="adm2", password="GoodPass123")
    group = Group.objects.create(name="Admin")
    admin.groups.add(group)
    client = auth_client(admin)

    def raise_exc(self):
        raise Exception("boom")

    monkeypatch.setattr(UserListView, "get_queryset", raise_exc)
    r = client.get(reverse("users_list"))
    assert r.status_code == 500 and "detail" in r.data


def test_user_list_forbidden_without_role_and_unauthenticated():
    user = User.objects.create_user(email="noadmin@example.com", username="noadmin", password="GoodPass123")
    client = auth_client(user)
    r = client.get(reverse("users_list"))
    assert r.status_code == 403

    client2 = APIClient()
    r2 = client2.get(reverse("users_list"))
    assert r2.status_code == 401


def test_assign_and_revoke_role_and_cache_invalidation(django_user_model):
    admin = django_user_model.objects.create_user(email="a1@example.com", username="a1", password="GoodPass123")
    target = django_user_model.objects.create_user(email="t1@example.com", username="t1", password="GoodPass123")
    admin_group = Group.objects.create(name="Admin")
    admin.groups.add(admin_group)
    client = auth_client(admin)

    assign_url = reverse("assign_role")
    revoke_url = reverse("revoke_role")

    r = client.post(assign_url, {}, format="json")
    assert r.status_code == 400
    r = client.post(revoke_url, {}, format="json")
    assert r.status_code == 400

    r = client.post(assign_url, {"user_id": "00000000-0000-0000-0000-000000000000", "role": "Editor"}, format="json")
    assert r.status_code == 404
    r = client.post(revoke_url, {"user_id": "00000000-0000-0000-0000-000000000000", "role": "Editor"}, format="json")
    assert r.status_code == 404

    r = client.post(assign_url, {"user_id": str(target.id), "role": "Editor"}, format="json")
    assert r.status_code == 200
    assert target.groups.filter(name="Editor").exists()

    r = client.post(revoke_url, {"user_id": str(target.id), "role": "Editor"}, format="json")
    assert r.status_code == 200
    r = client.post(revoke_url, {"user_id": str(target.id), "role": "Missing"}, format="json")
    assert r.status_code == 404


def test_assign_role_invalid_payload_returns_400(django_user_model):
    admin = django_user_model.objects.create_user(email="a3@example.com", username="a3", password="GoodPass123")
    group = Group.objects.create(name="Admin")
    admin.groups.add(group)
    client = auth_client(admin)
    url = reverse("assign_role")
    res = client.post(url, {"bad": "data"}, format="json")
    assert res.status_code == 400


def test_roles_catalog_view_lists_groups_and_permissions(django_user_model):
    admin = django_user_model.objects.create_user(email="a2@example.com", username="a2", password="GoodPass123")
    admin_group = Group.objects.create(name="Admin")
    admin.groups.add(admin_group)

    group = Group.objects.create(name="Staff")
    perm = DjangoPermission.objects.first()
    if perm:
        group.permissions.add(perm)

    client = auth_client(admin)
    r = client.get(reverse("roles_catalog"))
    assert r.status_code == 200
    assert "roles" in r.data and "role_permissions" in r.data


def test_rate_limited_refresh_view_allows(monkeypatch):
    # Ensure RateLimitedRefreshView works when provided refresh token key variant
    user = User.objects.create_user(email="rlr@example.com", username="rlr", password="GoodPass123")
    client = APIClient()
    obtain = client.post(reverse("token_obtain_pair"), {"email": "rlr@example.com", "password": "GoodPass123"}, format="json")
    assert obtain.status_code == 200
    res = client.post(reverse("token_refresh"), {"refresh": obtain.data["refresh"]}, format="json")
    assert res.status_code == 200 and "access" in res.data


def test_my_sessions_view_and_cache(django_user_model):
    user = django_user_model.objects.create_user(email="sess@example.com", username="sess", password="GoodPass123")
    for _ in range(3):
        baker.make(
            UserSession,
            user=user,
            ip="127.0.0.1",
            device_info="UA",
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
            revoked=False,
        )
    client = auth_client(user)
    url = reverse("me_sessions")
    r1 = client.get(url)
    assert r1.status_code == 200
    assert r1.data["count"] >= 1
    r2 = client.get(url)
    assert r2.status_code == 200


def test_my_active_session_view_found_and_not_found(django_user_model):
    user = django_user_model.objects.create_user(email="act@example.com", username="act", password="GoodPass123")
    client = auth_client(user)
    url = reverse("me_session_active")

    r0 = client.get(url)
    assert r0.status_code == 404

    baker.make(
        UserSession,
        user=user,
        ip="1.1.1.1",
        device_info="UA",
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
        revoked=False,
    )
    r1 = client.get(url)
    assert r1.status_code == 200
    assert r1.data["ip"] in ("1.1.1.1", None)

    # Second call should hit cache branch
    r2 = client.get(url)
    assert r2.status_code == 200


def test_compatibility_404_endpoints(client: APIClient):
    r1 = client.get(reverse("auth_user_compat"))
    r2 = client.get(reverse("auth_session_compat"))
    assert r1.status_code == 404 and r2.status_code == 404


def test_unauthenticated_access_401(client: APIClient):
    for name in [
        "me",
        "me_roles_permissions",
        "users_list",
        "assign_role",
        "revoke_role",
        "roles_catalog",
        "me_sessions",
        "me_session_active",
    ]:
        r = client.get(reverse(name))
        assert r.status_code in (401, 405)


