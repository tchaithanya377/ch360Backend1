from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection, DatabaseError
import uuid as _uuid

from .models import Student, StudentEnrollmentHistory
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

    # Assign Student role
    from django.contrib.auth.models import Group
    student_group, _ = Group.objects.get_or_create(name='Student')
    user.groups.add(student_group)

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



@receiver(post_save, sender=Student)
def ensure_enrollment_history_on_batch_assignment(sender, instance: Student, created: bool, **kwargs):
    """Create or update StudentEnrollmentHistory when a student's batch is set.

    Rules:
    - When a student has a `student_batch`, ensure there is an Active history row
      for the batch's academic context (year_of_study, semester, academic_year).
    - If an Active row exists for the same combination, do nothing.
    - If there is a different Active row, mark it completed with completion_date=timezone.now().date().
    - Only runs when student has a batch assigned.
    """
    batch = instance.student_batch
    if not batch:
        return

    academic_year = batch.academic_year.year if getattr(batch, 'academic_year', None) else None
    if not academic_year:
        return

    today = timezone.now().date()
    target = {
        'year_of_study': batch.year_of_study,
        'semester': batch.semester,
        'academic_year': academic_year,
    }

    # Close any other active histories not matching current batch context
    active_histories = StudentEnrollmentHistory.objects.filter(
        student=instance,
        status='ACTIVE',
    )

    # If an exact active exists, keep it
    exact = active_histories.filter(**target).first()
    if exact:
        # Ensure enrollment date is set (for newly created student that got batch later)
        updates = []
        if not exact.enrollment_date:
            exact.enrollment_date = instance.enrollment_date or today
            updates.append('enrollment_date')
        # Ensure status and completion are consistent for current active
        if exact.status != 'ACTIVE':
            exact.status = 'ACTIVE'
            updates.append('status')
        if exact.completion_date:
            exact.completion_date = None
            updates.append('completion_date')
        if updates:
            exact.save(update_fields=updates)
        return

    # Close other actives
    for row in active_histories.exclude(**target):
        row.status = 'INACTIVE'
        if not row.completion_date:
            row.completion_date = today
        row.save(update_fields=['status', 'completion_date'])

    # Create the current active history
    StudentEnrollmentHistory.objects.create(
        student=instance,
        year_of_study=target['year_of_study'],
        semester=target['semester'],
        academic_year=target['academic_year'],
        enrollment_date=instance.enrollment_date or today,
        status='ACTIVE',
    )

