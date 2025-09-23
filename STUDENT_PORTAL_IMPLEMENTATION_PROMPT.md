# Student Portal Implementation Prompt

## Overview
Create a comprehensive student portal for an Indian AP (Andhra Pradesh) university with role-based authentication, student profile management, and representative functionality (CR/LR). The system should handle 20K+ students with excellent performance.

## Core Requirements

### 1. Student Authentication System

#### Login Endpoint
- **URL**: `POST /api/student-portal/auth/login/`
- **Purpose**: Authenticate students using roll number or email
- **Authentication**: None (public endpoint)

#### Request Format
```json
{
    "username": "22CS001",  // Roll number (optional)
    "email": "student@university.edu",  // Email (optional)
    "password": "student_password"
}
```

#### Response Format
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "uuid-string",
        "email": "student@university.edu",
        "username": "22CS001",
        "is_active": true,
        "is_verified": true
    },
    "student_profile": {
        "id": "uuid-string",
        "roll_number": "22CS001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "student@university.edu",
        "date_of_birth": "2000-01-15",
        "gender": "M",
        "student_batch": {
            "id": "uuid-string",
            "batch_code": "CS-2024-3-A",
            "department": "Computer Science",
            "academic_program": "B.Tech Computer Science",
            "year_of_study": "3",
            "section": "A",
            "semester": "5"
        },
        "academic_year": "2024-2025",
        "is_active": true
    },
    "representative_role": {
        "id": "uuid-string",
        "representative_type": "CR",
        "scope_description": "3rd Year Section A - 5 Sem",
        "is_active": true,
        "responsibilities": "Represent class in academic matters",
        "contact_email": "cr@university.edu",
        "contact_phone": "+91-9876543210"
    },
    "roles": ["Student"],
    "permissions": ["students.view_student", "students.change_student"]
}
```

#### Authentication Logic
1. **User Lookup**: Support both roll number and email login
2. **Password Validation**: Verify user password
3. **Role Verification**: Ensure user has 'Student' role
4. **JWT Token Generation**: Create access and refresh tokens
5. **Session Recording**: Log successful login attempts
6. **Profile Retrieval**: Get complete student profile with academic context
7. **Representative Check**: Include representative role if applicable

### 2. Student Profile Management

#### Profile Retrieval Endpoint
- **URL**: `GET /api/student-portal/profile/`
- **Purpose**: Get current student's profile information
- **Authentication**: JWT Token required

#### Profile Update Endpoint
- **URL**: `PUT/PATCH /api/student-portal/profile/`
- **Purpose**: Update student profile information
- **Authentication**: JWT Token required

#### Request Format (Update)
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "student_mobile": "+91-9876543210",
    "student_alternate_mobile": "+91-9876543211",
    "address": {
        "address_line_1": "123 Main Street",
        "address_line_2": "Apt 4B",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500001",
        "country": "India"
    },
    "emergency_contact": {
        "name": "Jane Doe",
        "relationship": "Mother",
        "phone": "+91-9876543212"
    }
}
```

### 3. Student Dashboard

#### Dashboard Endpoint
- **URL**: `GET /api/student-portal/dashboard/`
- **Purpose**: Get student dashboard data
- **Authentication**: JWT Token required

#### Response Format
```json
{
    "student_info": {
        "name": "John Doe",
        "roll_number": "22CS001",
        "batch": "CS-2024-3-A",
        "department": "Computer Science",
        "year": "3rd Year",
        "section": "A",
        "semester": "5"
    },
    "academic_info": {
        "academic_year": "2024-2025",
        "program": "B.Tech Computer Science",
        "status": "Active",
        "enrollment_date": "2022-07-01"
    },
    "representative_status": {
        "is_representative": true,
        "role": "CR",
        "scope": "3rd Year Section A",
        "active_since": "2024-07-01"
    },
    "recent_activities": [
        {
            "id": "uuid-string",
            "type": "FEEDBACK",
            "title": "Library Issue Resolved",
            "date": "2024-09-15T10:30:00Z",
            "status": "COMPLETED"
        }
    ],
    "pending_feedback": 2,
    "upcoming_events": [
        {
            "id": "uuid-string",
            "title": "Class Meeting",
            "date": "2024-09-20T14:00:00Z",
            "location": "Room 101"
        }
    ]
}
```

