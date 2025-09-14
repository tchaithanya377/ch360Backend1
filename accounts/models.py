import uuid
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q, UniqueConstraint, Index
from django.db.models.functions import Lower
try:
    from django.contrib.postgres.indexes import GinIndex
except Exception:  # pragma: no cover - optional import for non-Postgres envs
    GinIndex = None  # type: ignore
from django.utils import timezone


class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, username=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.password_updated_at = timezone.now()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, username=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email=email, password=password, username=username, **extra_fields)


class User(TimeStampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    password_updated_at = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self) -> str:  # pragma: no cover - convenience
        return self.email
    class Meta:
        constraints = [
            UniqueConstraint(Lower('email'), name='uniq_accounts_user_email_lower'),
        ]
        indexes = [
            Index(fields=['is_active']),
        ]


class Role(TimeStampedUUIDModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Permission(TimeStampedUUIDModel):
    codename = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.codename


class RolePermission(TimeStampedUUIDModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')

    class Meta:
        unique_together = ('role', 'permission')
        indexes = [
            Index(fields=['role', 'permission']),
        ]


class UserRole(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'role')
        indexes = [
            Index(fields=['user', 'role']),
        ]


class IdentifierType(models.TextChoices):
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    USERNAME = 'username', 'Username'


class AuthIdentifier(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='identifiers')
    identifier = models.CharField(max_length=255)
    id_type = models.CharField(max_length=20, choices=IdentifierType.choices)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ('id_type', 'identifier'),
        )
        constraints = [
            UniqueConstraint(fields=['user', 'id_type'], condition=Q(is_primary=True), name='uniq_primary_identifier_per_type')
        ]
        indexes = [
            Index(fields=['user', 'id_type', 'is_primary']),
        ]


class FailedLogin(TimeStampedUUIDModel):
    identifier = models.CharField(max_length=255)
    id_type = models.CharField(max_length=20, choices=IdentifierType.choices)
    attempt_time = models.DateTimeField(default=timezone.now)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    reason = models.TextField(blank=True)


class PasswordReset(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    reset_token_hash = models.CharField(max_length=128, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at
    class Meta:
        indexes = [
            Index(fields=['user', 'used']),
        ]


class MfaSetup(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_setups')
    secret_encrypted = models.TextField()
    confirmed = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(null=True, blank=True)


class UserSession(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_token_hash = models.CharField(max_length=128, db_index=True)
    device_info = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=64, null=True, blank=True)
    region = models.CharField(max_length=64, null=True, blank=True)
    city = models.CharField(max_length=64, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_raw = models.JSONField(default=dict, blank=True)
    login_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)

    def is_active(self) -> bool:
        now = timezone.now()
        return (not self.revoked) and (now < self.expires_at)
    class Meta:
        indexes = [
            Index(fields=['user', 'revoked', 'expires_at']),
        ]


class AuditLog(TimeStampedUUIDModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=150)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            Index(fields=['created_at']),
            Index(fields=['user', 'created_at']),
        ] + ([GinIndex(fields=['meta'])] if GinIndex else [])


