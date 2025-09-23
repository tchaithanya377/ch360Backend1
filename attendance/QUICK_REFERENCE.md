# 🚀 Attendance System - Quick Reference Guide

## 📋 Quick Start

### **1. Start the System**
```bash
# Start Django server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A campshub360 worker -l info

# Start Celery beat (separate terminal)
celery -A campshub360 beat -l info
```

### **2. Access Points**
- **Admin Interface**: `http://localhost:8000/admin/attendance/`
- **API Base URL**: `http://localhost:8000/api/v1/attendance/`
- **API Documentation**: `http://localhost:8000/api/docs/`

---

## 🎯 Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **QR Code Scanning** | Students scan QR codes for attendance | ✅ Active |
| **Biometric Attendance** | Fingerprint, face, iris scanning | ✅ Active |
| **Manual Entry** | Faculty manual attendance marking | ✅ Active |
| **Offline Sync** | Offline attendance with sync | ✅ Active |
| **Auto Session Management** | Auto open/close sessions | ✅ Active |
| **Exam Eligibility** | 75% threshold calculation | ✅ Active |
| **Leave Management** | Leave applications & approvals | ✅ Active |
| **Correction Workflows** | Attendance correction requests | ✅ Active |
| **Audit Trails** | Complete change tracking | ✅ Active |
| **Real-time Statistics** | Live attendance calculations | ✅ Active |

---

## 📊 Core Models

### **AttendanceSession**
- **Purpose**: Represents a single attendance session
- **Key Fields**: course_section, faculty, scheduled_date, status, qr_token
- **Statuses**: scheduled → open → closed → locked

### **AttendanceRecord**
- **Purpose**: Individual student attendance record
- **Key Fields**: session, student, mark, marked_at, source
- **Marks**: present, absent, late, excused
- **Sources**: qr, biometric, manual, offline

### **AttendanceStatistics**
- **Purpose**: Pre-calculated statistics for performance
- **Key Fields**: student, course_section, attendance_percentage, is_eligible_for_exam

---

## 🔧 Configuration Settings

### **Essential Settings**
```python
# Minimum attendance for exam eligibility
ATTENDANCE_THRESHOLD_PERCENT = 75

# Grace period for late arrivals (minutes)
ATTENDANCE_GRACE_PERIOD_MINUTES = 5

# QR token expiry time (minutes)
ATTENDANCE_QR_TOKEN_EXPIRY_MINUTES = 60

# Data retention period (days)
ATTENDANCE_DATA_RETENTION_DAYS = 2555  # 7 years
```

### **Configure via Admin**
1. Go to Admin → Attendance → Attendance Configurations
2. Add/edit configuration keys
3. Set values and data types
4. Enable/disable as needed

---

## 🌐 API Endpoints

### **Session Management**
```http
GET    /api/v1/attendance/sessions/           # List sessions
POST   /api/v1/attendance/sessions/           # Create session
GET    /api/v1/attendance/sessions/{id}/      # Get session details
PATCH  /api/v1/attendance/sessions/{id}/      # Update session
POST   /api/v1/attendance/sessions/{id}/open/ # Open session
POST   /api/v1/attendance/sessions/{id}/close/ # Close session
POST   /api/v1/attendance/sessions/{id}/generate-qr/ # Generate QR
```

### **Attendance Recording**
```http
GET    /api/v1/attendance/records/            # List records
POST   /api/v1/attendance/records/            # Mark attendance
POST   /api/v1/attendance/records/bulk-mark/  # Bulk marking
POST   /api/v1/attendance/records/qr-scan/    # QR code scan
```

### **Statistics & Reports**
```http
GET    /api/v1/attendance/statistics/student/{id}/    # Student stats
GET    /api/v1/attendance/statistics/course/{id}/     # Course stats
GET    /api/v1/attendance/reports/exam-eligibility/   # Exam eligibility
```

### **Leave Management**
```http
GET    /api/v1/attendance/leave-applications/         # List leaves
POST   /api/v1/attendance/leave-applications/         # Apply leave
PATCH  /api/v1/attendance/leave-applications/{id}/    # Approve/reject
```

---

## 📱 Attendance Capture Modes

### **1. QR Code Scanning**
```python
# Generate QR for session
POST /api/v1/attendance/sessions/{id}/generate-qr/

# Student scans QR
POST /api/v1/attendance/records/qr-scan/
{
  "qr_token": "abc123...",
  "student": "uuid",
  "device_id": "mobile123"
}
```

### **2. Biometric Attendance**
```python
# Register device
POST /api/v1/attendance/biometric-devices/
{
  "device_id": "device001",
  "device_name": "Fingerprint Scanner A101",
  "device_type": "fingerprint",
  "location": "Room A101",
  "ip_address": "192.168.1.100"
}

# Enroll student template
POST /api/v1/attendance/biometric-templates/
{
  "student": "uuid",
  "device": "uuid",
  "template_data": "encrypted_template"
}
```