### 4. Representative Dashboard (CR/LR)

#### Representative Dashboard Endpoint
- **URL**: `GET /api/student-portal/representative/dashboard/`
- **Purpose**: Get representative-specific dashboard data
- **Authentication**: JWT Token + Representative role required

#### Response Format
```json
{
    "representative_info": {
        "role": "CR",
        "scope": "3rd Year Section A - 5 Sem",
        "active_since": "2024-07-01",
        "contact_info": {
            "email": "cr@university.edu",
            "phone": "+91-9876543210"
        }
    },
    "represented_students": {
        "total_count": 65,
        "active_count": 63,
        "recent_additions": 2
    },
    "pending_tasks": [
        {
            "id": "uuid-string",
            "type": "FEEDBACK",
            "title": "Hostel Complaint",
            "priority": "HIGH",
            "submitted_by": "22CS015",
            "date": "2024-09-15T09:00:00Z"
        }
    ],
    "recent_activities": [
        {
            "id": "uuid-string",
            "type": "MEETING",
            "title": "Class Representative Meeting",
            "date": "2024-09-14T15:00:00Z",
            "participants": 65,
            "outcome": "Discussed upcoming exams"
        }
    ],
    "statistics": {
        "feedback_handled": 15,
        "meetings_conducted": 8,
        "events_organized": 3,
        "students_helped": 45
    }
}
```

## Technical Implementation Details

### 1. Database Models

#### Student Model Extensions
```python
class Student(TimeStampedUUIDModel):
    # Existing fields...
    roll_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    student_batch = models.ForeignKey(StudentBatch, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
```

#### Student Representative Model
```python
class StudentRepresentative(TimeStampedUUIDModel):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='representative_role')
    representative_type = models.CharField(max_length=20, choices=StudentRepresentativeType.choices)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    semester = models.CharField(max_length=10)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    academic_program = models.ForeignKey(AcademicProgram, on_delete=models.CASCADE)
    year_of_study = models.CharField(max_length=1, choices=YEAR_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    is_active = models.BooleanField(default=True)
    responsibilities = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)
```

### 2. Authentication Logic

#### User Lookup Strategy
```python
def _get_user_by_identifier(self, identifier: str):
    """Get user by roll number or email"""
    # 1. Try email match first
    try:
        return User.objects.get(email__iexact=identifier)
    except User.DoesNotExist:
        pass
    
    # 2. Try roll number via AuthIdentifier
    auth_ids = AuthIdentifier.objects.filter(
        Q(identifier__iexact=identifier),
        Q(id_type=IdentifierType.USERNAME) | Q(id_type=IdentifierType.EMAIL)
    ).select_related('user')
    if auth_ids.exists():
        return auth_ids.first().user
    
    # 3. Fallback to username field
    try:
        return User.objects.get(username__iexact=identifier)
    except User.DoesNotExist:
        return None
```

#### Role Verification
```python
def _user_is_student(self, user):
    """Check if user has Student role"""
    return user.groups.filter(name='Student').exists()
```

### 3. Permission System

#### Custom Permission Classes
```python
class IsStudent(BasePermission):
    """Permission class to ensure user has Student role"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Student').exists()

class IsClassRepresentative(BasePermission):
    """Permission class for Class Representatives"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.student_profile.representative_role.representative_type == 'CR'
        except:
            return False
```

### 4. API Endpoints Structure

#### URL Configuration
```python
urlpatterns = [
    # Authentication
    path('auth/login/', StudentPortalLoginView.as_view(), name='login'),
    
    # Dashboard endpoints
    path('dashboard/', StudentPortalDashboardView.as_view(), name='dashboard'),
    path('representative/dashboard/', StudentRepresentativeDashboardView.as_view(), name='representative-dashboard'),
    
    # Profile management
    path('profile/', StudentPortalProfileView.as_view(), name='profile'),
    
    # Representative functionality
    path('representatives/', StudentRepresentativeViewSet.as_view(), name='representatives'),
    path('representative-activities/', StudentRepresentativeActivityViewSet.as_view(), name='representative-activities'),
    
    # Feedback system
    path('feedback/', StudentFeedbackViewSet.as_view(), name='feedback'),
]
```

### 5. Serializers

