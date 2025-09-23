import os
import pytest
from django.conf import settings as dj_settings


@pytest.fixture(scope='session', autouse=True)
def _test_settings_override():
    # Force a fast, local SQLite DB for tests to avoid touching external databases
    dj_settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': False,
        'TEST': {'NAME': ':memory:'},
    }
    # Speed up password hashing in tests
    dj_settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    # Disable DRF throttling during tests if configured
    if hasattr(dj_settings, 'REST_FRAMEWORK'):
        rf = dict(dj_settings.REST_FRAMEWORK or {})
        rf['DEFAULT_THROTTLE_CLASSES'] = []
        rf['DEFAULT_THROTTLE_RATES'] = {}
        dj_settings.REST_FRAMEWORK = rf
    # Ensure DEBUG off noise doesn't affect
    dj_settings.DEBUG = False
    # Disable migrations to avoid heavy/duplicate migration issues in tests
    try:
        apps = list(dj_settings.INSTALLED_APPS)
        dj_settings.MIGRATION_MODULES = {app.split('.')[-1]: None for app in apps}
    except Exception:
        dj_settings.MIGRATION_MODULES = {}


@pytest.fixture(scope='session')
def django_db_modify_db_settings():
    # Ensure pytest-django uses SQLite in-memory before DB setup occurs
    dj_settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': False,
        'TEST': {'NAME': ':memory:'},
    }
    dj_settings.DATABASE_ROUTERS = []


