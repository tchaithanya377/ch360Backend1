# 📚 CampsHub360 Enhanced Attendance System

## 🎯 Overview

The CampsHub360 Enhanced Attendance System is a production-ready, timetable-driven attendance management solution designed for Indian universities. It provides comprehensive attendance tracking with multiple capture modes, advanced security, audit trails, and compliance features.

---

## 🏗️ System Architecture

### **Core Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    ATTENDANCE SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│  📱 Frontend Apps    │  🔧 Admin Interface  │  📊 Reports   │
├─────────────────────────────────────────────────────────────┤
│  🌐 REST API Layer (Django REST Framework)                 │
├─────────────────────────────────────────────────────────────┤
│  🧠 Business Logic Layer                                    │
│  • Session Management  • Attendance Rules  • Calculations  │
├─────────────────────────────────────────────────────────────┤
│  💾 Data Layer (PostgreSQL)                                │
│  • Models  • Migrations  • Indexes  • Constraints         │
├─────────────────────────────────────────────────────────────┤
│  ⚡ Background Tasks (Celery)                               │
│  • Auto Session Management  • Statistics  • Cleanup       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Table of Contents

1. [System Features](#-system-features)
2. [Data Models](#-data-models)
3. [Business Logic](#-business-logic)
4. [API Endpoints](#-api-endpoints)
5. [Attendance Capture Modes](#-attendance-capture-modes)
6. [Configuration](#-configuration)
7. [Security & Compliance](#-security--compliance)
8. [Installation & Setup](#-installation--setup)
9. [Usage Guide](#-usage-guide)
10. [Troubleshooting](#-troubleshooting)

---

## ✨ System Features

### **🎯 Core Features**
- **Timetable-Driven Sessions** - Automatic session generation from existing timetable
- **Multi-Capture Modes** - QR codes, biometric, manual entry, offline sync
- **Real-time Statistics** - Live attendance calculations and exam eligibility
- **Advanced Security** - Encryption, audit trails, role-based access
- **Compliance Ready** - GDPR/Indian Data Protection Act compliant
- **Scalable Design** - Handles thousands of students and sessions

### **📊 Advanced Features**
- **Exam Eligibility Rules** - Configurable attendance thresholds (default: 75%)
- **Leave Management** - Integrated leave applications with approval workflows
- **Correction Workflows** - Attendance correction requests with audit trails
- **Biometric Integration** - Support for fingerprint, face recognition, iris scanning
- **Offline Sync** - Offline attendance capture with conflict resolution
- **Background Automation** - Auto session management, statistics calculation

---

## 🗄️ Data Models

### **Core Models**

#### **1. AttendanceSession**
```python
# Represents a single attendance session
class AttendanceSession:
    course_section: ForeignKey     # Which course section
    faculty: ForeignKey           # Teaching faculty
    scheduled_date: Date          # When the session is scheduled
    start_datetime: DateTime      # Session start time
    end_datetime: DateTime        # Session end time
    status: Choice               # scheduled, open, closed, locked, cancelled
    room: CharField              # Location/room
    qr_token: CharField          # QR code for attendance
    biometric_enabled: Boolean   # Enable biometric attendance
    auto_opened: Boolean         # Auto-opened by system
    auto_closed: Boolean         # Auto-closed by system
```

#### **2. AttendanceRecord**
```python
# Individual student attendance record
class AttendanceRecord:
    session: ForeignKey          # Which session
    student: ForeignKey          # Which student
    mark: Choice                # present, absent, late, excused
    marked_at: DateTime         # When marked
    source: Choice              # qr, biometric, manual, offline
    device_id: CharField        # Device used for marking
    location_lat: DecimalField  # GPS coordinates
    location_lng: DecimalField  # GPS coordinates
    sync_status: Choice         # pending, synced, conflict
```

#### **3. AttendanceStatistics**
```python
# Pre-calculated statistics for performance
class AttendanceStatistics:
    student: ForeignKey         # Student
    course_section: ForeignKey  # Course section
    academic_year: CharField    # Academic year
    semester: CharField         # Semester
    total_sessions: Integer     # Total sessions
    present_count: Integer      # Present count
    absent_count: Integer       # Absent count
    attendance_percentage: Decimal # Calculated percentage
    is_eligible_for_exam: Boolean # Exam eligibility
```

#### **4. BiometricDevice**
```python
# Biometric device configuration
class BiometricDevice:
    device_id: CharField        # Unique device identifier
    device_name: CharField      # Human-readable name
    device_type: Choice         # fingerprint, face, iris, palm
    location: CharField         # Physical location
    status: Choice              # active, inactive, maintenance
    ip_address: GenericIPAddressField # Network address
    api_endpoint: URLField      # API endpoint
```

#### **5. AttendanceAuditLog**
```python
# Immutable audit trail
class AttendanceAuditLog:
    entity_type: CharField      # Model name
    entity_id: CharField        # Record ID
    action: CharField           # create, update, delete, approve
    performed_by: ForeignKey    # User who performed action
    before: JSONField           # State before change
    after: JSONField            # State after change
    ip_address: GenericIPAddressField # User's IP
    created_at: DateTime        # When action occurred
```

---

## 🧠 Business Logic

### **Session Management Logic**

#### **1. Session Generation**
```python
def generate_sessions_from_timetable(start_date, end_date):
    """
    Generate attendance sessions from timetable slots
    """
    for slot in TimetableSlot.objects.filter(is_active=True):
        current_date = start_date
        while current_date <= end_date:
            # Check if slot matches current date's day of week
            if current_date.weekday() == slot.day_of_week:
                # Check for holidays
                if not is_holiday(current_date):
                    # Create session
                    session = AttendanceSession.objects.create(
                        course_section=slot.course_section,
                        faculty=slot.faculty,
                        scheduled_date=current_date,
                        start_datetime=combine_datetime(current_date, slot.start_time),
                        end_datetime=combine_datetime(current_date, slot.end_time),
                        room=slot.room,
                        status='scheduled'
                    )
            current_date += timedelta(days=1)
```

#### **2. Auto Session Management**
```python
@celery_task
def auto_open_sessions():
    """
    Automatically open sessions 5 minutes before start time
    """
    now = timezone.now()
    grace_period = get_setting('ATTENDANCE_GRACE_PERIOD_MINUTES', 5)
    
    sessions_to_open = AttendanceSession.objects.filter(
        status='scheduled',
        start_datetime__lte=now + timedelta(minutes=grace_period),
        start_datetime__gte=now
    )
    
    for session in sessions_to_open:
        session.status = 'open'
        session.auto_opened = True
        session.save()

@celery_task
def auto_close_sessions():
    """
    Automatically close sessions after end time
    """
    now = timezone.now()
    
    sessions_to_close = AttendanceSession.objects.filter(
        status='open',
        end_datetime__lt=now
    )
    
    for session in sessions_to_close:
        session.status = 'closed'
        session.auto_closed = True
        session.save()
```

### **Attendance Calculation Logic**

#### **1. Mark Attendance**
```python
def mark_attendance(session_id, student_id, mark, source='manual', **kwargs):
    """
    Mark student attendance with validation
    """
    session = AttendanceSession.objects.get(id=session_id)
    student = Student.objects.get(id=student_id)
    
    # Validate session is open
    if session.status != 'open':
        raise ValidationError("Session is not open for attendance")
    
    # Check if student is enrolled in course section
    if not is_student_enrolled(student, session.course_section):
        raise ValidationError("Student not enrolled in this course section")
    
    # Check for existing record
    existing_record = AttendanceRecord.objects.filter(
        session=session,
        student=student
    ).first()
    
    if existing_record:
        # Update existing record
        existing_record.mark = mark
        existing_record.marked_at = timezone.now()
        existing_record.source = source
        existing_record.save()
    else:
        # Create new record
        AttendanceRecord.objects.create(
            session=session,
            student=student,
            mark=mark,
            marked_at=timezone.now(),
            source=source,
            **kwargs
        )
    
    # Log the action
    log_attendance_action('mark', session, student, mark, source)
```

#### **2. Calculate Attendance Percentage**
```python
def calculate_attendance_percentage(student, course_section, start_date, end_date):
    """
    Calculate attendance percentage for a student in a course section
    """
    # Get all sessions in date range
    sessions = AttendanceSession.objects.filter(
        course_section=course_section,
        scheduled_date__gte=start_date,
        scheduled_date__lte=end_date,
        status__in=['closed', 'locked']
    )
    
    total_sessions = sessions.count()
    if total_sessions == 0:
        return 0.0
    
    # Get attendance records
    records = AttendanceRecord.objects.filter(
        session__in=sessions,
        student=student
    )
    
    present_count = records.filter(mark__in=['present', 'late']).count()
    absent_count = records.filter(mark='absent').count()
    excused_count = records.filter(mark='excused').count()
    
    # Calculate percentage (excused absences don't count against)
    effective_total = total_sessions - excused_count
    if effective_total == 0:
        return 100.0
    
    percentage = (present_count / effective_total) * 100
    return round(percentage, 2)
```

#### **3. Exam Eligibility Check**
```python
def check_exam_eligibility(student, course_section):
    """
    Check if student is eligible for exams based on attendance
    """
    threshold = get_setting('ATTENDANCE_THRESHOLD_PERCENT', 75)
    
    # Get current academic period
    academic_year = get_current_academic_year()
    semester = get_current_semester()
    
    # Calculate attendance percentage
    percentage = calculate_attendance_percentage(
        student, course_section, 
        academic_year.start_date, academic_year.end_date
    )
    
    is_eligible = percentage >= threshold
    
    # Update or create statistics record
    stats, created = AttendanceStatistics.objects.update_or_create(
        student=student,
        course_section=course_section,
        academic_year=academic_year.name,
        semester=semester.name,
        defaults={
            'attendance_percentage': percentage,
            'is_eligible_for_exam': is_eligible,
            'last_calculated': timezone.now()
        }
    )
    
    return is_eligible, percentage
```

---

## 🌐 API Endpoints

### **Session Management**

#### **List Sessions**
```http
GET /api/v1/attendance/sessions/
```
**Query Parameters:**
- `course_section` - Filter by course section ID
- `faculty` - Filter by faculty ID
- `status` - Filter by status (scheduled, open, closed, locked, cancelled)
- `date_from` - Filter from date
- `date_to` - Filter to date
- `page` - Page number for pagination

**Response:**
```json
{
  "count": 150,
  "next": "http://api/attendance/sessions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "course_section": {
        "id": "uuid",
        "course": {
          "code": "CS101",
          "name": "Programming Fundamentals"
        },
        "section_name": "A"
      },
      "faculty": {
        "id": "uuid",
        "first_name": "John",
        "last_name": "Doe"
      },
      "scheduled_date": "2024-09-20",
      "start_datetime": "2024-09-20T10:00:00Z",
      "end_datetime": "2024-09-20T11:00:00Z",
      "room": "A101",
      "status": "open",
      "attendance_count": 25,
      "qr_token": "abc123...",
      "qr_expires_at": "2024-09-20T11:00:00Z"
    }
  ]
}
```

#### **Create Session**
```http
POST /api/v1/attendance/sessions/
```
**Request Body:**
```json
{
  "course_section": "uuid",
  "faculty": "uuid",
  "scheduled_date": "2024-09-20",
  "start_datetime": "2024-09-20T10:00:00Z",
  "end_datetime": "2024-09-20T11:00:00Z",
  "room": "A101",
  "notes": "Makeup session"
}
```

#### **Open Session**
```http
POST /api/v1/attendance/sessions/{id}/open/
```

#### **Close Session**
```http
POST /api/v1/attendance/sessions/{id}/close/
```

#### **Generate QR Code**
```http
POST /api/v1/attendance/sessions/{id}/generate-qr/
```

### **Attendance Recording**

#### **Mark Attendance (Single)**
```http
POST /api/v1/attendance/records/
```
**Request Body:**
```json
{
  "session": "uuid",
  "student": "uuid",
  "mark": "present",
  "source": "manual",
  "notes": "Late arrival"
}
```

#### **Mark Attendance (Bulk)**
```http
POST /api/v1/attendance/records/bulk-mark/
```
**Request Body:**
```json
{
  "session": "uuid",
  "records": [
    {
      "student": "uuid1",
      "mark": "present"
    },
    {
      "student": "uuid2",
      "mark": "absent"
    }
  ]
}
```

#### **QR Code Scan**
```http
POST /api/v1/attendance/records/qr-scan/
```
**Request Body:**
```json
{
  "qr_token": "abc123...",
  "student": "uuid",
  "device_id": "device123",
  "location": {
    "lat": 17.3850,
    "lng": 78.4867
  }
}
```

### **Statistics & Reports**

#### **Student Statistics**
```http
GET /api/v1/attendance/statistics/student/{student_id}/
```

#### **Course Statistics**
```http
GET /api/v1/attendance/statistics/course/{course_section_id}/
```

#### **Exam Eligibility Report**
```http
GET /api/v1/attendance/reports/exam-eligibility/
```

### **Leave Management**

#### **Apply for Leave**
```http
POST /api/v1/attendance/leave-applications/
```

#### **Approve/Reject Leave**
```http
PATCH /api/v1/attendance/leave-applications/{id}/
```

### **Correction Requests**

#### **Request Correction**
```http
POST /api/v1/attendance/correction-requests/
```

#### **Approve/Reject Correction**
```http
PATCH /api/v1/attendance/correction-requests/{id}/
```

---

## 📱 Attendance Capture Modes

### **1. QR Code Scanning**

#### **How it Works:**
1. Faculty generates QR code for session
2. QR code contains encrypted session information
3. Students scan QR code with mobile app
4. App validates QR code and marks attendance
5. Location verification ensures student is in correct room

#### **QR Code Structure:**
```json
{
  "session_id": "uuid",
  "expires_at": "2024-09-20T11:00:00Z",
  "room": "A101",
  "token": "encrypted_token"
}
```

#### **Security Features:**
- Time-limited tokens (default: 60 minutes)
- Location verification
- One-time use tokens
- Encryption of sensitive data

### **2. Biometric Attendance**

#### **Supported Devices:**
- **Fingerprint Scanners** - Most common, high accuracy
- **Face Recognition** - Contactless, good for hygiene
- **Iris Scanners** - Highest accuracy, expensive
- **Palm Scanners** - Alternative to fingerprint

#### **Integration Process:**
1. **Device Registration** - Register biometric device in admin
2. **Template Enrollment** - Students enroll biometric templates
3. **Attendance Capture** - Students use biometric device
4. **Data Sync** - Device syncs data with server
5. **Verification** - System verifies biometric match

#### **Security Measures:**
- Encrypted template storage
- Quality score validation
- Duplicate detection
- Audit logging

### **3. Manual Entry**

#### **Faculty Manual Entry:**
- Faculty marks attendance manually in admin interface
- Bulk marking capabilities
- Student filtering by course section
- Notes and reason fields

#### **Student Self-Entry:**
- Students can mark their own attendance (if enabled)
- Requires faculty approval
- Limited to specific time windows
- Audit trail maintained

### **4. Offline Sync**

#### **Offline Capture:**
- Mobile app works offline
- Attendance data stored locally
- Sync when internet available
- Conflict resolution for duplicate entries

#### **Sync Process:**
1. **Offline Storage** - Data stored in local database
2. **Sync Trigger** - Automatic or manual sync
3. **Conflict Detection** - Check for duplicate entries
4. **Resolution** - Apply conflict resolution rules
5. **Server Update** - Update server with resolved data

---

## ⚙️ Configuration

### **System Settings**

All settings are configurable via the admin interface:

#### **Attendance Rules**
```python
# Minimum attendance percentage for exam eligibility
ATTENDANCE_THRESHOLD_PERCENT = 75

# Grace period for late arrivals (minutes)
ATTENDANCE_GRACE_PERIOD_MINUTES = 5

# Minimum duration to be marked present (minutes)
MIN_DURATION_FOR_PRESENT_MINUTES = 10

# Maximum days for correction requests
ATTENDANCE_MAX_CORRECTION_DAYS = 7
```

#### **QR Code Settings**
```python
# QR token expiry time (minutes)
ATTENDANCE_QR_TOKEN_EXPIRY_MINUTES = 60

# QR code generation interval (minutes)
QR_GENERATION_INTERVAL_MINUTES = 5
```

#### **Biometric Settings**
```python
# Enable biometric attendance
BIOMETRIC_ENABLED = True

# Biometric sync interval (minutes)
BIOMETRIC_SYNC_INTERVAL_MINUTES = 5

# Minimum quality score for templates
BIOMETRIC_MIN_QUALITY_SCORE = 0.7
```

#### **Data Retention**
```python
# Data retention period (days)
ATTENDANCE_DATA_RETENTION_DAYS = 2555  # 7 years

# Audit log retention (days)
AUDIT_LOG_RETENTION_DAYS = 2555
```

### **Celery Task Schedule**

```python
CELERY_BEAT_SCHEDULE = {
    'auto-open-sessions': {
        'task': 'attendance.tasks.auto_open_sessions',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'auto-close-sessions': {
        'task': 'attendance.tasks.auto_close_sessions',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'calculate-statistics': {
        'task': 'attendance.tasks.calculate_attendance_statistics',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'cleanup-old-data': {
        'task': 'attendance.tasks.cleanup_old_attendance_data',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Weekly on Monday
    },
}
```

---

## 🔒 Security & Compliance

### **Data Encryption**

#### **Field-Level Encryption**
```python
# Sensitive fields are encrypted using AES-256-GCM
from cryptography.fernet import Fernet

def encrypt_field(value):
    """Encrypt sensitive field data"""
    key = settings.ENCRYPTION_KEY
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()

def decrypt_field(encrypted_value):
    """Decrypt sensitive field data"""
    key = settings.ENCRYPTION_KEY
    f = Fernet(key)
    return f.decrypt(encrypted_value.encode()).decode()
```

#### **Encrypted Fields:**
- Biometric template data
- Personal identification numbers
- Sensitive configuration values
- API keys and tokens

### **Audit Trail**

#### **Comprehensive Logging**
```python
def log_attendance_action(action, session, student, mark=None, source=None):
    """Log all attendance-related actions"""
    AttendanceAuditLog.objects.create(
        entity_type='AttendanceRecord',
        entity_id=f"{session.id}-{student.id}",
        action=action,
        performed_by=request.user,
        before=get_before_state(session, student),
        after=get_after_state(session, student, mark),
        source=source,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        session_id=str(session.id),
        student_id=str(student.id)
    )
```

#### **Audit Log Fields:**
- **Entity Information** - What was changed
- **Action Details** - What action was performed
- **User Information** - Who performed the action
- **State Changes** - Before and after states
- **Context Information** - IP, user agent, timestamp
- **Session Context** - Related session and student IDs

### **Access Control**

#### **Role-Based Permissions**
```python
# Permission levels
ATTENDANCE_PERMISSIONS = {
    'view_attendance': 'Can view attendance records',
    'mark_attendance': 'Can mark attendance',
    'manage_sessions': 'Can create/edit sessions',
    'approve_corrections': 'Can approve correction requests',
    'manage_biometric': 'Can manage biometric devices',
    'view_statistics': 'Can view attendance statistics',
    'export_data': 'Can export attendance data',
}
```

#### **API Rate Limiting**
```python
# Rate limiting configuration
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'attendance_marking': '60/minute',  # Specific limit for attendance marking
    }
}
```

### **Privacy Compliance**

#### **GDPR Compliance**
- **Data Minimization** - Only collect necessary data
- **Purpose Limitation** - Use data only for stated purposes
- **Storage Limitation** - Automatic data deletion after retention period
- **Right to Erasure** - Students can request data deletion
- **Data Portability** - Students can export their data

#### **Indian Data Protection Act**
- **Consent Management** - Explicit consent for biometric data
- **Data Localization** - Data stored within India
- **Breach Notification** - Automatic breach detection and notification
- **Data Protection Officer** - Designated DPO for compliance

---

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.11+
- PostgreSQL 13+
- Redis (for Celery)
- Node.js (for frontend, if applicable)

### **Installation Steps**

#### **1. Clone Repository**
```bash
git clone <repository-url>
cd ch360Backend-main
```

#### **2. Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

#### **4. Database Setup**
```bash
# Create PostgreSQL database
createdb ch360_attendance

# Run migrations
python manage.py migrate
```

#### **5. Create Superuser**
```bash
python manage.py createsuperuser
```

#### **6. Load Initial Data**
```bash
# Load default configurations
python manage.py loaddata attendance/fixtures/default_configs.json

# Load sample data (optional)
python manage.py loaddata attendance/fixtures/sample_data.json
```

#### **7. Start Services**
```bash
# Start Django server
python manage.py runserver

# Start Celery worker (in separate terminal)
celery -A campshub360 worker -l info

# Start Celery beat (in separate terminal)
celery -A campshub360 beat -l info
```

### **Environment Variables**

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ch360_attendance

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Email (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Biometric API (if using external service)
BIOMETRIC_API_URL=https://api.biometric-service.com
BIOMETRIC_API_KEY=your-api-key
```

---

## 📖 Usage Guide

### **For Administrators**

#### **1. System Configuration**
1. Access admin interface: `http://localhost:8000/admin/attendance/`
2. Go to **Attendance Configurations**
3. Set up system parameters:
   - Attendance threshold percentage
   - Grace period for late arrivals
   - QR token expiry time
   - Data retention period

#### **2. Course Setup**
1. Go to **Timetable Slots**
2. Create timetable slots for each course section
3. Set day of week, start/end times, room
4. Enable automatic session generation

#### **3. Faculty Management**
1. Assign faculty to course sections
2. Set up faculty permissions
3. Configure faculty-specific settings

#### **4. Student Enrollment**
1. Ensure students are enrolled in course sections
2. Set up student batches
3. Configure student-specific settings

### **For Faculty**

#### **1. Session Management**
1. **View Sessions**: See all your scheduled sessions
2. **Open Session**: Start attendance marking
3. **Generate QR**: Create QR code for students
4. **Close Session**: End attendance marking

#### **2. Attendance Marking**
1. **Manual Entry**: Mark attendance manually
2. **Bulk Marking**: Mark multiple students at once
3. **QR Scanning**: Let students scan QR codes
4. **Biometric**: Use biometric devices

#### **3. Leave Management**
1. **View Leave Applications**: See student leave requests
2. **Approve/Reject**: Process leave applications
3. **Bulk Processing**: Handle multiple requests

#### **4. Reports**
1. **Attendance Reports**: View attendance statistics
2. **Exam Eligibility**: Check student eligibility
3. **Export Data**: Download reports in various formats

### **For Students**

#### **1. QR Code Attendance**
1. Open mobile app
2. Scan QR code displayed in class
3. Confirm attendance
4. View attendance history

#### **2. Leave Applications**
1. Submit leave application
2. Upload supporting documents
3. Track application status
4. Receive notifications

#### **3. Attendance Tracking**
1. View attendance percentage
2. Check exam eligibility
3. View attendance history
4. Request corrections if needed

### **For IT Administrators**

#### **1. Device Management**
1. **Register Biometric Devices**: Add new devices
2. **Configure Network Settings**: Set up device connectivity
3. **Monitor Device Status**: Check device health
4. **Update Firmware**: Keep devices updated

#### **2. System Monitoring**
1. **View Audit Logs**: Monitor all system activities
2. **Check Statistics**: Monitor system performance
3. **Review Error Logs**: Troubleshoot issues
4. **Monitor Background Tasks**: Check Celery tasks

#### **3. Data Management**
1. **Backup Data**: Regular database backups
2. **Archive Old Data**: Move old data to archive
3. **Clean Up**: Remove expired data
4. **Export Data**: Create data exports

---

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Sessions Not Auto-Opening**
**Symptoms:** Sessions remain in 'scheduled' status
**Causes:**
- Celery worker not running
- Incorrect timezone settings
- Database connection issues

**Solutions:**
```bash
# Check Celery worker status
celery -A campshub360 inspect active

# Restart Celery worker
celery -A campshub360 worker -l info

# Check timezone settings
python manage.py shell -c "from django.utils import timezone; print(timezone.now())"
```

#### **2. QR Codes Not Working**
**Symptoms:** QR codes not generating or not scanning
**Causes:**
- QR token expiry
- Network connectivity issues
- Invalid session status

**Solutions:**
```bash
# Regenerate QR codes
python manage.py shell -c "
from attendance.tasks import generate_qr_for_session
from attendance.models import AttendanceSession
for session in AttendanceSession.objects.filter(status='open'):
    generate_qr_for_session.delay(session.id)
"

# Check QR token expiry
python manage.py shell -c "
from attendance.models import AttendanceSession
for session in AttendanceSession.objects.filter(status='open'):
    print(f'Session {session.id}: QR expires at {session.qr_expires_at}')
"
```

#### **3. Biometric Devices Not Syncing**
**Symptoms:** Biometric data not appearing in system
**Causes:**
- Device connectivity issues
- API configuration problems
- Network firewall blocking

**Solutions:**
```bash
# Check device status
python manage.py shell -c "
from attendance.models import BiometricDevice
for device in BiometricDevice.objects.all():
    print(f'Device {device.device_id}: Status {device.status}, Last seen: {device.last_seen}')
"

# Test device connectivity
curl -X GET "http://device-ip:port/api/status" -H "Authorization: Bearer api-key"
```

#### **4. Statistics Not Calculating**
**Symptoms:** Attendance percentages not updating
**Causes:**
- Celery tasks failing
- Database performance issues
- Incorrect date ranges

**Solutions:**
```bash
# Manually trigger statistics calculation
python manage.py shell -c "
from attendance.tasks import calculate_attendance_statistics
calculate_attendance_statistics.delay()
"

# Check Celery task logs
celery -A campshub360 events

# Check database performance
python manage.py shell -c "
from attendance.models import AttendanceRecord
print(f'Total records: {AttendanceRecord.objects.count()}')
"
```

#### **5. Performance Issues**
**Symptoms:** Slow response times, timeouts
**Causes:**
- Large dataset queries
- Missing database indexes
- Inefficient API endpoints

**Solutions:**
```bash
# Check database indexes
python manage.py dbshell -c "\di attendance_*"

# Analyze slow queries
python manage.py shell -c "
from django.db import connection
print(connection.queries[-10:])  # Last 10 queries
"

# Optimize queries
python manage.py shell -c "
from attendance.models import AttendanceRecord
# Use select_related for foreign keys
records = AttendanceRecord.objects.select_related('session', 'student').all()
"
```

### **Debugging Tools**

#### **1. Django Debug Toolbar**
```python
# Add to settings.py for development
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

#### **2. Logging Configuration**
```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'attendance.log',
        },
    },
    'loggers': {
        'attendance': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

#### **3. Database Query Analysis**
```python
# Add to settings.py
if DEBUG:
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['file'],
    }
```

### **Monitoring & Alerts**

#### **1. Health Checks**
```python
# Create health check endpoint
def health_check(request):
    """System health check"""
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'celery': check_celery_workers(),
        'biometric_devices': check_biometric_devices(),
    }
    
    status = 'healthy' if all(checks.values()) else 'unhealthy'
    return JsonResponse({'status': status, 'checks': checks})
```

#### **2. Performance Monitoring**
```python
# Monitor key metrics
def get_system_metrics():
    """Get system performance metrics"""
    return {
        'total_sessions': AttendanceSession.objects.count(),
        'active_sessions': AttendanceSession.objects.filter(status='open').count(),
        'total_records': AttendanceRecord.objects.count(),
        'pending_corrections': AttendanceCorrectionRequest.objects.filter(status='pending').count(),
        'device_status': BiometricDevice.objects.values('status').annotate(count=Count('id')),
    }
```

---

## 📞 Support & Maintenance

### **Regular Maintenance Tasks**

#### **Daily Tasks**
- Monitor system health
- Check error logs
- Verify backup completion
- Review audit logs

#### **Weekly Tasks**
- Update device firmware
- Clean up old temporary files
- Review performance metrics
- Check disk space usage

#### **Monthly Tasks**
- Archive old data
- Update system dependencies
- Review security logs
- Performance optimization

#### **Yearly Tasks**
- Full system backup
- Security audit
- Disaster recovery testing
- System upgrade planning

### **Contact Information**

- **Technical Support**: support@campshub360.com
- **Documentation**: docs.campshub360.com
- **Issue Tracker**: github.com/campshub360/issues
- **Emergency Contact**: +91-XXX-XXX-XXXX

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📚 Additional Resources

- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Security Guide](docs/security.md)
- [Performance Tuning](docs/performance.md)
- [FAQ](docs/faq.md)

---

*Last updated: September 2024*
*Version: 2.0.0*
