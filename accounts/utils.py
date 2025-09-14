from __future__ import annotations

from typing import Optional, Tuple

import requests
import time
from django_redis import get_redis_connection


def extract_client_ip(request) -> Optional[str]:
    if request.META.get('HTTP_X_FORWARDED_FOR'):
        return request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def geolocate_ip(ip: Optional[str]) -> Tuple[Optional[dict], Optional[str], Optional[str], Optional[str], Optional[float], Optional[float]]:
    if not ip:
        return None, None, None, None, None, None
    try:
        # Use ipapi.co (no key, rate limited). Swap to paid provider in prod.
        resp = requests.get(f'https://ipapi.co/{ip}/json/', timeout=2)
        if resp.status_code != 200:
            return None, None, None, None, None, None
        data = resp.json()
        country = data.get('country_name')
        region = data.get('region')
        city = data.get('city')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        try:
            lat_f = float(latitude) if latitude is not None else None
            lon_f = float(longitude) if longitude is not None else None
        except Exception:
            lat_f, lon_f = None, None
        return data, country, region, city, lat_f, lon_f
    except Exception:
        return None, None, None, None, None, None

from django.utils import timezone
from .models import AuditLog, User
import uuid


def create_audit_log(user, action, object_type=None, object_id=None, ip=None, user_agent=None, meta=None):
    """
    Utility function to create audit logs manually
    
    Args:
        user: User instance or None
        action: String describing the action
        object_type: Type of object being acted upon
        object_id: ID of the object being acted upon
        ip: IP address of the user
        user_agent: User agent string
        meta: Additional metadata as dict
    """
    return AuditLog.objects.create(
        user=user,
        action=action,
        object_type=object_type or '',
        object_id=object_id,
        ip=ip,
        user_agent=user_agent or '',
        meta=meta or {}
    )


def create_sample_audit_logs():
    """Create sample audit logs for testing"""
    try:
        # Get the first user
        user = User.objects.first()
        if not user:
            print("No users found. Please create a user first.")
            return
        
        # Create sample audit logs
        sample_logs = [
            {
                'action': 'LOGIN',
                'object_type': 'User',
                'object_id': user.id,
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'login_method': 'password', 'success': True}
            },
            {
                'action': 'USER_UPDATED',
                'object_type': 'User',
                'object_id': user.id,
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'fields_changed': ['last_login'], 'old_values': {}, 'new_values': {'last_login': timezone.now().isoformat()}}
            },
            {
                'action': 'STUDENT_CREATED',
                'object_type': 'Student',
                'object_id': str(uuid.uuid4()),
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'student_name': 'John Doe', 'roll_number': 'STU001', 'grade_level': 'GRADE_10'}
            },
            {
                'action': 'FACULTY_UPDATED',
                'object_type': 'Faculty',
                'object_id': str(uuid.uuid4()),
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'faculty_name': 'Dr. Jane Smith', 'department': 'Computer Science', 'fields_changed': ['phone']}
            },
            {
                'action': 'EXAM_SCHEDULED',
                'object_type': 'ExamSchedule',
                'object_id': str(uuid.uuid4()),
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'exam_name': 'Midterm Exam', 'subject': 'Mathematics', 'date': '2024-01-15', 'duration': '2 hours'}
            },
            {
                'action': 'FEE_PAYMENT',
                'object_type': 'Payment',
                'object_id': str(uuid.uuid4()),
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'amount': 5000, 'currency': 'INR', 'payment_method': 'online', 'student_id': 'STU001'}
            },
            {
                'action': 'ATTENDANCE_MARKED',
                'object_type': 'AttendanceRecord',
                'object_id': str(uuid.uuid4()),
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'student_id': 'STU001', 'subject': 'Mathematics', 'status': 'present', 'date': '2024-01-10'}
            },
            {
                'action': 'SYSTEM_BACKUP',
                'object_type': 'System',
                'object_id': None,
                'ip': '127.0.0.1',
                'user_agent': 'System/Backup',
                'meta': {'backup_type': 'full', 'size': '2.5GB', 'duration': '15 minutes', 'status': 'success'}
            },
            {
                'action': 'LOGIN_FAILED',
                'object_type': '',
                'object_id': None,
                'ip': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'identifier': 'invalid@email.com', 'reason': 'Invalid credentials', 'attempt_count': 3}
            },
            {
                'action': 'LOGOUT',
                'object_type': 'User',
                'object_id': user.id,
                'ip': '127.0.0.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'meta': {'session_duration': '2 hours 30 minutes'}
            }
        ]
        
        # Create the audit logs
        created_logs = []
        for log_data in sample_logs:
            log = create_audit_log(
                user=user if log_data['action'] in ['LOGIN', 'USER_UPDATED', 'LOGOUT'] else None,
                action=log_data['action'],
                object_type=log_data['object_type'],
                object_id=log_data['object_id'],
                ip=log_data['ip'],
                user_agent=log_data['user_agent'],
                meta=log_data['meta']
            )
            created_logs.append(log)
        
        print(f"Created {len(created_logs)} sample audit logs")
        return created_logs
        
    except Exception as e:
        print(f"Error creating sample audit logs: {e}")
        return []


# ------------------
# Redis Rate Limiter
# ------------------

class RateLimitExceeded(Exception):
    pass


def _rl_redis():
    try:
        return get_redis_connection("default")
    except Exception:
        return None


def rate_limit_key(scope: str, key: str) -> str:
    return f"ratelimit:{scope}:{key}"


def allow_request(scope: str, key: str, limit: int, window_seconds: int) -> bool:
    r = _rl_redis()
    if r is None:
        return True
    now = int(time.time())
    bucket = now // window_seconds
    k = f"{rate_limit_key(scope, key)}:{bucket}"
    with r.pipeline() as p:
        p.incr(k, 1)
        p.expire(k, window_seconds * 2)
        cnt, _ = p.execute()
    return int(cnt) <= limit


def ratelimit(scope: str, limit: int, window_seconds: int, key_func=None):
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):
            rk = key_func(request) if key_func else (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or 'unknown')
            if not allow_request(scope, rk, limit, window_seconds):
                raise RateLimitExceeded('rate limit exceeded')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
