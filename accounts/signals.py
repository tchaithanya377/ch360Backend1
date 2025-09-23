from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import AuditLog, User, FailedLogin
import json


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, object_type=None, object_id=None, request=None, meta=None):
    """Helper function to create audit logs"""
    ip = None
    user_agent = ''
    
    if request:
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(
        user=user,
        action=action,
        object_type=object_type or '',
        object_id=object_id,
        ip=ip,
        user_agent=user_agent,
        meta=meta or {}
    )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login"""
    create_audit_log(
        user=user,
        action='LOGIN',
        request=request,
        meta={'login_method': 'password'}
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    create_audit_log(
        user=user,
        action='LOGOUT',
        request=request
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Log failed login attempts"""
    # Create failed login record
    identifier = credentials.get('username', '')
    FailedLogin.objects.create(
        identifier=identifier,
        id_type='email',
        ip=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        reason='Invalid credentials'
    )
    
    # Create audit log
    create_audit_log(
        user=None,
        action='LOGIN_FAILED',
        request=request,
        meta={'identifier': identifier}
    )


@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation and updates"""
    if created:
        action = 'USER_CREATED'
        meta = {
            'email': instance.email,
            'username': instance.username,
            'is_staff': instance.is_staff,
            'is_active': instance.is_active
        }
    else:
        action = 'USER_UPDATED'
        meta = {
            'email': instance.email,
            'username': instance.username,
            'is_staff': instance.is_staff,
            'is_active': instance.is_active
        }
    
    # Get the appropriate ID field based on the model
    entity_id = None
    if hasattr(instance, 'id'):
        entity_id = instance.id
    elif hasattr(instance, 'session_key'):  # Django Session model
        entity_id = instance.session_key
    elif hasattr(instance, 'pk'):
        entity_id = instance.pk
    
    if entity_id:
        # Ensure we only assign a real User instance to the AuditLog.user FK.
        # Tests may call this handler with dummy objects (e.g., having session_key),
        # which should not be assigned to the FK field.
        create_audit_log(
            user=instance if isinstance(instance, User) else None,
            action=action,
            object_type='User',
            object_id=entity_id,
            meta=meta
        )


@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """Log user deletion"""
    # Get the appropriate ID field based on the model
    entity_id = None
    if hasattr(instance, 'id'):
        entity_id = instance.id
    elif hasattr(instance, 'session_key'):  # Django Session model
        entity_id = instance.session_key
    elif hasattr(instance, 'pk'):
        entity_id = instance.pk
    
    if entity_id:
        create_audit_log(
            user=None,  # User is being deleted
            action='USER_DELETED',
            object_type='User',
            object_id=entity_id,
            meta={
                'email': instance.email,
                'username': instance.username
            }
        )


# Generic audit logging for other models
def log_model_changes(sender, **kwargs):
    """Generic signal handler for model changes"""
    instance = kwargs.get('instance')
    created = kwargs.get('created', False)
    
    if not instance:
        return
    
    model_name = instance._meta.model_name
    app_label = instance._meta.app_label
    
    # Skip logging for certain models to avoid noise
    skip_models = ['auditlog', 'failedlogin', 'usersession', 'passwordreset']
    if model_name.lower() in skip_models:
        return
    
    if created:
        action = f'{model_name.upper()}_CREATED'
    else:
        action = f'{model_name.upper()}_UPDATED'
    
    # Try to get the current user from thread local or request
    from django.contrib.auth import get_user
    try:
        current_user = get_user()
    except:
        current_user = None
    
    create_audit_log(
        user=current_user,
        action=action,
        object_type=f'{app_label}.{model_name}',
        object_id=getattr(instance, 'id', None),
        meta={
            'model': f'{app_label}.{model_name}',
            'created': created
        }
    )


# Connect to all models for generic audit logging
from django.apps import apps

for model in apps.get_models():
    if model._meta.app_label in ['accounts', 'students', 'faculty', 'academics', 'attendance', 'enrollment', 'grads', 'rnd', 'fees', 'transportation', 'mentoring', 'feedback', 'open_requests']:
        post_save.connect(log_model_changes, sender=model)
        post_delete.connect(
            lambda sender, instance, **kwargs: create_audit_log(
                user=None,
                action=f'{sender._meta.model_name.upper()}_DELETED',
                object_type=f'{sender._meta.app_label}.{sender._meta.model_name}',
                object_id=getattr(instance, 'id', None),
                meta={'model': f'{sender._meta.app_label}.{sender._meta.model_name}'}
            ),
            sender=model
        )
