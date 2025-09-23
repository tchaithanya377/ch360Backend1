import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

from accounts.admin import UserAdmin
from accounts.models import User
from django.contrib.admin.sites import AdminSite
from django.contrib import admin as djadmin


pytestmark = pytest.mark.django_db


def _add_messages_middleware(request):
    setattr(request, "session", {})
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


def test_user_admin_registered_and_actions(rf: RequestFactory):
    assert isinstance(admin.site._registry[User], UserAdmin)

    request = _add_messages_middleware(rf.post("/admin/accounts/user/"))
    ua: UserAdmin = admin.site._registry[User]

    u1 = User.objects.create_user(email="a@b.com", username="a", password="Xx12345678")
    u2 = User.objects.create_user(email="b@b.com", username="b", password="Xx12345678")

    ua.reset_passwords_to_default(request, User.objects.filter(id__in=[u1.id, u2.id]))
    u1.refresh_from_db()
    assert u1.must_change_password is True
    assert u1.check_password("Campus@360")

    request2 = _add_messages_middleware(rf.post(f"/admin/accounts/user/{u2.pk}/reset-password/"))
    response = ua.reset_single_password(request2, object_id=str(u2.pk))
    assert response.status_code in (302, 301)

    request3 = _add_messages_middleware(rf.post(f"/admin/accounts/user/0000/reset-password/"))
    response2 = ua.reset_single_password(request3, object_id="00000000-0000-0000-0000-000000000000")
    assert response2.status_code in (302, 301)

    # Cover get_urls customization indirectly by building them
    urls = ua.get_urls()
    assert any("reset-password" in str(u.pattern) for u in urls)


def test_admin_unregistration_fallback(monkeypatch):
    # Force an exception inside the hide loop to cover except branch
    from accounts import admin as accounts_admin
    called = {"n": 0}
    def raise_unreg(model):
        called["n"] += 1
        raise Exception("fail")
    # Ensure re-import does not fail on User already registered
    try:
        djadmin.site.unregister(User)
    except Exception:
        pass
    # Make register a no-op to avoid AlreadyRegistered for other models on reload
    monkeypatch.setattr(djadmin.site, "register", lambda *args, **kwargs: None, raising=True)
    monkeypatch.setattr(djadmin.site, "unregister", raise_unreg, raising=True)
    # Re-import the module to execute the try/except block
    import importlib
    importlib.reload(accounts_admin)
    assert called["n"] >= 1


def test_admin_user_changelist_loads(admin_client, django_user_model):
    su = django_user_model.objects.create_superuser(email="su@example.com", username="su", password="Admin123456")
    admin_client.force_login(su)
    resp = admin_client.get("/admin/accounts/user/")
    assert resp.status_code == 200


