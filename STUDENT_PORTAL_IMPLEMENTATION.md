# Student Portal Backend Implementation for AP Universities

## Overview

This implementation provides a comprehensive backend for a student portal specifically designed for Andhra Pradesh (AP) universities, featuring role-based authentication with Class Representatives (CR) and Ladies Representatives (LR) functionality.

## Features

### 🔐 Authentication & Authorization
- **Student Login**: Login using roll number or email
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Student, CR, LR, and other representative roles
- **Session Management**: Track login sessions with geolocation

### 👥 Student Representatives System
- **Class Representative (CR)**: Academic representation and coordination
- **Ladies Representative (LR)**: Gender-specific issues and activities
- **Sports Representative**: Sports and physical activities
- **Cultural Representative**: Cultural events and activities
- **Academic Representative**: Academic matters and curriculum
- **Hostel Representative**: Hostel and accommodation issues
- **Library Representative**: Library services and resources
- **Placement Representative**: Career and placement activities

### 📊 Student Portal Features
- **Dashboard**: Comprehensive student dashboard with academic summary
- **Profile Management**: Update personal and contact information
- **Feedback System**: Submit and track feedback/complaints
- **Representative Activities**: Track representative activities and achievements
- **Statistics**: Detailed statistics and analytics
- **Announcements**: University and class-specific announcements
- **Events**: Academic and cultural events

## API Endpoints

### Authentication
```
POST /api/student-portal/auth/login/
```
**Request:**
```json
{
  "username": "22CS001",  // roll number or email
  "password": "Campus@360"
}
```

**Response:**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid",
    "email": "student@example.com",
    "username": "22CS001",
    "is_active": true,
    "is_verified": false
  },
  "student_profile": {
    "id": "uuid",
    "roll_number": "22CS001",
    "full_name": "John Doe",
    "academic_info": {
      "department": {
        "name": "Computer Science",
        "code": "CS"
      },
      "academic_program": {
        "name": "B.Tech Computer Science",
        "code": "BTECH-CS"
      },
      "academic_year": "2024-2025",
      "year_of_study": "3",
      "semester": "5",
      "section": "A"
    },
    "contact_info": {
      "address_line1": "123 Main St",
      "city": "Hyderabad",
      "state": "Telangana"
    }
  },
  "representative_role": {
    "representative_type": "CR",
    "scope_description": "Dept: Computer Science | Year: 3 | Section: A",
    "is_active": true
  },
  "roles": ["Student"],
  "permissions": ["students.view", "academics.view"]
}
```

### Dashboard
```
GET /api/student-portal/dashboard/
```
**Response:**
```json
{
  "student": { /* student profile data */ },
  "academic_summary": {
    "current_semester": "5",
    "year_of_study": "3",
    "department": "Computer Science",
    "section": "A"
  },
  "stats": {
    "total_assignments": 15,
    "pending_assignments": 3,
    "attendance_percentage": 85.5,
    "upcoming_exams": 2,
    "feedback_submitted": 5,
    "feedback_resolved": 3
  },
  "recent_activities": [],
  "announcements": [],
  "upcoming_events": [],
  "feedback_summary": {
    "total_submitted": 5,
    "pending": 1,
    "in_progress": 1,
    "resolved": 3,
    "overdue": 0
  }
}
```

### Representative Dashboard
```
GET /api/student-portal/representative/dashboard/
```
**Response:**
```json
{
  "representative": { /* representative data */ },
  "represented_students_count": 45,
  "recent_activities": [],
  "pending_feedback": [],
  "feedback_stats": {
    "total_handled": 12,
    "pending": 2,
    "in_progress": 3,
    "resolved": 7,
    "overdue": 1
  },
  "upcoming_events": [],
  "announcements": []
}
```

### Profile Management
```
GET /api/student-portal/profile/
PATCH /api/student-portal/profile/
```

### Feedback System
```
GET /api/student-portal/feedback/
POST /api/student-portal/feedback/
GET /api/student-portal/feedback/{id}/
PATCH /api/student-portal/feedback/{id}/
POST /api/student-portal/feedback/{id}/assign_representative/
POST /api/student-portal/feedback/{id}/update_status/
```

### Representative Activities
```
GET /api/student-portal/representative-activities/
POST /api/student-portal/representative-activities/
GET /api/student-portal/representative-activities/{id}/
PATCH /api/student-portal/representative-activities/{id}/
POST /api/student-portal/representative-activities/{id}/submit_for_review/
```

### Representatives
```
GET /api/student-portal/representatives/
GET /api/student-portal/representatives/my_representatives/
GET /api/student-portal/representatives/{id}/represented_students/
```

### Statistics
```
GET /api/student-portal/stats/
```

## Models

### StudentRepresentative
- **student**: One-to-one relationship with Student
- **representative_type**: CR, LR, SPORTS, CULTURAL, etc.
- **academic_year**: Academic year for representation
- **semester**: Semester for representation
- **department**: Department being represented
- **academic_program**: Academic program being represented
- **year_of_study**: Year of study being represented
- **section**: Section being represented
- **is_active**: Whether representation is currently active
- **start_date/end_date**: Representation period
- **responsibilities**: List of responsibilities
- **achievements**: Notable achievements
- **contact_email/contact_phone**: Contact information
- **nominated_by/approved_by**: Nomination and approval tracking

### StudentRepresentativeActivity
- **representative**: Representative who performed the activity
- **activity_type**: ANNOUNCEMENT, MEETING, EVENT, etc.
- **title**: Activity title
- **description**: Detailed description
- **activity_date**: When activity was performed
- **location**: Where activity took place
- **participants_count**: Number of participants
- **target_audience**: Description of target audience
- **outcomes**: Results and outcomes
- **feedback_received**: Feedback from participants
- **follow_up_required**: Whether follow-up is needed
- **status**: DRAFT, SUBMITTED, APPROVED, REJECTED

### StudentFeedback
- **student**: Student who submitted feedback
- **representative**: Representative handling the feedback
- **feedback_type**: ACADEMIC, INFRASTRUCTURE, HOSTEL, etc.
- **title**: Feedback title
- **description**: Detailed description
- **priority**: LOW, MEDIUM, HIGH, URGENT
- **status**: SUBMITTED, UNDER_REVIEW, IN_PROGRESS, RESOLVED, CLOSED, REJECTED
- **resolution_notes**: Notes about resolution
- **resolved_by**: User who resolved the feedback
- **resolved_date**: When feedback was resolved
- **follow_up_required**: Whether follow-up is needed
- **is_anonymous**: Whether feedback is anonymous

## Permissions

### IsStudent
- Ensures user has Student role
- Allows access to student portal features

### IsClassRepresentative
- Ensures user is a current Class Representative
- Allows CR-specific functionality

### IsLadiesRepresentative
- Ensures user is a current Ladies Representative
- Allows LR-specific functionality

### IsStudentRepresentative
- Ensures user is any type of current representative
- Allows representative functionality

### IsRepresentativeOrReadOnly
- Representatives can write, others can only read
- Used for shared resources

### CanAccessRepresentedStudents
- Representatives can access students they represent
- Students can only access their own data

### CanHandleFeedback
- Students can submit feedback
- Representatives can handle feedback

### IsAPUniversityStudent
- AP University specific checks
- Additional validation for AP students

## Setup Instructions

### 1. Database Migration
```bash
python manage.py makemigrations students
python manage.py migrate
```

### 2. Create Sample Representatives
```bash
python manage.py create_sample_representatives --academic-year 2024-2025 --semester 5 --department-code CS
```

### 3. Create Student Group
```bash
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.get_or_create(name='Student')
```

### 4. Test the Implementation
```bash
python manage.py test students.tests.test_student_portal
```

## Usage Examples

### Student Login
```python
import requests

