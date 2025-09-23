import pytest
from django.contrib.auth import get_user_model
from accounts.backends import EmailBackend


pytestmark = pytest.mark.django_db


def test_email_backend_multiple_objects_returned(monkeypatch):
    User = get_user_model()
    User.objects.create_user(email="dup1@example.com", username="dup", password="Pass123456")

    # Monkeypatch manager.get to raise MultipleObjectsReturned to exercise the branch
    class DummyMgr:
        def get(self, *args, **kwargs):
            raise User.MultipleObjectsReturned

    monkeypatch.setattr(User, "objects", DummyMgr())

    backend = EmailBackend()
    result = backend.authenticate(request=None, username='dup', password='Pass123456')
    assert result is None

