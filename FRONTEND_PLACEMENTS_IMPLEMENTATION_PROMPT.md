# Frontend Implementation Prompt: Enhanced Placements Module

## 🎯 **Objective**
Create a comprehensive frontend implementation for the enhanced placements module that meets university standards in India, particularly for Andhra Pradesh institutions. The frontend should include all new features, API endpoints, and provide a modern, user-friendly interface for placement management.

## 📋 **Requirements Overview**

### **Core Features to Implement:**
1. **Enhanced Company Management** with ratings and metrics
2. **Placement Statistics Dashboard** for NIRF compliance
3. **Company Feedback System** for continuous improvement
4. **Document Management** for compliance tracking
5. **Alumni Network Management** for mentorship and recruitment
6. **Advanced Analytics & Reporting** for decision-making
7. **Placement Drive Management** with enhanced features
8. **Job Posting Management** with improved functionality
9. **Application Tracking** with status management
10. **Offer Management** with acceptance tracking

## 🔗 **API Endpoints to Implement**

### **Base URL:** `/api/v1/placements/api/`

### **1. Company Management**
```javascript
// Standard CRUD operations
GET    /companies/                    // List all companies
POST   /companies/                    // Create new company
GET    /companies/{id}/               // Get company details
PUT    /companies/{id}/               // Update company
DELETE /companies/{id}/               // Delete company

// Custom actions
GET    /companies/{id}/statistics/    // Get company performance statistics
```

### **2. Job Posting Management**
```javascript
GET    /jobs/                        // List all job postings
POST   /jobs/                        // Create new job posting
GET    /jobs/{id}/                   // Get job details
PUT    /jobs/{id}/                   // Update job posting
DELETE /jobs/{id}/                   // Delete job posting

// Custom actions
GET    /jobs/{id}/applications/      // Get applications for a job
```

### **3. Application Management**
```javascript
GET    /applications/                // List all applications
POST   /applications/                // Create new application
GET    /applications/{id}/           // Get application details
PUT    /applications/{id}/           // Update application
DELETE /applications/{id}/           // Delete application
```

### **4. Placement Drive Management**
```javascript
GET    /drives/                      // List all placement drives
POST   /drives/                      // Create new placement drive
GET    /drives/{id}/                 // Get drive details
PUT    /drives/{id}/                 // Update drive
DELETE /drives/{id}/                 // Delete drive
```

### **5. Interview Round Management**
```javascript
GET    /rounds/                      // List all interview rounds
POST   /rounds/                      // Create new round
GET    /rounds/{id}/                 // Get round details
PUT    /rounds/{id}/                 // Update round
DELETE /rounds/{id}/                 // Delete round
```

### **6. Offer Management**
```javascript
GET    /offers/                      // List all offers
POST   /offers/                      // Create new offer
GET    /offers/{id}/                 // Get offer details
PUT    /offers/{id}/                 // Update offer
DELETE /offers/{id}/                 // Delete offer
```

### **7. Placement Statistics (NEW)**
```javascript
GET    /statistics/                  // List all placement statistics
POST   /statistics/                  // Create new statistics
GET    /statistics/{id}/             // Get statistics details
PUT    /statistics/{id}/             // Update statistics
DELETE /statistics/{id}/             // Delete statistics

// Custom actions
GET    /statistics/overview/         // Get overall placement overview
```

### **8. Company Feedback (NEW)**
```javascript
GET    /feedbacks/                   // List all company feedback
POST   /feedbacks/                   // Create new feedback
GET    /feedbacks/{id}/              // Get feedback details
PUT    /feedbacks/{id}/              // Update feedback
DELETE /feedbacks/{id}/              // Delete feedback
```

### **9. Document Management (NEW)**
```javascript
GET    /documents/                   // List all placement documents
POST   /documents/                   // Upload new document
GET    /documents/{id}/              // Get document details
PUT    /documents/{id}/              // Update document
DELETE /documents/{id}/              // Delete document
```

### **10. Alumni Network (NEW)**
```javascript
GET    /alumni/                      // List all alumni placements
POST   /alumni/                      // Create new alumni record
GET    /alumni/{id}/                 // Get alumni details
PUT    /alumni/{id}/                 // Update alumni record
DELETE /alumni/{id}/                 // Delete alumni record

// Custom actions
GET    /alumni/alumni-network/       // Get alumni network statistics
```

### **11. Analytics & Reporting (NEW)**
```javascript
GET    /analytics/trends/            // Get placement trends over years
GET    /analytics/nirf-report/       // Generate NIRF compliance report
```

## 🎨 **UI/UX Requirements**

