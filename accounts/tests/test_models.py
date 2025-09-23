import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_bakery import baker

from accounts.models import (
    User,
    Role,
    Permission,
    RolePermission,
    UserRole,
    AuthIdentifier,
    IdentifierType,
    FailedLogin,
    PasswordReset,
    MfaSetup,
    UserSession,
    AuditLog,
)


pytestmark = pytest.mark.django_db


def test_user_manager_create_user_and_defaults():
    manager = User.objects
    user = manager.create_user(email="user@example.com", password="StrongPass123", username="u1")
    assert isinstance(user, get_user_model())
    assert user.email == "user@example.com"
    assert user.username == "u1"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.check_password("StrongPass123") is True
    assert user.password_updated_at is not None


def test_user_manager_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email=None, password="x", username="u")


@pytest.mark.parametrize(
    "is_staff,is_superuser,should_raise",
    [
        (True, True, False),
        (False, True, True),
        (True, False, True),
    ],
)
def test_user_manager_create_superuser_validation(is_staff, is_superuser, should_raise):
    extra = {"is_staff": is_staff, "is_superuser": is_superuser}
    if should_raise:
        with pytest.raises(ValueError):
            User.objects.create_superuser("super@example.com", "StrongPass123", "su", **extra)
    else:
        su = User.objects.create_superuser("super@example.com", "StrongPass123", "su", **extra)
        assert su.is_staff is True
        assert su.is_superuser is True
        assert su.is_active is True


def test_user_str():
    u = baker.make(User, email="a@b.com")
    assert str(u) == "a@b.com"


def test_user_constraints_indexes():
    u1 = baker.make(User, email="case@example.com", username="c1")
    with pytest.raises(Exception):
        baker.make(User, email="CASE@example.com", username="c2")
    assert u1 is not None


def test_role_and_permission_models_and_uniques():
    role = baker.make(Role, name="Admin")
    perm = baker.make(Permission, codename="accounts.view_secret")
    rp = baker.make(RolePermission, role=role, permission=perm)
    assert str(role) == "Admin"
    assert str(perm) == "accounts.view_secret"
    assert rp is not None
    with pytest.raises(Exception):
        baker.make(RolePermission, role=role, permission=perm)


def test_userrole_unique():
    user = baker.make(User)
    role = baker.make(Role)
    ur = baker.make(UserRole, user=user, role=role)
    assert ur is not None
    with pytest.raises(Exception):
        baker.make(UserRole, user=user, role=role)


def test_authidentifier_uniques_and_constraints():
    user = baker.make(User)
    a1 = baker.make(
        AuthIdentifier,
        user=user,
        identifier="user@example.com",
        id_type=IdentifierType.EMAIL,
        is_primary=True,
    )
    assert a1.is_primary is True
    with pytest.raises(Exception):
        baker.make(
            AuthIdentifier,
            user=user,
            identifier="user@example.com",
            id_type=IdentifierType.EMAIL,
        )
    with pytest.raises(Exception):
        baker.make(
            AuthIdentifier,
            user=user,
            identifier="other@example.com",
            id_type=IdentifierType.EMAIL,
            is_primary=True,
        )


def test_failed_login_model():
    fl = baker.make(FailedLogin, identifier="who@example.com", id_type=IdentifierType.EMAIL)
    assert fl.identifier == "who@example.com"


def test_password_reset_and_is_expired():
    pr = baker.make(PasswordReset, expires_at=timezone.now() + timezone.timedelta(seconds=1))
    assert pr.is_expired() is False
    pr.expires_at = timezone.now() - timezone.timedelta(seconds=1)
    assert pr.is_expired() is True


def test_mfa_setup_model():
    m = baker.make(MfaSetup, secret_encrypted="enc", confirmed=True)
    assert m.confirmed is True


def test_usersession_is_active_and_indexes():
    session = baker.make(
        UserSession,
        revoked=False,
        expires_at=timezone.now() + timezone.timedelta(hours=1),
    )
    assert session.is_active() is True
    session.revoked = True
    assert session.is_active() is False


def test_auditlog_creation_and_indexes():
    log = baker.make(AuditLog, action="LOGIN")
    assert log.action == "LOGIN"