# Login as student
response = requests.post('http://localhost:8000/api/student-portal/auth/login/', {
    'username': '22CS001',
    'password': 'Campus@360'
})

access_token = response.json()['access']
headers = {'Authorization': f'Bearer {access_token}'}

# Get dashboard
dashboard = requests.get('http://localhost:8000/api/student-portal/dashboard/', headers=headers)
print(dashboard.json())
```

### Submit Feedback
```python
# Submit feedback
feedback_data = {
    'feedback_type': 'ACADEMIC',
    'title': 'Library Issue',
    'description': 'Library computers are not working properly',
    'priority': 'MEDIUM'
}

response = requests.post(
    'http://localhost:8000/api/student-portal/feedback/',
    json=feedback_data,
    headers=headers
)
```

### Representative Activity
```python
# Submit representative activity
activity_data = {
    'activity_type': 'MEETING',
    'title': 'Class Meeting',
    'description': 'Monthly class meeting to discuss academic issues',
    'activity_date': '2024-01-15T10:00:00Z',
    'location': 'Classroom A-101',
    'participants_count': 45,
    'target_audience': 'All students of CS 3rd year Section A'
}

response = requests.post(
    'http://localhost:8000/api/student-portal/representative-activities/',
    json=activity_data,
    headers=headers
)
```

## Security Features

1. **JWT Authentication**: Secure token-based authentication
2. **Role-Based Access Control**: Granular permissions based on user roles
3. **Input Validation**: Comprehensive validation of all inputs
4. **Rate Limiting**: Built-in rate limiting for authentication endpoints
5. **Session Tracking**: Track user sessions with geolocation
6. **Data Isolation**: Users can only access their own data
7. **Representative Scope**: Representatives can only access their scope

## Integration Points

The student portal integrates with other apps in the system:

- **Assignments App**: Assignment statistics and data
- **Attendance App**: Attendance percentage and records
- **Exams App**: Upcoming exams and results
- **Academics App**: Course and program information
- **Departments App**: Department information
- **Events App**: University events and activities
- **Announcements App**: University announcements

## Testing

Comprehensive test suite covering:

- Authentication and authorization
- Dashboard functionality
- Representative system
- Feedback system
- Profile management
- Statistics and analytics
- Permission system
- API endpoints

Run tests:
```bash
python manage.py test students.tests.test_student_portal
```

## Future Enhancements

1. **Mobile App Integration**: API ready for mobile app development
2. **Real-time Notifications**: WebSocket integration for real-time updates
3. **File Upload**: Support for document and image uploads
4. **Advanced Analytics**: More detailed statistics and reports
5. **Multi-language Support**: Support for regional languages
6. **Integration with External Systems**: ERP, LMS, and other university systems

## Support

For issues or questions regarding the student portal implementation, please refer to the test files and API documentation. The implementation follows Django and DRF best practices and is designed to be scalable and maintainable.
