# Department Management System

A comprehensive Django application for managing university departments with scalable architecture and robust security features.

## Features

### Core Functionality
- **Department Management**: Complete CRUD operations for departments
- **Program Management**: Manage academic programs offered by departments
- **Resource Management**: Track department resources and facilities
- **Announcement System**: Department-specific announcements and notices
- **Event Management**: Schedule and manage department events
- **Document Management**: Store and manage department documents

### Security Features
- **Role-based Access Control**: Different permission levels for different user types
- **Data Validation**: Comprehensive validation for all input data
- **Audit Trail**: Track who created/updated records
- **Secure File Uploads**: Safe document and image upload handling

### Scalability Features
- **UUID Primary Keys**: Better performance and security
- **Database Indexing**: Optimized queries with proper indexes
- **Pagination**: Efficient handling of large datasets
- **Caching Support**: Built-in caching for frequently accessed data
- **API-First Design**: RESTful API for easy integration

## Models

### Department
The main model representing a university department with comprehensive information:
- Basic information (name, code, type)
- Leadership (head, deputy head)
- Contact and location details
- Academic information (establishment date, accreditation)
- Capacity management (faculty/student limits)
- Financial information (budget)
- Status tracking

### DepartmentProgram
Academic programs offered by departments:
- Program details (name, level, duration)
- Eligibility criteria and career prospects
- Accreditation status
- Status management

### DepartmentResource
Department resources and facilities:
- Resource types (laboratory, equipment, etc.)
- Location and status tracking
- Maintenance scheduling
- Cost tracking
- Responsible person assignment

### DepartmentAnnouncement
Department announcements and notices:
- Multiple announcement types
- Priority levels
- Publishing controls
- Target audience specification
- Expiry dates

### DepartmentEvent
Department events and activities:
- Event types (seminar, workshop, etc.)
- Scheduling and location
- Registration management
- Public/private visibility
- Organizer assignment

### DepartmentDocument
Department documents and files:
- Document types (policy, procedure, etc.)
- Version control
- Public/private access
- File management

## API Endpoints

### Department Management
- `GET /api/v1/departments/` - List all departments
- `POST /api/v1/departments/` - Create new department
- `GET /api/v1/departments/{id}/` - Get department details
- `PUT /api/v1/departments/{id}/` - Update department
- `DELETE /api/v1/departments/{id}/` - Delete department

### Department Programs
- `GET /api/v1/departments/{id}/programs/` - Get department programs
- `POST /api/v1/programs/` - Create new program
- `GET /api/v1/programs/{id}/` - Get program details

### Department Resources
- `GET /api/v1/departments/{id}/resources/` - Get department resources
- `POST /api/v1/resources/` - Create new resource
- `GET /api/v1/resources/{id}/` - Get resource details

### Department Announcements
- `GET /api/v1/departments/{id}/announcements/` - Get department announcements
- `POST /api/v1/announcements/` - Create new announcement
- `GET /api/v1/announcements/{id}/` - Get announcement details

### Department Events
- `GET /api/v1/departments/{id}/events/` - Get department events
- `POST /api/v1/events/` - Create new event
- `GET /api/v1/events/{id}/` - Get event details

### Department Documents
- `GET /api/v1/departments/{id}/documents/` - Get department documents
- `POST /api/v1/documents/` - Create new document
- `GET /api/v1/documents/{id}/` - Get document details

### Statistics and Search
- `GET /api/v1/departments/stats/` - Get department statistics
- `POST /api/v1/departments/search/` - Advanced search

## Permissions

### User Roles
- **Superuser/Staff**: Full access to all operations
- **Department Head**: Can manage their own department
- **Faculty**: Can view their department and sub-departments
- **Students**: Can view their own department
- **Regular Users**: Can view active departments only

### Permission Classes
- `IsDepartmentAdmin`: Department administrators
- `IsDepartmentHead`: Department heads
- `CanManageDepartment`: Department management
- `CanViewDepartment`: Department viewing
- `CanCreateDepartment`: Department creation

## Installation

1. Add `departments` to `INSTALLED_APPS` in settings.py
2. Run migrations: `python manage.py migrate`
3. Create superuser: `python manage.py createsuperuser`
4. Access admin interface at `/admin/`

## Usage

### Creating a Department
```python
from departments.models import Department

department = Department.objects.create(
    name="Computer Science",
    short_name="CS",
    code="CS001",
    department_type="ACADEMIC",
    email="cs@university.edu",
    phone="+1234567890",
    building="Engineering Building",
    address_line1="123 University Ave",
    city="University City",
    state="State",
    postal_code="12345",
    country="Country",
    established_date="2020-01-01",
    description="Department of Computer Science"
)
```

### API Usage
```python
import requests

# Get all departments
response = requests.get('http://localhost:8000/api/v1/departments/')
departments = response.json()

# Create new department
data = {
    "name": "Mathematics",
    "short_name": "MATH",
    "code": "MATH001",
    "department_type": "ACADEMIC",
    "email": "math@university.edu",
    "phone": "+1234567890",
    "building": "Science Building",
    "address_line1": "456 University Ave",
    "city": "University City",
    "state": "State",
    "postal_code": "12345",
    "country": "Country",
    "established_date": "2020-01-01",
    "description": "Department of Mathematics"
}
response = requests.post('http://localhost:8000/api/v1/departments/', json=data)
```

## Configuration

### Settings
The app uses Django's standard settings. Key configurations:
- `MEDIA_URL` and `MEDIA_ROOT` for file uploads
- `STATIC_URL` and `STATIC_ROOT` for static files
- Database configuration for optimal performance

### File Uploads
- Department logos: `department_logos/`
- Department documents: `department_documents/`
- All uploads are validated for security

## Security Considerations

1. **Input Validation**: All user inputs are validated
2. **File Upload Security**: File types and sizes are restricted
3. **Permission Checks**: All operations check user permissions
4. **SQL Injection Protection**: Django ORM provides protection
5. **XSS Protection**: Template escaping and input sanitization

## Performance Optimizations

1. **Database Indexing**: Strategic indexes on frequently queried fields
2. **Select Related**: Optimized queries with select_related
3. **Pagination**: Large datasets are paginated
4. **Caching**: Support for Redis caching
5. **Lazy Loading**: Related objects loaded on demand

## Monitoring and Logging

- All operations are logged
- Performance metrics can be tracked
- Error handling with proper HTTP status codes
- Audit trail for all changes

## Future Enhancements

1. **Real-time Notifications**: WebSocket support for announcements
2. **Advanced Analytics**: Department performance metrics
3. **Integration APIs**: Connect with external systems
4. **Mobile App Support**: Enhanced mobile API endpoints
5. **Workflow Management**: Approval workflows for department changes

## Contributing

1. Follow Django best practices
2. Write comprehensive tests
3. Update documentation
4. Ensure security compliance
5. Performance optimization

## License

This project is part of the CampsHub360 university management system.
