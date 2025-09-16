# Enhanced Placements Module

This module provides a comprehensive placement management system designed to meet university standards in India, particularly for Andhra Pradesh institutions. It includes features for NIRF compliance, UGC reporting, and advanced analytics.

## Features

### Core Placement Management
- **Company Management**: Track hiring companies with ratings, size, and performance metrics
- **Job Postings**: Manage job and internship opportunities
- **Placement Drives**: Organize campus placement drives with eligibility criteria
- **Applications**: Track student applications and their status
- **Interview Rounds**: Manage different rounds of selection process
- **Offers**: Track job offers and their acceptance status

### Enhanced Analytics & Reporting
- **Placement Statistics**: Comprehensive statistics for departments and programs
- **NIRF Compliance**: Generate reports meeting NIRF ranking requirements
- **Trend Analysis**: Track placement trends over multiple years
- **Company Performance**: Analyze company hiring patterns and success rates

### Alumni Network Management
- **Career Tracking**: Monitor alumni career progression
- **Mentorship Network**: Connect alumni willing to mentor current students
- **Recruitment Network**: Leverage alumni for job opportunities
- **Entrepreneurship Tracking**: Track alumni startups and ventures

### Compliance & Documentation
- **Document Management**: Store placement agreements, MOUs, and certificates
- **Company Feedback**: Collect and analyze feedback from recruiters
- **Audit Trails**: Maintain records for compliance and verification

## API Endpoints

### Companies
- `GET /api/companies/` - List all companies
- `POST /api/companies/` - Create new company
- `GET /api/companies/{id}/statistics/` - Get company performance statistics

### Job Postings
- `GET /api/jobs/` - List all job postings
- `POST /api/jobs/` - Create new job posting
- `GET /api/jobs/{id}/applications/` - Get applications for a job

### Placement Drives
- `GET /api/drives/` - List all placement drives
- `POST /api/drives/` - Create new placement drive

### Applications
- `GET /api/applications/` - List all applications
- `POST /api/applications/` - Submit new application

### Statistics & Analytics
- `GET /api/statistics/` - List placement statistics
- `GET /api/statistics/overview/` - Get overall placement overview
- `GET /api/analytics/trends/` - Get placement trends over years
- `GET /api/analytics/nirf-report/` - Generate NIRF compliance report

### Alumni Network
- `GET /api/alumni/` - List alumni placements
- `GET /api/alumni/alumni-network/` - Get alumni network statistics

### Company Feedback
- `GET /api/feedbacks/` - List company feedback
- `POST /api/feedbacks/` - Submit company feedback

### Documents
- `GET /api/documents/` - List placement documents
- `POST /api/documents/` - Upload placement document

## Models

### Core Models
- **Company**: Enhanced with ratings, size, and performance metrics
- **JobPosting**: Job and internship opportunities
- **Application**: Student applications with status tracking
- **PlacementDrive**: Campus placement drives
- **InterviewRound**: Interview process management
- **Offer**: Job offers with acceptance tracking

### Analytics Models
- **PlacementStatistics**: Department and program-wise statistics
- **CompanyFeedback**: Recruiter feedback and ratings
- **PlacementDocument**: Document management for compliance
- **AlumniPlacement**: Alumni career tracking and networking

## NIRF Compliance Features

### Key Metrics Tracked
1. **Placement Percentage**: Percentage of students placed
2. **Higher Studies**: Students pursuing higher education
3. **Entrepreneurship**: Students starting their own ventures
4. **Salary Statistics**: Average, highest, and lowest salaries
5. **Company Diversity**: Number and types of recruiting companies

### Reporting Capabilities
- Generate NIRF-compliant placement reports
- Track trends over multiple academic years
- Department and program-wise breakdowns
- Export data for ranking submissions

## Management Commands

### Generate Placement Statistics
```bash
python manage.py generate_placement_stats --academic-year 2024-2025
```

Options:
- `--academic-year`: Specify academic year (default: current year)
- `--department`: Generate for specific department
- `--force`: Force regeneration of existing statistics

## Installation & Setup

1. **Install Dependencies**: Ensure all required packages are installed
2. **Run Migrations**: Create database tables
   ```bash
   python manage.py makemigrations placements
   python manage.py migrate
   ```
3. **Generate Initial Statistics**: Create baseline statistics
   ```bash
   python manage.py generate_placement_stats
   ```

## Best Practices

### For Placement Officers
1. **Regular Data Entry**: Keep placement data updated regularly
2. **Company Feedback**: Collect feedback after each drive
3. **Document Management**: Maintain all placement-related documents
4. **Alumni Engagement**: Regularly update alumni information

### For Administrators
1. **Monthly Reports**: Generate monthly placement reports
2. **NIRF Preparation**: Use analytics for NIRF ranking submissions
3. **Trend Analysis**: Monitor placement trends for strategic planning
4. **Compliance**: Ensure all documentation meets regulatory requirements

## Integration with Other Modules

- **Students Module**: Links with student enrollment and academic records
- **Departments Module**: Department-wise placement tracking
- **Academics Module**: Program-specific placement statistics
- **Accounts Module**: User authentication and permissions

## Security & Permissions

- All endpoints require authentication
- Role-based access control for different user types
- Secure file upload for documents
- Audit trails for all placement activities

## Future Enhancements

1. **AI-Powered Matching**: Intelligent job-student matching
2. **Mobile App**: Mobile interface for students and recruiters
3. **Integration APIs**: Connect with external job portals
4. **Advanced Analytics**: Machine learning for placement predictions
5. **Video Interviews**: Built-in video interview scheduling

## Support & Maintenance

- Regular database backups recommended
- Monitor placement statistics accuracy
- Update company information regularly
- Maintain alumni network database

## Compliance Notes

This module is designed to meet:
- UGC guidelines for placement reporting
- NIRF ranking requirements
- Andhra Pradesh university standards
- Industry best practices for placement management

For technical support or feature requests, contact the development team.
