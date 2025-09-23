import pytest
from unittest.mock import Mock, patch

from accounts.utils import (
    extract_client_ip,
    geolocate_ip,
    create_audit_log,
    allow_request,
    rate_limit_key,
)

from accounts.models import AuditLog, User
from accounts.backends import EmailBackend
from accounts.signals import create_audit_log as signals_create_audit
from django.test.client import RequestFactory
from accounts import utils as u
import importlib


pytestmark = pytest.mark.django_db


def test_extract_client_ip_variants():
    req = Mock(META={"HTTP_X_FORWARDED_FOR": "1.2.3.4, 5.6.7.8"})
    assert extract_client_ip(req) == "1.2.3.4"
    req2 = Mock(META={"REMOTE_ADDR": "9.9.9.9"})
    assert extract_client_ip(req2) == "9.9.9.9"
    req3 = Mock(META={})
    assert extract_client_ip(req3) is None


@patch("accounts.utils.requests.get")
def test_geolocate_ip_success(mock_get):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "country_name": "Country",
        "region": "Reg",
        "city": "City",
        "latitude": "10.1",
        "longitude": "20.2",
    }
    mock_get.return_value = mock_resp
    raw, country, region, city, lat, lon = geolocate_ip("8.8.8.8")
    assert country == "Country" and region == "Reg" and city == "City"
    assert lat == 10.1 and lon == 20.2


@patch("accounts.utils.requests.get")
def test_geolocate_ip_non_200_and_errors(mock_get):
    mock_resp = Mock(status_code=500)
    mock_get.return_value = mock_resp
    assert geolocate_ip("8.8.8.8") == (None, None, None, None, None, None)
    assert geolocate_ip(None) == (None, None, None, None, None, None)


@patch("accounts.utils.requests.get")
def test_geolocate_ip_outer_exception(mock_get):
    mock_get.side_effect = Exception("boom")
    assert geolocate_ip("1.1.1.1") == (None, None, None, None, None, None)


@patch("accounts.utils.requests.get")
def test_geolocate_ip_non_numeric_lat_lon(mock_get):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "country_name": "C",
        "region": "R",
        "city": "Ci",
        "latitude": "not-a-number",
        "longitude": "NaN",
    }
    mock_get.return_value = mock_resp
    raw, country, region, city, lat, lon = geolocate_ip("9.9.9.9")
    assert lat is None and lon is None


def test_create_audit_log_creates_record():
    user = User.objects.create_user(email="ul@example.com", username="ul", password="Pass123456")
    log = create_audit_log(user, "ACTION", "Obj", user.id, "1.1.1.1", "UA", {"x": 1})
    assert isinstance(log, AuditLog)
    assert log.action == "ACTION"
    assert log.object_type == "Obj"


def test_rate_limit_key_and_allow_request_without_redis(monkeypatch):
    from accounts import utils as u
    monkeypatch.setattr(u, "_rl_redis", lambda: None)
    k = rate_limit_key("scope", "key")
    assert k == "ratelimit:scope:key"
    assert allow_request("scope", "key", limit=1, window_seconds=1) is True


def test_allow_request_with_fake_redis_and_decorator_blocks(monkeypatch):
    class FakePipe:
        def __init__(self):
            self.cnt = 0
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def incr(self, *args, **kwargs):
            return self
        def expire(self, *args, **kwargs):
            return self
        def execute(self):
            return [9999, True]  # far above the limit
    class FakeRedis:
        def pipeline(self):
            return FakePipe()
    monkeypatch.setattr(u, "_rl_redis", lambda: FakeRedis())
    assert allow_request("scope", "ip", limit=1, window_seconds=1) is False

    # decorator should raise RateLimitExceeded
    decorated = u.ratelimit("s", 1, 1)(lambda request: "ok")
    class R:  # minimal request with META
        META = {"REMOTE_ADDR": "1.1.1.1"}
    with pytest.raises(u.RateLimitExceeded):
        decorated(R())


def test__rl_redis_success_and_exception(monkeypatch):
    class Dummy: pass
    # success
    monkeypatch.setattr(u, "get_redis_connection", lambda name: Dummy())
    assert u._rl_redis() is not None
    # exception path
    def raise_conn(name):
        raise Exception("no redis")
    monkeypatch.setattr(u, "get_redis_connection", raise_conn)
    assert u._rl_redis() is None


def test_create_sample_audit_logs_paths(capfd):
    # Without user -> prints and returns None
    logs = u.create_sample_audit_logs()
    assert logs is None
    # With user -> returns list
    user = User.objects.create_user(email="smp@example.com", username="smp", password="Pass123456")
    logs2 = u.create_sample_audit_logs()
    assert isinstance(logs2, list) and len(logs2) > 0


def test_create_sample_audit_logs_exception(monkeypatch):
    def raise_first():
        raise Exception("boom")
    monkeypatch.setattr(u.User.objects, "first", raise_first)
    # Should handle exception and return []
    res = u.create_sample_audit_logs()
    assert res == []


def test_ratelimit_decorator_allows(monkeypatch):
    # When allow_request returns True, wrapped view returns value
    monkeypatch.setattr(u, "allow_request", lambda *a, **k: True)
    @u.ratelimit("scope", 10, 1)
    def view(request):
        return "ok"
    class Req:
        META = {"REMOTE_ADDR": "2.2.2.2"}
    assert view(Req()) == "ok"


def test_email_backend_authenticate_by_email_and_username():
    user = User.objects.create_user(email="bkd@example.com", username="bkd", password="OkPass123")
    backend = EmailBackend()
    # email
    u1 = backend.authenticate(request=None, username="bkd@example.com", password="OkPass123")
    assert u1 and u1.id == user.id
    # username
    u2 = backend.authenticate(request=None, username="bkd", password="OkPass123")
    assert u2 and u2.id == user.id
    # wrong
    assert backend.authenticate(request=None, username="bkd", password="wrong") is None
    # get_user
    assert backend.get_user(user.id) is not None
    assert backend.get_user("00000000-0000-0000-0000-000000000000") is None


def test_signals_create_audit_log_request_branches():
    # Exercise create_audit_log in signals to cover IP & UA extraction path
    rf = RequestFactory()
    req = rf.get("/x", HTTP_X_FORWARDED_FOR="3.3.3.3", HTTP_USER_AGENT="UAx")
    user = User.objects.create_user(email="scl@example.com", username="scl", password="Pass123456")
    signals_create_audit(user=user, action="X", object_type="Obj", object_id=user.id, request=req)
    assert AuditLog.objects.filter(action="X", user=user).exists()


