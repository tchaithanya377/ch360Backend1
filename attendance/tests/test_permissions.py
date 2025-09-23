"""
Tests for attendance permissions.
"""

from django.test import TestCase, RequestFactory
from attendance.permissions import IsAdminOrReadOnly
from attendance.tests.factories import UserFactory, AdminUserFactory


class TestIsAdminOrReadOnly(TestCase):
    """Test IsAdminOrReadOnly permission"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()
        self.admin_user = AdminUserFactory()
        self.permission = IsAdminOrReadOnly()

    def test_read_permission_authenticated_user(self):
        """Test that authenticated users can read"""
        request = self.factory.get('/api/test/')
        request.user = self.user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_write_permission_admin_user(self):
        """Test that admin users can write"""
        request = self.factory.post('/api/test/')
        request.user = self.admin_user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_write_permission_regular_user(self):
        """Test that regular users cannot write"""
        request = self.factory.post('/api/test/')
        request.user = self.user
        self.assertFalse(self.permission.has_permission(request, None))
