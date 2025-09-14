from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection, DatabaseError
import uuid as _uuid

from .models import Student
from accounts.models import AuthIdentifier, IdentifierType, UserSession


User = get_user_model()


@receiver(post_save, sender=Student)
def create_user_for_student(sender, instance: Student, created: bool, **kwargs):
    """Automatically create a User for new students if not linked.

    - Username/email login using roll_number or email
    - Default password: Campus@360
    - Primary identifier created for email (if present) and roll number
    """
    if not created:
        return

    if instance.user:
        return

    # Determine email fallback
    provisional_email = instance.email or f"{instance.roll_number}@students.local"

    # Ensure unique username; use roll number
    username = instance.roll_number

    user = User.objects.create_user(
        email=provisional_email,
        username=username,
        password='Campus@360',
        is_active=True,
    )

    # Link back
    instance.user = user
    instance.save(update_fields=['user'])

    # Create identifiers
    # Email identifier
    if instance.email:
        AuthIdentifier.objects.get_or_create(
            user=user,
            identifier=instance.email,
            id_type=IdentifierType.EMAIL,
            defaults={'is_primary': True, 'is_verified': False},
        )

    # Roll number identifier (store as username type)
    AuthIdentifier.objects.get_or_create(
        user=user,
        identifier=instance.roll_number,
        id_type=IdentifierType.USERNAME,
        defaults={'is_primary': not instance.email, 'is_verified': True},
    )


def record_session(user: User, request):
    """Record a login session with ip/user agent and expiry consistent with JWT."""
    ip = None
    if request.META.get('HTTP_X_FORWARDED_FOR'):
        ip = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    user_agent = request.META.get('HTTP_USER_AGENT', '')
    # expires_at handled by JWT lifetime; store approximate
    from django.conf import settings
    from datetime import timedelta

    lifetime = getattr(settings, 'SIMPLE_JWT', {}).get('ACCESS_TOKEN_LIFETIME') or timedelta(minutes=30)
    expires_at = timezone.now() + lifetime

    try:
        return UserSession.objects.create(
            user=user,
            session_token_hash='jwt',  # marker
            device_info=user_agent[:255],
            ip=ip,
            expires_at=expires_at,
            revoked=False,
        )
    except DatabaseError as e:
        # Fallback path: DB might not yet have geo columns; insert minimal columns
        try:
            now = timezone.now()
            new_id = _uuid.uuid4()
            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO accounts_usersession
                        (id, created_at, updated_at, user_id, session_token_hash, device_info, ip, expires_at, revoked)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        str(new_id), now, now, str(user.id), 'jwt', user_agent[:255], ip, expires_at, False
                    ]
                )
            # Return a lightweight instance
            us = UserSession(
                id=new_id,
                user=user,
                session_token_hash='jwt',
                device_info=user_agent[:255],
                ip=ip,
                expires_at=expires_at,
                revoked=False,
            )
            return us
        except Exception:
            # Last resort: do not block login
            return None