#### Login Serializer
```python
class StudentPortalLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, help_text="Roll number or email")
    email = serializers.EmailField(required=False, help_text="Email address")
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not (username or email):
            raise serializers.ValidationError("Either username or email is required")
        
        user = self._get_user_by_identifier(username or email)
        
        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials")
        
        if not self._user_is_student(user):
            raise serializers.ValidationError("Access denied. Student role required.")
        
        attrs['user'] = user
        return attrs
```

#### Profile Serializer
```python
class StudentPortalProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    student_batch_info = serializers.SerializerMethodField()
    academic_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'roll_number', 'first_name', 'last_name', 'full_name',
            'email', 'date_of_birth', 'gender', 'student_mobile',
            'student_alternate_mobile', 'student_batch', 'student_batch_info',
            'academic_info', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'roll_number', 'created_at', 'updated_at']
    
    def get_student_batch_info(self, obj):
        if obj.student_batch:
            return {
                'batch_code': obj.student_batch.batch_code,
                'department': obj.student_batch.department.name,
                'academic_program': obj.student_batch.academic_program.name,
                'year_of_study': obj.student_batch.get_year_of_study_display(),
                'section': obj.student_batch.get_section_display(),
                'semester': obj.student_batch.semester
            }
        return None
```

### 6. Performance Optimizations

#### Database Indexes
```python
class Student(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['roll_number']),
            models.Index(fields=['email']),
            models.Index(fields=['student_batch', 'is_active']),
        ]

class StudentRepresentative(models.Model):
    # ... fields ...
    
    class Meta:
        indexes = [
            models.Index(fields=['representative_type', 'is_active']),
            models.Index(fields=['academic_year', 'semester']),
            models.Index(fields=['department', 'academic_program']),
            models.Index(fields=['year_of_study', 'section']),
        ]
```

#### Query Optimization
```python
# Use select_related for foreign keys
students = Student.objects.select_related(
    'user', 'student_batch', 'student_batch__department', 
    'student_batch__academic_program'
).filter(is_active=True)

# Use prefetch_related for reverse foreign keys
representatives = StudentRepresentative.objects.prefetch_related(
    'activities', 'handled_feedback'
).filter(is_active=True)
```

### 7. Error Handling

#### Standard Error Responses
```json
// Authentication Error
{
    "non_field_errors": ["Invalid credentials"]
}

// Permission Error
{
    "detail": "You do not have permission to perform this action."
}

// Validation Error
{
    "field_name": ["This field is required."]
}

// Not Found Error
{
    "detail": "Not found."
}
```

### 8. Security Considerations

#### JWT Token Configuration
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

#### Rate Limiting
```python
# Implement rate limiting for login endpoint
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    # Login logic
```

### 9. Testing Requirements

#### Unit Tests
- Authentication with valid/invalid credentials
- Role-based access control
- Profile retrieval and updates
- Representative functionality
- Error handling scenarios

#### Performance Tests
- Login endpoint performance (target: <500ms)
- Profile retrieval performance (target: <200ms)
- Dashboard loading performance (target: <1s)
- Concurrent user handling (target: 100+ users)

#### Integration Tests
- End-to-end login flow
- Profile update workflow
- Representative dashboard functionality
- Feedback submission and handling

### 10. Deployment Considerations

#### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://localhost:6379/0
```

#### Production Settings
- Use PostgreSQL for database
- Implement Redis for caching
- Configure proper logging
- Set up monitoring and alerting
- Implement backup strategies

## Success Criteria

1. **Authentication**: Students can login with roll number or email
2. **Profile Management**: Students can view and update their profiles
3. **Dashboard**: Personalized dashboard with relevant information
4. **Representative Features**: CR/LR can access representative-specific features
5. **Performance**: System handles 20K+ users efficiently
6. **Security**: Proper authentication and authorization
7. **Scalability**: Optimized for high user load
8. **User Experience**: Intuitive and responsive interface

## Implementation Timeline

1. **Week 1**: Database models and authentication system
2. **Week 2**: API endpoints and serializers
3. **Week 3**: Permission system and representative functionality
4. **Week 4**: Testing, optimization, and deployment

This implementation provides a robust, scalable student portal specifically designed for Indian AP universities with comprehensive CR/LR functionality and excellent performance characteristics.