### **Design Principles:**
- **Modern & Clean:** Use modern design patterns and clean layouts
- **Responsive:** Mobile-first design that works on all devices
- **Accessible:** Follow WCAG guidelines for accessibility
- **Intuitive:** Easy navigation and user-friendly interface
- **Professional:** University-grade professional appearance

### **Color Scheme:**
- **Primary:** University blue (#1e40af)
- **Secondary:** Success green (#059669)
- **Warning:** Amber (#d97706)
- **Error:** Red (#dc2626)
- **Neutral:** Gray scale (#6b7280, #9ca3af, #d1d5db)

### **Typography:**
- **Headings:** Inter or Roboto (bold, 600-700 weight)
- **Body:** Inter or Roboto (regular, 400 weight)
- **Code:** JetBrains Mono or Fira Code

## 📱 **Page Structure & Components**

### **1. Dashboard Page**
```javascript
// Main dashboard with key metrics
- Placement Statistics Overview
- Recent Activities
- Quick Actions
- Charts and Graphs
- NIRF Compliance Status
```

### **2. Company Management**
```javascript
// Company listing and management
- Company List with filters and search
- Company Details Modal/Page
- Add/Edit Company Form
- Company Statistics View
- Company Rating System
```

### **3. Job Posting Management**
```javascript
// Job posting management
- Job List with filters
- Job Details View
- Add/Edit Job Form
- Application Management
- Skills and Requirements
```

### **4. Placement Drive Management**
```javascript
// Placement drive management
- Drive Calendar View
- Drive List with status
- Add/Edit Drive Form
- Drive Statistics
- Company Integration
```

### **5. Application Tracking**
```javascript
// Application management
- Application Pipeline View
- Status Management
- Bulk Operations
- Application Details
- Interview Scheduling
```

### **6. Offer Management**
```javascript
// Offer management
- Offer List with filters
- Offer Details View
- Acceptance Tracking
- Salary Analytics
- Joining Management
```

### **7. Placement Statistics (NEW)**
```javascript
// Statistics dashboard
- Department-wise Statistics
- Program-wise Breakdown
- NIRF Metrics Display
- Trend Analysis Charts
- Export Functionality
```

### **8. Company Feedback (NEW)**
```javascript
// Feedback management
- Feedback Collection Form
- Feedback Analytics
- Rating Visualization
- Improvement Suggestions
- Feedback History
```

### **9. Document Management (NEW)**
```javascript
// Document management
- Document Library
- File Upload Interface
- Document Categories
- Search and Filter
- Version Control
```

### **10. Alumni Network (NEW)**
```javascript
// Alumni management
- Alumni Directory
- Network Visualization
- Mentorship Matching
- Career Tracking
- Contact Management
```

### **11. Analytics & Reporting (NEW)**
```javascript
// Analytics dashboard
- Placement Trends
- NIRF Reports
- Company Performance
- Salary Analytics
- Export Options
```

## 🛠 **Technical Implementation**

### **Frontend Framework:**
```javascript
// Recommended: React with TypeScript
- React 18+ with hooks
- TypeScript for type safety
- Next.js for SSR/SSG (optional)
- Tailwind CSS for styling
- React Query for API state management
```

### **State Management:**
```javascript
// Recommended: Zustand or Redux Toolkit
- Global state for user authentication
- API state management with React Query
- Local state for forms and UI
- Persistent state for user preferences
```

### **API Integration:**
```javascript
// HTTP client setup
import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1/placements/api',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  }
});

// API service functions
export const companyService = {
  getAll: () => api.get('/companies/'),
  getById: (id) => api.get(`/companies/${id}/`),
  create: (data) => api.post('/companies/', data),
  update: (id, data) => api.put(`/companies/${id}/`, data),
  delete: (id) => api.delete(`/companies/${id}/`),
  getStatistics: (id) => api.get(`/companies/${id}/statistics/`)
};
```

### **Form Handling:**
```javascript
// Recommended: React Hook Form with validation
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

// Form validation schemas
const companySchema = yup.object({
  name: yup.string().required('Company name is required'),
  industry: yup.string().required('Industry is required'),
  company_size: yup.string().required('Company size is required'),
  rating: yup.number().min(0).max(5),
  contact_email: yup.string().email('Invalid email format')
});
```

### **Data Visualization:**
```javascript
// Recommended: Chart.js or Recharts
import { LineChart, BarChart, PieChart } from 'recharts';

// Chart components for analytics
const PlacementTrendsChart = ({ data }) => (
  <LineChart width={800} height={400} data={data}>
    <XAxis dataKey="academic_year" />
    <YAxis />
    <CartesianGrid strokeDasharray="3 3" />
    <Tooltip />
    <Legend />
    <Line type="monotone" dataKey="placement_percentage" stroke="#1e40af" />
  </LineChart>
);
```

## 📊 **Key Features Implementation**

### **1. Enhanced Company Management**
```javascript
// Company form with new fields
const CompanyForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: yupResolver(companySchema)
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label>Company Name *</label>
          <input {...register('name')} />
          {errors.name && <span>{errors.name.message}</span>}
        </div>
        
        <div>
          <label>Company Size *</label>
          <select {...register('company_size')}>
            <option value="STARTUP">Startup (1-50 employees)</option>
            <option value="SMALL">Small (51-200 employees)</option>
            <option value="MEDIUM">Medium (201-1000 employees)</option>
            <option value="LARGE">Large (1001-5000 employees)</option>
            <option value="ENTERPRISE">Enterprise (5000+ employees)</option>
          </select>
        </div>
        
        <div>
          <label>Rating (0-5)</label>
          <input type="number" step="0.1" min="0" max="5" {...register('rating')} />
        </div>
        
        <div>
          <label>Total Placements</label>
          <input type="number" {...register('total_placements')} />
        </div>
      </div>
    </form>
  );
};
```

### **2. Placement Statistics Dashboard**
```javascript
// Statistics dashboard component
const PlacementStatisticsDashboard = () => {
  const { data: overview } = useQuery('placement-overview', 
    () => api.get('/statistics/overview/')
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard 
        title="Total Students" 
        value={overview?.data.overview.total_students}
        icon={<UsersIcon />}
      />
      <StatCard 
        title="Placed Students" 
        value={overview?.data.overview.placed_students}
        icon={<CheckCircleIcon />}
      />
      <StatCard 
        title="Placement %" 
        value={`${overview?.data.overview.placement_percentage}%`}
        icon={<TrendingUpIcon />}
      />
      <StatCard 
        title="Avg Salary" 
        value={`₹${overview?.data.overview.average_salary?.toLocaleString()}`}
        icon={<CurrencyRupeeIcon />}
      />
    </div>
  );
};
```

### **3. Company Feedback System**
```javascript
// Feedback form component
const CompanyFeedbackForm = () => {
  return (
    <form className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label>Overall Rating *</label>
          <RatingInput 
            value={rating}
            onChange={setRating}
            max={5}
          />
        </div>
        
        <div>
          <label>Student Quality Rating *</label>
          <RatingInput 
            value={studentQualityRating}
            onChange={setStudentQualityRating}
            max={5}
          />
        </div>
      </div>
      
      <div>
        <label>Positive Feedback</label>
        <textarea 
          rows={4}
          placeholder="What went well during the placement drive?"
        />
      </div>
      
      <div>
        <label>Areas for Improvement</label>
        <textarea 
          rows={4}
          placeholder="What can be improved for future drives?"
        />
      </div>
      
      <div className="flex items-center">
        <input type="checkbox" id="would_visit_again" />
        <label htmlFor="would_visit_again">Would visit again</label>
      </div>
    </form>
  );
};
```

### **4. Alumni Network Management**
```javascript
// Alumni network component
const AlumniNetwork = () => {
  const { data: networkData } = useQuery('alumni-network', 
    () => api.get('/alumni/alumni-network/')
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Total Alumni" 
          value={networkData?.data.statistics.total_alumni}
        />
        <StatCard 
          title="Willing Mentors" 
          value={networkData?.data.statistics.willing_mentors}
        />
        <StatCard 
          title="Willing Recruiters" 
          value={networkData?.data.statistics.willing_recruiters}
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlumniDirectory alumni={networkData?.data.alumni_list} />
        <TopCompanies companies={networkData?.data.top_companies} />
      </div>
    </div>
  );
};
```

### **5. Analytics & Reporting**
```javascript
// Analytics dashboard
const AnalyticsDashboard = () => {
  const { data: trends } = useQuery('placement-trends', 
    () => api.get('/analytics/trends/')
  );
  
  const { data: nirfReport } = useQuery('nirf-report', 
    () => api.get('/analytics/nirf-report/')
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PlacementTrendsChart data={trends?.data.trends} />
        <NIRFComplianceChart data={nirfReport?.data.nirf_metrics} />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SalaryAnalytics data={trends?.data.trends} />
        <CompanyPerformanceChart data={companyData} />
      </div>
    </div>
  );
};
```

## 🔐 **Authentication & Authorization**

### **User Roles:**
```javascript
// Role-based access control
const ROLES = {
  ADMIN: 'admin',
  PLACEMENT_OFFICER: 'placement_officer',
  FACULTY: 'faculty',
  STUDENT: 'student'
};

// Permission checks
const usePermissions = () => {
  const { user } = useAuth();
  
  return {
    canManageCompanies: user?.role === ROLES.ADMIN || user?.role === ROLES.PLACEMENT_OFFICER,
    canViewStatistics: user?.role !== ROLES.STUDENT,
    canManageDocuments: user?.role === ROLES.ADMIN || user?.role === ROLES.PLACEMENT_OFFICER,
    canViewAnalytics: user?.role === ROLES.ADMIN || user?.role === ROLES.PLACEMENT_OFFICER
  };
};
```

## 📱 **Responsive Design**

### **Mobile-First Approach:**
```css
/* Tailwind CSS responsive classes */
.container {
  @apply px-4 sm:px-6 lg:px-8;
}

.grid-responsive {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6;
}

.card {
  @apply bg-white rounded-lg shadow-md p-4 md:p-6;
}

.form-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6;
}
```

## 🧪 **Testing Requirements**

### **Unit Tests:**
```javascript
// Component testing with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { CompanyForm } from './CompanyForm';

test('renders company form with required fields', () => {
  render(<CompanyForm />);
  expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/industry/i)).toBeInTheDocument();
});
```

### **Integration Tests:**
```javascript
// API integration testing
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.get('/api/v1/placements/api/companies/', (req, res, ctx) => {
    return res(ctx.json({ results: mockCompanies }));
  })
);
```

## 📦 **Package Dependencies**

### **Core Dependencies:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "next": "^14.0.0",
    "tailwindcss": "^3.3.0",
    "@headlessui/react": "^1.7.0",
    "@heroicons/react": "^2.0.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
    "react-hook-form": "^7.47.0",
    "@hookform/resolvers": "^3.3.0",
    "yup": "^1.3.0",
    "recharts": "^2.8.0",
    "date-fns": "^2.30.0",
    "react-hot-toast": "^2.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.0",
    "jest": "^29.7.0",
    "msw": "^2.0.0"
  }
}
```

## 🚀 **Implementation Steps**

### **Phase 1: Core Setup (Week 1)**
1. Set up React project with TypeScript
2. Configure Tailwind CSS and design system
3. Set up API client and authentication
4. Create basic routing and layout

### **Phase 2: Basic CRUD Operations (Week 2-3)**
1. Implement Company management
2. Implement Job Posting management
3. Implement Application tracking
4. Implement Placement Drive management

### **Phase 3: Enhanced Features (Week 4-5)**
1. Implement Placement Statistics dashboard
2. Implement Company Feedback system
3. Implement Document Management
4. Implement Alumni Network

### **Phase 4: Analytics & Reporting (Week 6)**
1. Implement Analytics dashboard
2. Implement NIRF reporting
3. Implement data visualization
4. Implement export functionality

### **Phase 5: Testing & Optimization (Week 7)**
1. Write unit and integration tests
2. Performance optimization
3. Accessibility improvements
4. Mobile responsiveness testing

## 📋 **Deliverables**

### **Code Deliverables:**
- Complete React application with TypeScript
- All 11 API endpoints integrated
- Responsive design for all screen sizes
- Comprehensive test coverage
- Documentation and README

### **Documentation Deliverables:**
- API integration guide
- Component documentation
- User manual
- Deployment guide
- Testing guide

## 🎯 **Success Criteria**

### **Functional Requirements:**
- ✅ All 11 API endpoints working correctly
- ✅ All CRUD operations functional
- ✅ NIRF compliance features implemented
- ✅ Analytics and reporting working
- ✅ Mobile responsive design
- ✅ Accessibility compliance

### **Performance Requirements:**
- ✅ Page load time < 3 seconds
- ✅ API response time < 1 second
- ✅ Mobile performance score > 90
- ✅ Desktop performance score > 95

### **Quality Requirements:**
- ✅ 90%+ test coverage
- ✅ Zero critical bugs
- ✅ WCAG 2.1 AA compliance
- ✅ Cross-browser compatibility

---

## 🎉 **Final Notes**

This implementation will create a world-class placement management system that meets university standards in India. The frontend will provide an intuitive, modern interface for managing all aspects of placements while ensuring compliance with NIRF and UGC requirements.

**Key Benefits:**
- **Enhanced User Experience** with modern, responsive design
- **Complete Functionality** covering all placement management needs
- **NIRF Compliance** for ranking submissions
- **Advanced Analytics** for data-driven decisions
- **Alumni Network** for long-term engagement
- **Document Management** for compliance tracking
- **Company Feedback** for continuous improvement

**Ready for Production:** The system will be production-ready with comprehensive testing, documentation, and deployment guides.
