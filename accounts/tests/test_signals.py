import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.test.client import RequestFactory

from accounts.models import AuditLog, FailedLogin
from accounts.signals import create_audit_log
from accounts import signals as sigmod
import uuid


pytestmark = pytest.mark.django_db

User = get_user_model()


def _req(ip="127.0.0.1", ua="UA/1.0"):
    rf = RequestFactory()
    req = rf.post("/login")
    req.META["REMOTE_ADDR"] = ip
    req.META["HTTP_USER_AGENT"] = ua
    return req


def test_login_logout_and_failed_login_audit_and_records():
    user = User.objects.create_user(email="sig@example.com", username="sig", password="Pass123456")

    user_logged_in.send(sender=User, request=_req(), user=user)
    assert AuditLog.objects.filter(action="LOGIN", user=user).exists()

    user_logged_out.send(sender=User, request=_req(), user=user)
    assert AuditLog.objects.filter(action="LOGOUT", user=user).exists()

    user_login_failed.send(sender=User, credentials={"username": "invalid@example.com"}, request=_req("2.2.2.2", "UA2"))
    assert FailedLogin.objects.filter(identifier="invalid@example.com").exists()
    assert AuditLog.objects.filter(action="LOGIN_FAILED").exists()


def test_user_create_update_delete_audit_logs():
    user = User.objects.create_user(email="cud@example.com", username="cud", password="StrongPass123")
    assert AuditLog.objects.filter(action="USER_CREATED", object_id=user.id).exists()
    user.username = "changed"
    user.save()
    assert AuditLog.objects.filter(action="USER_UPDATED", object_id=user.id).exists()
    uid = user.id
    user.delete()
    assert AuditLog.objects.filter(action="USER_DELETED", object_id=uid).exists()


def test_signals_create_audit_log_without_request():
    # Cover create_audit_log branch where no request is provided (ip and UA empty)
    create_audit_log(user=None, action="GENERIC", object_type="Any", object_id=None, request=None, meta={"a": 1})
    assert AuditLog.objects.filter(action="GENERIC").exists()


def test_log_user_deletion_branch_session_key_and_pk():
    # Dummy with session_key path
    class Dummy:
        email = "d1@example.com"
        username = "d1"
        session_key = str(uuid.uuid4())
    sigmod.log_user_deletion(sender=None, instance=Dummy())
    assert AuditLog.objects.filter(action="USER_DELETED", object_type="User").exists()

    # Dummy with pk path
    class Dummy2:
        email = "d2@example.com"
        username = "d2"
        pk = str(uuid.uuid4())
    d2 = Dummy2()
    sigmod.log_user_deletion(sender=None, instance=d2)
    assert AuditLog.objects.filter(action="USER_DELETED", object_id=d2.pk).exists()


def test_generic_log_model_changes_early_return():
    # Calling without instance should hit early return branch
    sigmod.log_model_changes(sender=None)


def test_log_user_changes_session_key_path():
    class Dummy:
        email = "e@example.com"
        username = "e"
        is_staff = False
        is_active = True
        session_key = str(uuid.uuid4())
    d = Dummy()
    sigmod.log_user_changes(sender=None, instance=d, created=False)
    assert AuditLog.objects.filter(action="USER_UPDATED", object_id=d.session_key).exists()


def test_log_user_changes_pk_path():
    class Dummy:
        email = "e2@example.com"
        username = "e2"
        is_staff = False
        is_active = True
        pk = str(uuid.uuid4())
    d = Dummy()
    sigmod.log_user_changes(sender=None, instance=d, created=False)
    assert AuditLog.objects.filter(action="USER_UPDATED", object_id=d.pk).exists()


