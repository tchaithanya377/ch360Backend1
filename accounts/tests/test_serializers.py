import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from accounts.serializers import RegisterSerializer, UserSerializer
from accounts.forms import UserCreationForm, UserChangeForm
from accounts.serializers import UserSerializer as USerSer


pytestmark = pytest.mark.django_db

User = get_user_model()


def test_register_serializer_success():
    data = {
        "email": "reg@example.com",
        "username": "reguser",
        "password": "GoodPass123",
    }
    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.email == "reg@example.com"
    assert user.username == "reguser"
    assert user.check_password("GoodPass123") is True
    assert user.identifiers.filter(identifier="reg@example.com", is_primary=True).exists()


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"email": "", "username": "u", "password": "GoodPass123"}, "email"),
        ({"email": "x@example.com", "username": "u", "password": "short"}, "password"),
    ],
)
def test_register_serializer_invalid(payload, field):
    serializer = RegisterSerializer(data=payload)
    assert serializer.is_valid() is False
    assert field in serializer.errors


def test_user_serializer_lists_groups_and_permissions_happy():
    user = User.objects.create_user(email="ss@example.com", username="ss", password="GoodPass123")
    ser = UserSerializer(instance=user)
    data = ser.data
    assert "groups" in data and "permissions" in data


def test_user_serializer_permissions_exception(monkeypatch):
    user = User.objects.create_user(email="se@example.com", username="se", password="GoodPass123")
    def boom():
        raise RuntimeError("boom")
    monkeypatch.setattr(user, "get_all_permissions", boom)
    ser = UserSerializer(instance=user)
    assert ser.data["permissions"] == []


def test_user_serializer_groups_and_permissions_handles_exceptions(monkeypatch):
    user = baker.make(User)

    # Cause exception when serializer tries to access groups.values_list
    def raise_values_list(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(user.groups, "values_list", raise_values_list)

    def boom_get_all_permissions():
        raise RuntimeError("boom2")

    monkeypatch.setattr(user, "get_all_permissions", boom_get_all_permissions)

    ser = UserSerializer(instance=user)
    data = ser.data
    assert data["groups"] == []
    assert data["permissions"] == []


def test_user_creation_form_valid_and_password_rules():
    form = UserCreationForm(data={
        "email": "f1@example.com",
        "username": "f1",
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
        "password1": "Pass123456",
        "password2": "Pass123456",
    })
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.check_password("Pass123456")

    # mismatch
    form2 = UserCreationForm(data={
        "email": "f2@example.com",
        "username": "f2",
        "password1": "Pass123456",
        "password2": "Mismatch",
    })
    assert form2.is_valid() is False

    # too short
    form3 = UserCreationForm(data={
        "email": "f3@example.com",
        "username": "f3",
        "password1": "short",
        "password2": "short",
    })
    assert form3.is_valid() is False


def test_user_change_form_sets_password_when_provided():
    user = User.objects.create_user(email="chg@example.com", username="chg", password="Original123")
    form = UserChangeForm(instance=user, data={
        "email": user.email,
        "username": user.username,
        "is_active": True,
        "is_staff": False,
        "is_superuser": False,
        "groups": [],
        "password": "NewSecret123",
    })
    assert form.is_valid(), form.errors
    user2 = form.save()
    assert user2.check_password("NewSecret123")


def test_register_serializer_duplicate_email_invalid():
    # Existing user
    User.objects.create_user(email="dup@example.com", username="dup", password="GoodPass123")
    payload = {"email": "dup@example.com", "username": "dup2", "password": "GoodPass123"}
    ser = RegisterSerializer(data=payload)
    assert ser.is_valid() is False
    assert "email" in ser.errors