### **3. Manual Entry**
```python
# Faculty marks attendance
POST /api/v1/attendance/records/
{
  "session": "uuid",
  "student": "uuid",
  "mark": "present",
  "source": "manual"
}
```

### **4. Bulk Marking**
```python
# Mark multiple students
POST /api/v1/attendance/records/bulk-mark/
{
  "session": "uuid",
  "records": [
    {"student": "uuid1", "mark": "present"},
    {"student": "uuid2", "mark": "absent"}
  ]
}
```

---

## 🔄 Business Logic Flow

### **Session Lifecycle**
```
1. Timetable Slot Created
   ↓
2. Session Generated (scheduled)
   ↓
3. Auto-Open (5 min before start)
   ↓
4. Attendance Marking (open)
   ↓
5. Auto-Close (after end time)
   ↓
6. Statistics Calculation
   ↓
7. Exam Eligibility Check
```

### **Attendance Calculation**
```python
# Formula
attendance_percentage = (present_count / effective_total) * 100

# Where:
# - present_count = present + late
# - effective_total = total_sessions - excused_absences
# - excused absences don't count against attendance
```

### **Exam Eligibility**
```python
# Rule
is_eligible = attendance_percentage >= threshold_percent

# Default threshold: 75%
# Configurable via admin interface
```

---

## 🛠️ Admin Operations

### **Bulk Actions**
1. **Open Sessions**: Select multiple sessions → Action: "Mark selected sessions as open"
2. **Close Sessions**: Select multiple sessions → Action: "Mark selected sessions as closed"
3. **Generate QR Codes**: Select multiple sessions → Action: "Generate QR codes for selected sessions"
4. **Calculate Statistics**: Select multiple students → Action: "Calculate statistics for selected students"

### **Key Admin Sections**
- **Sessions**: Manage attendance sessions
- **Records**: View attendance records
- **Statistics**: Monitor attendance statistics
- **Leave Applications**: Process leave requests
- **Correction Requests**: Handle correction requests
- **Biometric Devices**: Manage biometric devices
- **Configuration**: System settings
- **Audit Logs**: View audit trail

---

## 🔒 Security Features

### **Data Protection**
- **Encryption**: AES-256-GCM for sensitive data
- **Audit Trails**: Complete change tracking
- **Access Control**: Role-based permissions
- **Rate Limiting**: API protection
- **Data Retention**: Automatic cleanup

### **Compliance**
- **GDPR**: European data protection
- **Indian Data Protection Act**: Local compliance
- **Audit Logs**: Immutable change records
- **Data Minimization**: Only collect necessary data

---

## 📊 Monitoring & Statistics

### **Key Metrics**
- Total sessions count
- Open sessions count
- Today's sessions count
- Total attendance records
- Pending corrections
- Pending leave applications
- Device status monitoring

### **Real-time Dashboard**
Access via admin interface to monitor:
- System health
- Performance metrics
- Error rates
- User activity

---

## 🚨 Troubleshooting

### **Common Issues**

#### **Sessions Not Auto-Opening**
```bash
# Check Celery worker
celery -A campshub360 inspect active

# Restart worker
celery -A campshub360 worker -l info
```

#### **QR Codes Not Working**
```bash
# Regenerate QR codes
python manage.py shell -c "
from attendance.tasks import generate_qr_for_session
from attendance.models import AttendanceSession
for session in AttendanceSession.objects.filter(status='open'):
    generate_qr_for_session.delay(session.id)
"
```

#### **Statistics Not Updating**
```bash
# Manual calculation
python manage.py shell -c "
from attendance.tasks import calculate_attendance_statistics
calculate_attendance_statistics.delay()
"
```

### **Health Checks**
```bash
# System check
python manage.py check

# Test admin
python test_admin.py

# Test system
python simple_test.py
```

---

## 📞 Support

### **Quick Commands**
```bash
# Check system status
python manage.py check

# View migrations
python manage.py showmigrations attendance

# Create superuser
python manage.py createsuperuser

# Run tests
python simple_test.py
python test_admin.py
```

### **Logs & Debugging**
```bash
# Django logs
tail -f logs/django.log

# Celery logs
celery -A campshub360 events

# Database queries
python manage.py shell -c "
from django.db import connection
print(connection.queries[-5:])
"
```

---

## 📚 Documentation Links

- **Full README**: [attendance/README.md](README.md)
- **API Documentation**: [attendance/openapi.yml](openapi.yml)
- **Security Guide**: [attendance/security_guidance.md](security_guidance.md)
- **Load Tests**: [attendance/load_tests.py](load_tests.py)
- **Migration Summary**: [ATTENDANCE_MIGRATION_SUMMARY.md](../ATTENDANCE_MIGRATION_SUMMARY.md)

---

*Quick Reference Guide - Updated: September 2024*
