# Assignments App

This Django app provides a comprehensive assignment management system for educational institutions, allowing faculty to create and manage assignments while students can submit their work.

## Features

### For Faculty
- Create, edit, and manage assignments
- Set due dates, maximum marks, and instructions
- Support for both individual and group assignments
- File attachment support for assignment materials
- Grade student submissions with feedback
- View assignment statistics and analytics
- Create assignment templates for reuse
- Comment on assignments for clarifications

### For Students
- View assigned assignments
- Submit assignments with file attachments
- Track submission status and grades
- View feedback from faculty
- Comment on assignments for questions

### For HOD (Head of Department)
- Oversight of all assignments in their department
- View department-wide assignment statistics
- Monitor faculty assignment activity

## Models

### Core Models

1. **AssignmentCategory**: Categories for organizing assignments
2. **Assignment**: Main assignment model with all assignment details
3. **AssignmentSubmission**: Student submissions for assignments
4. **AssignmentGrade**: Grading information for submissions
5. **AssignmentFile**: File attachments for assignments and submissions
6. **AssignmentComment**: Comments and discussions on assignments
7. **AssignmentGroup**: Group management for group assignments
8. **AssignmentTemplate**: Reusable assignment templates

### Key Features

- **File Support**: Both assignments and submissions support file attachments
- **Group Assignments**: Support for group work with configurable group sizes
- **Late Submission Tracking**: Automatic detection and marking of late submissions
- **Grading System**: Comprehensive grading with letter grades and feedback
- **Status Management**: Draft, Published, Closed, and Cancelled states
- **Permission System**: Role-based access control for different user types

## API Endpoints

### Assignment Categories
- `GET /api/v1/assignments/categories/` - List categories
- `POST /api/v1/assignments/categories/` - Create category (Admin only)
- `GET /api/v1/assignments/categories/{id}/` - Get category details
- `PUT/PATCH /api/v1/assignments/categories/{id}/` - Update category (Admin only)
- `DELETE /api/v1/assignments/categories/{id}/` - Delete category (Admin only)

### Assignments
- `GET /api/v1/assignments/` - List assignments (filtered by user role)
- `POST /api/v1/assignments/` - Create assignment (Faculty only)
- `GET /api/v1/assignments/{id}/` - Get assignment details
- `PUT/PATCH /api/v1/assignments/{id}/` - Update assignment (Owner only)
- `DELETE /api/v1/assignments/{id}/` - Delete assignment (Owner only)
- `GET /api/v1/assignments/my-assignments/` - Get user's assignments
- `POST /api/v1/assignments/{id}/publish/` - Publish assignment (Faculty only)
- `POST /api/v1/assignments/{id}/close/` - Close assignment (Faculty only)

### Submissions
- `GET /api/v1/assignments/{id}/submit/` - List submissions for assignment
- `POST /api/v1/assignments/{id}/submit/` - Submit assignment (Student only)
- `GET /api/v1/assignments/submissions/{id}/` - Get submission details
- `PUT/PATCH /api/v1/assignments/submissions/{id}/` - Update submission (Owner only)
- `DELETE /api/v1/assignments/submissions/{id}/` - Delete submission (Owner only)

### Grading
- `POST /api/v1/assignments/submissions/{id}/grade/` - Grade submission (Faculty only)
- `PUT/PATCH /api/v1/assignments/submissions/{id}/grade/` - Update grade (Faculty only)

### Comments
- `GET /api/v1/assignments/{id}/comments/` - List assignment comments
- `POST /api/v1/assignments/{id}/comments/` - Add comment

### Files
- `POST /api/v1/assignments/files/upload/` - Upload assignment files

### Statistics
- `GET /api/v1/assignments/stats/` - Get assignment statistics (role-based)

### Templates
- `GET /api/v1/assignments/templates/` - List assignment templates
- `POST /api/v1/assignments/templates/` - Create template (Faculty only)
- `GET /api/v1/assignments/templates/{id}/` - Get template details
- `PUT/PATCH /api/v1/assignments/templates/{id}/` - Update template (Owner only)
- `DELETE /api/v1/assignments/templates/{id}/` - Delete template (Owner only)

## Permissions

The app implements role-based permissions:

- **Faculty**: Can create, edit, and manage their own assignments
- **Students**: Can view assigned assignments and submit work
- **HOD**: Can oversee all assignments in their department
- **Admin**: Full access to all functionality

## File Management

- Support for multiple file types (PDF, DOC, images, etc.)
- File size validation
- Organized file storage with proper directory structure
- File metadata tracking (size, type, upload date)

## Usage Examples

### Creating an Assignment (Faculty)
```python
POST /api/v1/assignments/
{
    "title": "Programming Assignment 1",
    "description": "Implement a sorting algorithm",
    "instructions": "Submit your code with comments",
    "max_marks": 100,
    "due_date": "2024-02-15T23:59:59Z",
    "category": "category-uuid",
    "assigned_to_grades": ["grade-uuid-1", "grade-uuid-2"]
}
```

### Submitting an Assignment (Student)
```python
POST /api/v1/assignments/{assignment-id}/submit/
{
    "content": "Here is my implementation...",
    "notes": "I had some issues with the algorithm",
    "attachment_files": [
        {
            "file_name": "sorting.py",
            "file_path": "path/to/file"
        }
    ]
}
```

### Grading a Submission (Faculty)
```python
POST /api/v1/assignments/submissions/{submission-id}/grade/
{
    "marks_obtained": 85,
    "grade_letter": "B+",
    "feedback": "Good implementation, but could be more efficient"
}
```

## Database Indexes

The app includes optimized database indexes for:
- Assignment queries by faculty and status
- Submission queries by assignment and student
- File queries by assignment and type
- Date-based queries for due dates and submission dates

## Integration

The assignments app integrates with:
- **Accounts app**: User authentication and roles
- **Faculty app**: Faculty information and department management
- **Students app**: Student information and grade management
- **Academics app**: Grade and department references

## Future Enhancements

Potential future features:
- Plagiarism detection integration
- Peer review assignments
- Assignment scheduling and automation
- Advanced analytics and reporting
- Mobile app support
- Real-time notifications
- Assignment collaboration tools
