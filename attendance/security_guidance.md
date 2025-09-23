# Security and Privacy Implementation Guidance
## CampsHub360 Enhanced Attendance System

### Table of Contents
1. [Data Classification and Encryption](#data-classification-and-encryption)
2. [Authentication and Authorization](#authentication-and-authorization)
3. [Data Retention and Privacy](#data-retention-and-privacy)
4. [Biometric Data Handling](#biometric-data-handling)
5. [Network Security](#network-security)
6. [Audit and Compliance](#audit-and-compliance)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Implementation Checklist](#implementation-checklist)

---

## Data Classification and Encryption

### 1. Data Sensitivity Levels

#### **Highly Sensitive (Encrypt at Rest + Transit)**
- Biometric templates (fingerprint, face, iris data)
- Aadhar numbers and government IDs
- Student personal information (DOB, address, phone)
- Attendance records with location data
- Audit logs containing PII

#### **Moderately Sensitive (Encrypt in Transit)**
- Student roll numbers and academic records
- Faculty information
- Course and timetable data
- Attendance statistics and reports

#### **Low Sensitivity (Standard Protection)**
- System configurations
- Public academic calendar data
- Non-personal metadata

### 2. Encryption Implementation

```python
# settings.py - Encryption Configuration
import os
from cryptography.fernet import Fernet

# Generate encryption key (store securely in environment)
ATTENDANCE_ENCRYPTION_KEY = os.getenv('ATTENDANCE_ENCRYPTION_KEY', Fernet.generate_key())

# Database encryption for sensitive fields
FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY', Fernet.generate_key())

# Encryption settings
ENCRYPTION_ALGORITHM = 'AES-256-GCM'
ENCRYPTION_KEY_ROTATION_DAYS = 90
```

```python
# attendance/encryption.py
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import json

class AttendanceEncryption:
    """Encryption utilities for attendance data"""
    
    def __init__(self):
        self.cipher = Fernet(settings.ATTENDANCE_ENCRYPTION_KEY)
    
    def encrypt_biometric_data(self, template_data):
        """Encrypt biometric template data"""
        if isinstance(template_data, dict):
            template_data = json.dumps(template_data)
        
        encrypted_data = self.cipher.encrypt(template_data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_biometric_data(self, encrypted_data):
        """Decrypt biometric template data"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt biometric data: {str(e)}")
    
    def encrypt_pii_field(self, field_value):
        """Encrypt PII fields like Aadhar, phone numbers"""
        if not field_value:
            return field_value
        
        encrypted_data = self.cipher.encrypt(str(field_value).encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_pii_field(self, encrypted_value):
        """Decrypt PII fields"""
        if not encrypted_value:
            return encrypted_value
        
        try:
            decoded_data = base64.b64decode(encrypted_value.encode())
            return self.cipher.decrypt(decoded_data).decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt PII field: {str(e)}")
```

### 3. Database-Level Encryption

```sql
-- PostgreSQL Column-Level Encryption
-- Create extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Example: Encrypt biometric templates
ALTER TABLE attendance_biometric_template 
ADD COLUMN template_data_encrypted BYTEA;

-- Encrypt existing data
UPDATE attendance_biometric_template 
SET template_data_encrypted = pgp_sym_encrypt(template_data, 'encryption_key_here')
WHERE template_data IS NOT NULL;

-- Create function for automatic encryption
CREATE OR REPLACE FUNCTION encrypt_biometric_template()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.template_data IS NOT NULL THEN
        NEW.template_data_encrypted := pgp_sym_encrypt(NEW.template_data, 'encryption_key_here');
        NEW.template_data := NULL; -- Clear plaintext
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER encrypt_biometric_trigger
    BEFORE INSERT OR UPDATE ON attendance_biometric_template
    FOR EACH ROW
    EXECUTE FUNCTION encrypt_biometric_template();
```

---

## Authentication and Authorization

### 1. JWT Token Security

```python
# settings.py - JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Short-lived access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),     # Refresh tokens
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': 'campushub360-attendance',
    'ISSUER': 'campushub360-api',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
```

### 2. Role-Based Access Control

```python
# attendance/permissions.py
from rest_framework import permissions
from django.contrib.auth.models import Permission

class AttendancePermissionMixin:
    """Mixin for attendance-specific permissions"""
    
    def has_attendance_permission(self, user, action, resource):
        """Check if user has specific attendance permission"""
        permission_codename = f'attendance.{action}_{resource}'
        return user.has_perm(permission_codename)

class FacultyAttendancePermission(permissions.BasePermission):
    """Permission class for faculty attendance operations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Faculty can manage their own sessions
        if request.user.groups.filter(name='Faculty').exists():
            return True
        
        # Admin can manage all sessions
        if request.user.is_staff:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Faculty can only manage their own sessions
        if hasattr(obj, 'faculty') and obj.faculty.user == request.user:
            return True
        
        return False

class StudentAttendancePermission(permissions.BasePermission):
    """Permission class for student attendance operations"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Students can view their own attendance
        if request.user.groups.filter(name='Student').exists():
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Students can only access their own records
        if hasattr(obj, 'student') and obj.student.user == request.user:
            return True
        
        return False

class AdminAttendancePermission(permissions.BasePermission):
    """Permission class for admin attendance operations"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff
```

### 3. API Rate Limiting

```python
# attendance/rate_limits.py
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from rest_framework.response import Response
from rest_framework import status

# Rate limit configurations
ATTENDANCE_RATE_LIMITS = {
    'qr_scan': '100/minute',      # 100 QR scans per minute per user
    'bulk_mark': '10/minute',     # 10 bulk operations per minute per user
    'session_management': '20/minute',  # 20 session operations per minute
    'statistics_query': '60/minute',    # 60 statistics queries per minute
    'export_data': '5/hour',      # 5 exports per hour per user
}

def attendance_rate_limit(view_func):
    """Decorator for attendance-specific rate limiting"""
    return ratelimit(
        key='user',
        rate=ATTENDANCE_RATE_LIMITS.get('default', '100/hour'),
        method='POST',
        block=True
    )(view_func)

def qr_scan_rate_limit(view_func):
    """Rate limit for QR scanning"""
    return ratelimit(
        key='user',
        rate=ATTENDANCE_RATE_LIMITS['qr_scan'],
        method='POST',
        block=True
    )(view_func)

def bulk_mark_rate_limit(view_func):
    """Rate limit for bulk marking"""
    return ratelimit(
        key='user',
        rate=ATTENDANCE_RATE_LIMITS['bulk_mark'],
        method='POST',
        block=True
    )(view_func)
```

---

## Data Retention and Privacy

### 1. Data Retention Policy

```python
# attendance/data_retention.py
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class DataRetentionManager:
    """Manages data retention policies for attendance system"""
    
    RETENTION_POLICIES = {
        'attendance_records': 7 * 365,  # 7 years (UGC requirement)
        'audit_logs': 3 * 365,          # 3 years
        'biometric_templates': 1 * 365,  # 1 year (after student graduation)
        'session_data': 2 * 365,        # 2 years
        'statistics': 5 * 365,          # 5 years
        'export_logs': 1 * 365,         # 1 year
    }
    
    @classmethod
    def get_retention_date(cls, data_type):
        """Get cutoff date for data retention"""
        days = cls.RETENTION_POLICIES.get(data_type, 365)
        return timezone.now().date() - timedelta(days=days)
    
    @classmethod
    def cleanup_expired_data(cls):
        """Clean up data that exceeds retention period"""
        from .models_enhanced import (
            AttendanceRecord, AttendanceAuditLog, 
            BiometricTemplate, AttendanceSession
        )
        
        # Clean up old attendance records
        cutoff_date = cls.get_retention_date('attendance_records')
        old_records = AttendanceRecord.objects.filter(
            session__scheduled_date__lt=cutoff_date
        )
        deleted_count = old_records.count()
        old_records.delete()
        
        # Clean up old audit logs
        cutoff_date = cls.get_retention_date('audit_logs')
        old_logs = AttendanceAuditLog.objects.filter(
            created_at__date__lt=cutoff_date
        )
        old_logs.delete()
        
        # Clean up biometric templates for graduated students
        cutoff_date = cls.get_retention_date('biometric_templates')
        old_templates = BiometricTemplate.objects.filter(
            student__status='GRADUATED',
            created_at__date__lt=cutoff_date
        )
        old_templates.delete()
        
        return {
            'attendance_records_deleted': deleted_count,
            'audit_logs_deleted': old_logs.count(),
            'biometric_templates_deleted': old_templates.count()
        }
```

### 2. Privacy Compliance (GDPR/Indian Data Protection)

```python
# attendance/privacy.py
from django.db import models
from django.utils import timezone

class DataConsent(models.Model):
    """Track data consent for students"""
    CONSENT_TYPES = [
        ('ATTENDANCE_TRACKING', 'Attendance Tracking'),
        ('BIOMETRIC_DATA', 'Biometric Data Collection'),
        ('LOCATION_TRACKING', 'Location Tracking'),
        ('DATA_SHARING', 'Data Sharing with Third Parties'),
        ('ANALYTICS', 'Analytics and Reporting'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    consent_text = models.TextField(help_text="Text of consent given")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'consent_type']
    
    def revoke_consent(self):
        """Revoke consent for data processing"""
        self.granted = False
        self.revoked_at = timezone.now()
        self.save()

class DataSubjectRequest(models.Model):
    """Handle data subject requests (GDPR Article 15-22)"""
    REQUEST_TYPES = [
        ('ACCESS', 'Data Access Request'),
        ('RECTIFICATION', 'Data Rectification Request'),
        ('ERASURE', 'Data Erasure Request'),
        ('PORTABILITY', 'Data Portability Request'),
        ('RESTRICTION', 'Processing Restriction Request'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('REJECTED', 'Rejected'),
        ],
        default='PENDING'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    handled_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def generate_data_export(self):
        """Generate data export for student"""
        from .models_enhanced import AttendanceRecord, LeaveApplication
        
        data = {
            'student_info': {
                'roll_number': self.student.roll_number,
                'name': self.student.full_name,
                'email': self.student.email,
            },
            'attendance_records': list(
                AttendanceRecord.objects.filter(student=self.student)
                .values('session__scheduled_date', 'mark', 'marked_at', 'source')
            ),
            'leave_applications': list(
                LeaveApplication.objects.filter(student=self.student)
                .values('leave_type', 'start_date', 'end_date', 'status', 'reason')
            ),
            'export_generated_at': timezone.now().isoformat()
        }
        
        self.response_data = data
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()
        
        return data
```

---

## Biometric Data Handling

### 1. Biometric Data Security

```python
# attendance/biometric_security.py
import hashlib
import hmac
from cryptography.fernet import Fernet
from django.conf import settings

class BiometricSecurityManager:
    """Manages biometric data security and compliance"""
    
    def __init__(self):
        self.encryption_key = settings.BIOMETRIC_ENCRYPTION_KEY
        self.cipher = Fernet(self.encryption_key)
    
    def store_biometric_template(self, student_id, device_id, template_data):
        """Securely store biometric template"""
        # Validate template quality
        if not self._validate_template_quality(template_data):
            raise ValueError("Biometric template quality below threshold")
        
        # Encrypt template data
        encrypted_template = self._encrypt_template(template_data)
        
        # Generate template hash for integrity
        template_hash = self._generate_template_hash(encrypted_template)
        
        # Store in database
        from .models_enhanced import BiometricTemplate
        template = BiometricTemplate.objects.create(
            student_id=student_id,
            device_id=device_id,
            template_data=encrypted_template,
            template_hash=template_hash,
            quality_score=self._calculate_quality_score(template_data)
        )
        
        return template
    
    def _encrypt_template(self, template_data):
        """Encrypt biometric template"""
        if isinstance(template_data, dict):
            import json
            template_data = json.dumps(template_data)
        
        encrypted_data = self.cipher.encrypt(template_data.encode())
        return encrypted_data.hex()
    
    def _decrypt_template(self, encrypted_template):
        """Decrypt biometric template"""
        try:
            encrypted_bytes = bytes.fromhex(encrypted_template)
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt template: {str(e)}")
    
    def _generate_template_hash(self, encrypted_template):
        """Generate hash for template integrity"""
        return hashlib.sha256(encrypted_template.encode()).hexdigest()
    
    def _validate_template_quality(self, template_data):
        """Validate biometric template quality"""
        # Implement quality validation logic
        # Return True if quality is acceptable
        return True
    
    def _calculate_quality_score(self, template_data):
        """Calculate quality score for template"""
        # Implement quality scoring algorithm
        # Return score between 0.0 and 1.0
        return 0.85
    
    def verify_template_integrity(self, template_id):
        """Verify template hasn't been tampered with"""
        from .models_enhanced import BiometricTemplate
        
        template = BiometricTemplate.objects.get(id=template_id)
        current_hash = self._generate_template_hash(template.template_data)
        
        return hmac.compare_digest(template.template_hash, current_hash)
    
    def delete_biometric_data(self, student_id):
        """Securely delete all biometric data for student"""
        from .models_enhanced import BiometricTemplate
        
        templates = BiometricTemplate.objects.filter(student_id=student_id)
        
        for template in templates:
            # Securely overwrite template data
            template.template_data = 'DELETED'
            template.template_hash = 'DELETED'
            template.is_active = False
            template.save()
        
        # Delete records after secure overwrite
        templates.delete()
```

### 2. Biometric Compliance

```python
# attendance/biometric_compliance.py
from django.utils import timezone
from datetime import timedelta

class BiometricComplianceManager:
    """Manages biometric data compliance requirements"""
    
    def __init__(self):
        self.retention_period = timedelta(days=365)  # 1 year after graduation
        self.consent_required = True
    
    def check_biometric_consent(self, student_id):
        """Check if student has given consent for biometric data"""
        from .privacy import DataConsent
        
        consent = DataConsent.objects.filter(
            student_id=student_id,
            consent_type='BIOMETRIC_DATA',
            granted=True,
            revoked_at__isnull=True
        ).first()
        
        return consent is not None
    
    def require_biometric_consent(self, student_id):
        """Require explicit consent before biometric enrollment"""
        if not self.check_biometric_consent(student_id):
            raise PermissionError("Biometric consent required before enrollment")
    
    def audit_biometric_access(self, user_id, action, template_id=None):
        """Audit all biometric data access"""
        from .models_enhanced import AttendanceAuditLog
        
        AttendanceAuditLog.objects.create(
            entity_type="BiometricTemplate",
            entity_id=str(template_id) if template_id else "N/A",
            action=action,
            performed_by_id=user_id,
            reason=f"Biometric {action} operation",
            source="biometric_system"
        )
    
    def cleanup_expired_biometric_data(self):
        """Clean up biometric data after retention period"""
        from .models_enhanced import BiometricTemplate
        from students.models import Student
        
        cutoff_date = timezone.now().date() - self.retention_period
        
        # Find graduated students with expired biometric data
        expired_templates = BiometricTemplate.objects.filter(
            student__status='GRADUATED',
            created_at__date__lt=cutoff_date
        )
        
        deleted_count = expired_templates.count()
        expired_templates.delete()
        
        return deleted_count
```

---

## Network Security

### 1. API Security Headers

```python
# settings.py - Security Headers
SECURE_HEADERS = {
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'X_FRAME_OPTIONS': 'DENY',
    'X_XSS_PROTECTION': '1; mode=block',
    'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains',
    'CONTENT_SECURITY_POLICY': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    'REFERRER_POLICY': 'strict-origin-when-cross-origin',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://app.campushub360.com",
    "https://admin.campushub360.com",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

### 2. API Gateway Security

```python
# attendance/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
import time
import hashlib

class AttendanceSecurityMiddleware(MiddlewareMixin):
    """Security middleware for attendance endpoints"""
    
    def process_request(self, request):
        # Rate limiting per IP
        if not self._check_rate_limit(request):
            return JsonResponse(
                {'error': 'Rate limit exceeded'}, 
                status=429
            )
        
        # Validate request signature for sensitive endpoints
        if request.path.startswith('/attendance/api/records/qr-scan/'):
            if not self._validate_request_signature(request):
                return JsonResponse(
                    {'error': 'Invalid request signature'}, 
                    status=403
                )
        
        # Check for suspicious patterns
        if self._detect_suspicious_activity(request):
            return JsonResponse(
                {'error': 'Suspicious activity detected'}, 
                status=403
            )
    
    def _check_rate_limit(self, request):
        """Check rate limit for IP address"""
        # Implement rate limiting logic
        return True
    
    def _validate_request_signature(self, request):
        """Validate request signature for QR scanning"""
        # Implement signature validation
        return True
    
    def _detect_suspicious_activity(self, request):
        """Detect suspicious activity patterns"""
        # Implement anomaly detection
        return False
```

---

## Audit and Compliance

### 1. Comprehensive Audit Logging

```python
# attendance/audit.py
from django.utils import timezone
from django.db import models
import json

class AttendanceAuditLogger:
    """Comprehensive audit logging for attendance system"""
    
    @staticmethod
    def log_attendance_mark(user, session, student, mark, source, **kwargs):
        """Log attendance marking operation"""
        from .models_enhanced import AttendanceAuditLog
        
        AttendanceAuditLog.objects.create(
            entity_type="AttendanceRecord",
            entity_id=f"{session.id}_{student.id}",
            action="mark_attendance",
            performed_by=user,
            before=kwargs.get('before_data'),
            after={
                'mark': mark,
                'source': source,
                'marked_at': timezone.now().isoformat()
            },
            reason=kwargs.get('reason', 'Attendance marked'),
            source=source,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            session_id=str(session.id),
            student_id=str(student.id)
        )
    
    @staticmethod
    def log_session_operation(user, session, action, **kwargs):
        """Log session management operations"""
        from .models_enhanced import AttendanceAuditLog
        
        AttendanceAuditLog.objects.create(
            entity_type="AttendanceSession",
            entity_id=str(session.id),
            action=action,
            performed_by=user,
            before=kwargs.get('before_data'),
            after=kwargs.get('after_data'),
            reason=kwargs.get('reason', f'Session {action}'),
            source=kwargs.get('source', 'system'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            session_id=str(session.id)
        )
    
    @staticmethod
    def log_biometric_access(user, template, action, **kwargs):
        """Log biometric data access"""
        from .models_enhanced import AttendanceAuditLog
        
        AttendanceAuditLog.objects.create(
            entity_type="BiometricTemplate",
            entity_id=str(template.id),
            action=action,
            performed_by=user,
            before=kwargs.get('before_data'),
            after=kwargs.get('after_data'),
            reason=f"Biometric {action}",
            source="biometric_system",
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            student_id=str(template.student.id)
        )
    
    @staticmethod
    def log_data_export(user, export_type, filters, **kwargs):
        """Log data export operations"""
        from .models_enhanced import AttendanceAuditLog
        
        AttendanceAuditLog.objects.create(
            entity_type="DataExport",
            entity_id=f"export_{timezone.now().timestamp()}",
            action="export_data",
            performed_by=user,
            before=None,
            after={
                'export_type': export_type,
                'filters': filters,
                'exported_at': timezone.now().isoformat()
            },
            reason=f"Data export: {export_type}",
            source="export_system",
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent')
        )
```

### 2. Compliance Reporting

```python
# attendance/compliance.py
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone

class ComplianceReporter:
    """Generate compliance reports for attendance system"""
    
    @staticmethod
    def generate_data_retention_report():
        """Generate data retention compliance report"""
        from .models_enhanced import AttendanceRecord, AttendanceAuditLog, BiometricTemplate
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'data_retention_status': {},
            'recommendations': []
        }
        
        # Check attendance records retention
        old_records = AttendanceRecord.objects.filter(
            session__scheduled_date__lt=timezone.now().date() - timedelta(days=7*365)
        ).count()
        
        report['data_retention_status']['attendance_records'] = {
            'total_records': AttendanceRecord.objects.count(),
            'records_over_7_years': old_records,
            'compliance_status': 'COMPLIANT' if old_records == 0 else 'NON_COMPLIANT'
        }
        
        # Check biometric data retention
        old_templates = BiometricTemplate.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=365)
        ).count()
        
        report['data_retention_status']['biometric_templates'] = {
            'total_templates': BiometricTemplate.objects.count(),
            'templates_over_1_year': old_templates,
            'compliance_status': 'COMPLIANT' if old_templates == 0 else 'NON_COMPLIANT'
        }
        
        return report
    
    @staticmethod
    def generate_privacy_compliance_report():
        """Generate privacy compliance report"""
        from .privacy import DataConsent, DataSubjectRequest
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'consent_status': {},
            'data_subject_requests': {}
        }
        
        # Check consent status
        total_students = DataConsent.objects.values('student').distinct().count()
        biometric_consent = DataConsent.objects.filter(
            consent_type='BIOMETRIC_DATA',
            granted=True,
            revoked_at__isnull=True
        ).count()
        
        report['consent_status'] = {
            'total_students': total_students,
            'biometric_consent_granted': biometric_consent,
            'consent_rate': (biometric_consent / total_students * 100) if total_students > 0 else 0
        }
        
        # Check data subject requests
        pending_requests = DataSubjectRequest.objects.filter(status='PENDING').count()
        completed_requests = DataSubjectRequest.objects.filter(status='COMPLETED').count()
        
        report['data_subject_requests'] = {
            'pending_requests': pending_requests,
            'completed_requests': completed_requests,
            'total_requests': pending_requests + completed_requests
        }
        
        return report
    
    @staticmethod
    def generate_security_audit_report():
        """Generate security audit report"""
        from .models_enhanced import AttendanceAuditLog
        
        # Check for suspicious activities
        recent_logs = AttendanceAuditLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        failed_attempts = recent_logs.filter(
            action__in=['failed_login', 'invalid_qr_scan', 'unauthorized_access']
        ).count()
        
        bulk_operations = recent_logs.filter(
            action='bulk_mark'
        ).count()
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'security_metrics': {
                'total_audit_events': recent_logs.count(),
                'failed_attempts': failed_attempts,
                'bulk_operations': bulk_operations,
                'suspicious_activities': failed_attempts > 100  # Threshold
            },
            'recommendations': []
        }
        
        if failed_attempts > 100:
            report['recommendations'].append(
                "High number of failed attempts detected. Review security measures."
            )
        
        return report
```

---

## Monitoring and Alerting

### 1. Security Monitoring

```python
# attendance/monitoring.py
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SecurityMonitor:
    """Monitor security events and send alerts"""
    
    @staticmethod
    def check_failed_attempts():
        """Check for excessive failed attempts"""
        from .models_enhanced import AttendanceAuditLog
        
        recent_failures = AttendanceAuditLog.objects.filter(
            action__in=['failed_login', 'invalid_qr_scan'],
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_failures > 50:  # Threshold
            SecurityMonitor.send_security_alert(
                'High Failed Attempts',
                f'Detected {recent_failures} failed attempts in the last hour'
            )
    
    @staticmethod
    def check_unusual_activity():
        """Check for unusual activity patterns"""
        from .models_enhanced import AttendanceRecord
        
        # Check for unusual bulk operations
        recent_bulk = AttendanceRecord.objects.filter(
            source='bulk_mark',
            marked_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_bulk > 1000:  # Threshold
            SecurityMonitor.send_security_alert(
                'Unusual Bulk Activity',
                f'Detected {recent_bulk} bulk operations in the last hour'
            )
    
    @staticmethod
    def send_security_alert(subject, message):
        """Send security alert email"""
        try:
            send_mail(
                subject=f'SECURITY ALERT: {subject}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.SECURITY_ALERT_RECIPIENTS,
                fail_silently=False
            )
            logger.warning(f"Security alert sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send security alert: {str(e)}")
    
    @staticmethod
    def monitor_biometric_access():
        """Monitor biometric data access"""
        from .models_enhanced import AttendanceAuditLog
        
        recent_biometric_access = AttendanceAuditLog.objects.filter(
            entity_type='BiometricTemplate',
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        
        if recent_biometric_access > 100:  # Threshold
            SecurityMonitor.send_security_alert(
                'High Biometric Access',
                f'Detected {recent_biometric_access} biometric access events in the last hour'
            )
```

### 2. Performance Monitoring

```python
# attendance/performance_monitor.py
import time
from django.db import connection
from django.core.cache import cache

class PerformanceMonitor:
    """Monitor attendance system performance"""
    
    @staticmethod
    def monitor_database_performance():
        """Monitor database query performance"""
        queries = connection.queries
        slow_queries = [q for q in queries if float(q['time']) > 1.0]  # > 1 second
        
        if slow_queries:
            logger.warning(f"Detected {len(slow_queries)} slow database queries")
            for query in slow_queries:
                logger.warning(f"Slow query: {query['sql'][:100]}... ({query['time']}s)")
    
    @staticmethod
    def monitor_api_response_times():
        """Monitor API response times"""
        # This would be implemented with middleware
        pass
    
    @staticmethod
    def check_system_health():
        """Check overall system health"""
        health_status = {
            'database': PerformanceMonitor._check_database_health(),
            'cache': PerformanceMonitor._check_cache_health(),
            'storage': PerformanceMonitor._check_storage_health(),
        }
        
        if not all(health_status.values()):
            SecurityMonitor.send_security_alert(
                'System Health Issue',
                f'System health check failed: {health_status}'
            )
        
        return health_status
    
    @staticmethod
    def _check_database_health():
        """Check database connectivity and performance"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    @staticmethod
    def _check_cache_health():
        """Check cache system health"""
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception:
            return False
    
    @staticmethod
    def _check_storage_health():
        """Check storage system health"""
        try:
            from django.core.files.storage import default_storage
            test_file = 'health_check.txt'
            default_storage.save(test_file, ContentFile(b'test'))
            default_storage.delete(test_file)
            return True
        except Exception:
            return False
```

---

## Implementation Checklist

### Pre-Deployment Security Checklist

- [ ] **Encryption Setup**
  - [ ] Generate and securely store encryption keys
  - [ ] Configure database-level encryption for sensitive fields
  - [ ] Implement field-level encryption for PII data
  - [ ] Set up key rotation procedures

- [ ] **Authentication & Authorization**
  - [ ] Configure JWT tokens with appropriate lifetimes
  - [ ] Implement role-based access control
  - [ ] Set up API rate limiting
  - [ ] Configure CORS policies

- [ ] **Data Protection**
  - [ ] Implement data retention policies
  - [ ] Set up consent management system
  - [ ] Configure data subject request handling
  - [ ] Implement secure data deletion

- [ ] **Biometric Security**
  - [ ] Implement biometric data encryption
  - [ ] Set up consent verification
  - [ ] Configure access auditing
  - [ ] Implement secure deletion procedures

- [ ] **Network Security**
  - [ ] Configure security headers
  - [ ] Set up API gateway security
  - [ ] Implement request validation
  - [ ] Configure SSL/TLS certificates

- [ ] **Audit & Compliance**
  - [ ] Set up comprehensive audit logging
  - [ ] Configure compliance reporting
  - [ ] Implement data retention monitoring
  - [ ] Set up privacy compliance tracking

- [ ] **Monitoring & Alerting**
  - [ ] Configure security monitoring
  - [ ] Set up performance monitoring
  - [ ] Implement alerting system
  - [ ] Configure health checks

### Post-Deployment Security Checklist

- [ ] **Regular Security Tasks**
  - [ ] Monitor failed login attempts
  - [ ] Review audit logs weekly
  - [ ] Check for unusual activity patterns
  - [ ] Verify data retention compliance

- [ ] **Monthly Security Reviews**
  - [ ] Review access permissions
  - [ ] Update security configurations
  - [ ] Test incident response procedures
  - [ ] Review compliance reports

- [ ] **Quarterly Security Tasks**
  - [ ] Rotate encryption keys
  - [ ] Update security policies
  - [ ] Conduct security training
  - [ ] Perform penetration testing

### Emergency Response Procedures

1. **Security Incident Response**
   - Immediately isolate affected systems
   - Notify security team and administrators
   - Preserve evidence and logs
   - Implement containment measures
   - Document incident details

2. **Data Breach Response**
   - Assess scope and impact of breach
   - Notify relevant authorities within 72 hours
   - Inform affected individuals
   - Implement remediation measures
   - Conduct post-incident review

3. **System Compromise Response**
   - Disconnect compromised systems
   - Change all passwords and keys
   - Review and update security measures
   - Monitor for additional compromises
   - Document lessons learned

This comprehensive security and privacy implementation guidance ensures that the CampsHub360 attendance system meets the highest standards for data protection, privacy compliance, and security best practices required for Indian universities and AP state requirements.
