# 🎓 Grades System Frontend Implementation Guide

## 📋 Overview
Complete guide to implement the Indian University Grades System (CBCS compliant) in your frontend application.

## 🔗 API Endpoints

### Base URL
```
http://your-domain.com/api/v1/grads/
```

### Authentication
```javascript
// Get JWT Token
POST /api/auth/token/
{
  "email": "admin@gmail.com",
  "password": "admin123"
}

// Use Token in Headers
Authorization: Bearer <your_jwt_token>
```

## 🎯 API Endpoints Reference

### 1. Health Check
```javascript
GET /api/v1/grads/health/
// Response: {"status": "ok", "app": "grads"}
```

### 2. Grade Scales Management
```javascript
// Get all grade scales
GET /api/v1/grads/grade-scales/

// Get specific grade scale
GET /api/v1/grads/grade-scales/{id}/

// Create new grade scale
POST /api/v1/grads/grade-scales/
{
  "letter": "A+",
  "description": "Excellent",
  "min_score": 80.00,
  "max_score": 89.00,
  "grade_points": 9.00,
  "is_active": true
}

// Update grade scale
PUT /api/v1/grads/grade-scales/{id}/

// Delete grade scale
DELETE /api/v1/grads/grade-scales/{id}/
```

### 3. Mid-Term Grades
```javascript
// Get all midterm grades
GET /api/v1/grads/midterm-grades/

// Get specific midterm grade
GET /api/v1/grads/midterm-grades/{id}/

// Create midterm grade
POST /api/v1/grads/midterm-grades/
{
  "student": "student-uuid",
  "course_section": 2,
  "semester": 1,
  "midterm_marks": 28,
  "total_marks": 30
}

// Bulk upsert midterm grades
POST /api/v1/grads/midterm-grades/bulk_upsert/
{
  "grades": [
    {
      "student": "student-uuid",
      "course_section": 2,
      "semester": 1,
      "midterm_marks": 25,
      "total_marks": 30
    }
  ]
}
```

### 4. Semester Grades
```javascript
// Get all semester grades
GET /api/v1/grads/semester-grades/

// Get specific semester grade
GET /api/v1/grads/semester-grades/{id}/

// Create semester grade
POST /api/v1/grads/semester-grades/
{
  "student": "student-uuid",
  "course_section": 2,
  "semester": 1,
  "final_marks": 85,
  "total_marks": 100
}

// Bulk upsert semester grades
POST /api/v1/grads/semester-grades/bulk_upsert/
{
  "grades": [
    {
      "student": "student-uuid",
      "course_section": 2,
      "semester": 1,
      "final_marks": 90,
      "total_marks": 100
    }
  ]
}
```

### 5. SGPA (Semester GPA)
```javascript
// Get all SGPA records
GET /api/v1/grads/semester-gpas/

// Get specific SGPA
GET /api/v1/grads/semester-gpas/{id}/

// Filter by student
GET /api/v1/grads/semester-gpas/?student={student_id}
```

### 6. CGPA (Cumulative GPA)
```javascript
// Get all CGPA records
GET /api/v1/grads/cumulative-gpas/

// Get specific CGPA
GET /api/v1/grads/cumulative-gpas/{id}/

// Filter by student
GET /api/v1/grads/cumulative-gpas/?student={student_id}

// Get academic transcript
GET /api/v1/grads/cumulative-gpas/{id}/academic_transcript/
```

## 🚀 Frontend Implementation

### 1. API Service Layer (JavaScript/TypeScript)

```javascript
// api/gradesService.js
class GradesService {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.token = token;
  }

  getHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  // Grade Scales
  async getGradeScales() {
    const response = await fetch(`${this.baseURL}/grade-scales/`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async createGradeScale(data) {
    const response = await fetch(`${this.baseURL}/grade-scales/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  }

  // Midterm Grades
  async getMidtermGrades() {
    const response = await fetch(`${this.baseURL}/midterm-grades/`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async createMidtermGrade(data) {
    const response = await fetch(`${this.baseURL}/midterm-grades/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async bulkUpsertMidtermGrades(grades) {
    const response = await fetch(`${this.baseURL}/midterm-grades/bulk_upsert/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ grades })
    });
    return response.json();
  }

  // Semester Grades
  async getSemesterGrades() {
    const response = await fetch(`${this.baseURL}/semester-grades/`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async createSemesterGrade(data) {
    const response = await fetch(`${this.baseURL}/semester-grades/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data)
    });
    return response.json();
  }

  async bulkUpsertSemesterGrades(grades) {
    const response = await fetch(`${this.baseURL}/semester-grades/bulk_upsert/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ grades })
    });
    return response.json();
  }

  // SGPA
  async getSGPAs(studentId = null) {
    const url = studentId 
      ? `${this.baseURL}/semester-gpas/?student=${studentId}`
      : `${this.baseURL}/semester-gpas/`;
    const response = await fetch(url, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  // CGPA
  async getCGPAs(studentId = null) {
    const url = studentId 
      ? `${this.baseURL}/cumulative-gpas/?student=${studentId}`
      : `${this.baseURL}/cumulative-gpas/`;
    const response = await fetch(url, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  // Academic Transcript
  async getAcademicTranscript(cgpaId) {
    const response = await fetch(`${this.baseURL}/cumulative-gpas/${cgpaId}/academic_transcript/`, {
      headers: this.getHeaders()
    });
    return response.json();
  }
}

export default GradesService;
```

### 2. React Components Example

```jsx
// components/GradeEntryForm.jsx
import React, { useState, useEffect } from 'react';
import GradesService from '../api/gradesService';

const GradeEntryForm = ({ studentId, courseSectionId, semesterId, type = 'midterm' }) => {
  const [formData, setFormData] = useState({
    student: studentId,
    course_section: courseSectionId,
    semester: semesterId,
    marks: '',
    total_marks: 100
  });
  const [gradeScales, setGradeScales] = useState([]);
  const [calculatedGrade, setCalculatedGrade] = useState(null);

  useEffect(() => {
    loadGradeScales();
  }, []);

  const loadGradeScales = async () => {
    try {
      const scales = await gradesService.getGradeScales();
      setGradeScales(scales);
    } catch (error) {
      console.error('Error loading grade scales:', error);
    }
  };

  const calculateGrade = (marks, totalMarks) => {
    const percentage = (marks / totalMarks) * 100;
    const grade = gradeScales.find(scale => 
      percentage >= scale.min_score && percentage <= scale.max_score
    );
    return grade ? {
      letter: grade.letter,
      description: grade.description,
      grade_points: grade.grade_points,
      percentage: percentage
    } : null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const gradeData = {
        ...formData,
        [type === 'midterm' ? 'midterm_marks' : 'final_marks']: parseFloat(formData.marks)
      };
      
      if (type === 'midterm') {
        await gradesService.createMidtermGrade(gradeData);
      } else {
        await gradesService.createSemesterGrade(gradeData);
      }
      
      alert('Grade saved successfully!');
    } catch (error) {
      console.error('Error saving grade:', error);
      alert('Error saving grade');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="grade-entry-form">
      <h3>{type === 'midterm' ? 'Midterm' : 'Semester'} Grade Entry</h3>
      
      <div className="form-group">
        <label>Marks Obtained:</label>
        <input
          type="number"
          value={formData.marks}
          onChange={(e) => {
            const marks = e.target.value;
            setFormData({...formData, marks});
            if (marks && formData.total_marks) {
              setCalculatedGrade(calculateGrade(marks, formData.total_marks));
            }
          }}
          required
        />
      </div>

      <div className="form-group">
        <label>Total Marks:</label>
        <input
          type="number"
          value={formData.total_marks}
          onChange={(e) => setFormData({...formData, total_marks: e.target.value})}
          required
        />
      </div>

      {calculatedGrade && (
        <div className="calculated-grade">
          <h4>Calculated Grade:</h4>
          <p><strong>Grade:</strong> {calculatedGrade.letter} ({calculatedGrade.description})</p>
          <p><strong>Percentage:</strong> {calculatedGrade.percentage.toFixed(2)}%</p>
          <p><strong>Grade Points:</strong> {calculatedGrade.grade_points}</p>
        </div>
      )}

      <button type="submit" className="btn-primary">
        Save {type === 'midterm' ? 'Midterm' : 'Semester'} Grade
      </button>
    </form>
  );
};

export default GradeEntryForm;
```

### 3. SGPA/CGPA Display Component

```jsx
// components/GPADisplay.jsx
import React, { useState, useEffect } from 'react';
import GradesService from '../api/gradesService';

const GPADisplay = ({ studentId }) => {
  const [sgpas, setSGPAs] = useState([]);
  const [cgpa, setCGPA] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGPAData();
  }, [studentId]);

  const loadGPAData = async () => {
    try {
      const [sgpaData, cgpaData] = await Promise.all([
        gradesService.getSGPAs(studentId),
        gradesService.getCGPAs(studentId)
      ]);
      
      setSGPAs(sgpaData);
      setCGPA(cgpaData[0]); // Assuming one CGPA per student
      setLoading(false);
    } catch (error) {
      console.error('Error loading GPA data:', error);
      setLoading(false);
    }
  };

  const getAcademicStandingColor = (standing) => {
    const colors = {
      'EXCELLENT': '#4CAF50',
      'VERY_GOOD': '#8BC34A',
      'GOOD': '#FFC107',
      'SATISFACTORY': '#FF9800',
      'PASS': '#FF5722',
      'PROBATION': '#F44336'
    };
    return colors[standing] || '#9E9E9E';
  };

  const getClassificationColor = (classification) => {
    const colors = {
      'FIRST_CLASS_DISTINCTION': '#4CAF50',
      'FIRST_CLASS': '#8BC34A',
      'SECOND_CLASS': '#FFC107',
      'PASS_CLASS': '#FF9800',
      'FAIL': '#F44336'
    };
    return colors[classification] || '#9E9E9E';
  };

  if (loading) return <div>Loading GPA data...</div>;

  return (
    <div className="gpa-display">
      <h2>Academic Performance</h2>
      
      {/* CGPA Section */}
      {cgpa && (
        <div className="cgpa-section">
          <h3>Cumulative GPA (CGPA)</h3>
          <div className="gpa-card cgpa-card">
            <div className="gpa-value">{cgpa.cgpa}</div>
            <div className="gpa-details">
              <p><strong>Classification:</strong> 
                <span style={{color: getClassificationColor(cgpa.classification)}}>
                  {cgpa.classification?.replace(/_/g, ' ')}
                </span>
              </p>
              <p><strong>Total Credits:</strong> {cgpa.total_credits_earned}</p>
              <p><strong>Graduation Eligible:</strong> 
                <span className={cgpa.is_eligible_for_graduation ? 'eligible' : 'not-eligible'}>
                  {cgpa.is_eligible_for_graduation ? 'Yes' : 'No'}
                </span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* SGPA Section */}
      <div className="sgpa-section">
        <h3>Semester GPAs (SGPA)</h3>
        <div className="sgpa-grid">
          {sgpas.map((sgpa) => (
            <div key={sgpa.id} className="gpa-card sgpa-card">
              <div className="semester-name">{sgpa.semester}</div>
              <div className="gpa-value">{sgpa.sgpa}</div>
              <div className="gpa-details">
                <p><strong>Standing:</strong> 
                  <span style={{color: getAcademicStandingColor(sgpa.academic_standing)}}>
                    {sgpa.academic_standing?.replace(/_/g, ' ')}
                  </span>
                </p>
                <p><strong>Credits:</strong> {sgpa.total_credits}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GPADisplay;
```

### 4. Academic Transcript Component

```jsx
// components/AcademicTranscript.jsx
import React, { useState, useEffect } from 'react';
import GradesService from '../api/gradesService';

const AcademicTranscript = ({ studentId }) => {
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTranscript();
  }, [studentId]);

  const loadTranscript = async () => {
    try {
      // First get CGPA to get transcript
      const cgpas = await gradesService.getCGPAs(studentId);
      if (cgpas.length > 0) {
        const transcriptData = await gradesService.getAcademicTranscript(cgpas[0].id);
        setTranscript(transcriptData);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error loading transcript:', error);
      setLoading(false);
    }
  };

  if (loading) return <div>Loading transcript...</div>;
  if (!transcript) return <div>No transcript data available</div>;

  return (
    <div className="academic-transcript">
      <h2>Academic Transcript</h2>
      
      {/* Student Info */}
      <div className="student-info">
        <h3>{transcript.student.name}</h3>
        <p><strong>Roll Number:</strong> {transcript.student.roll_number}</p>
      </div>

      {/* CGPA Summary */}
      <div className="cgpa-summary">
        <h3>Overall Performance</h3>
        <div className="summary-card">
          <div className="cgpa-value">{transcript.cgpa.value}</div>
          <div className="cgpa-details">
            <p><strong>Classification:</strong> {transcript.cgpa.classification}</p>
            <p><strong>Total Credits:</strong> {transcript.cgpa.total_credits_earned}</p>
            <p><strong>Graduation Eligible:</strong> 
              {transcript.cgpa.is_eligible_for_graduation ? 'Yes' : 'No'}
            </p>
          </div>
        </div>
      </div>

      {/* Semester-wise Details */}
      <div className="semester-details">
        <h3>Semester-wise Performance</h3>
        {transcript.semesters.map((semester, index) => (
          <div key={index} className="semester-card">
            <h4>{semester.semester.name}</h4>
            <div className="semester-sgpa">
              <strong>SGPA:</strong> {semester.sgpa.value} ({semester.sgpa.academic_standing})
            </div>
            
            <div className="courses-table">
              <table>
                <thead>
                  <tr>
                    <th>Course Code</th>
                    <th>Course Title</th>
                    <th>Credits</th>
                    <th>Marks</th>
                    <th>Grade</th>
                    <th>Points</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {semester.courses.map((course, courseIndex) => (
                    <tr key={courseIndex}>
                      <td>{course.course_code}</td>
                      <td>{course.course_title}</td>
                      <td>{course.credits}</td>
                      <td>{course.marks_obtained}/{course.total_marks}</td>
                      <td>{course.grade}</td>
                      <td>{course.grade_points}</td>
                      <td className={course.passed ? 'passed' : 'failed'}>
                        {course.passed ? 'Pass' : 'Fail'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AcademicTranscript;
```

### 5. Bulk Grade Entry Component

```jsx
// components/BulkGradeEntry.jsx
import React, { useState } from 'react';
import GradesService from '../api/gradesService';

const BulkGradeEntry = ({ courseSectionId, semesterId, type = 'midterm' }) => {
  const [students, setStudents] = useState([]);
  const [grades, setGrades] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleGradeChange = (studentId, field, value) => {
    setGrades(prev => {
      const existing = prev.find(g => g.student === studentId);
      if (existing) {
        return prev.map(g => 
          g.student === studentId ? { ...g, [field]: value } : g
        );
      } else {
        return [...prev, {
          student: studentId,
          course_section: courseSectionId,
          semester: semesterId,
          [field]: value
        }];
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const validGrades = grades.filter(g => 
        g.student && (g.midterm_marks || g.final_marks)
      );
      
      if (type === 'midterm') {
        await gradesService.bulkUpsertMidtermGrades(validGrades);
      } else {
        await gradesService.bulkUpsertSemesterGrades(validGrades);
      }
      
      alert('Grades saved successfully!');
      setGrades([]);
    } catch (error) {
      console.error('Error saving grades:', error);
      alert('Error saving grades');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bulk-grade-entry">
      <h3>Bulk {type === 'midterm' ? 'Midterm' : 'Semester'} Grade Entry</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="students-grid">
          {students.map(student => (
            <div key={student.id} className="student-grade-row">
              <div className="student-info">
                <strong>{student.roll_number}</strong>
                <span>{student.first_name} {student.last_name}</span>
              </div>
              
              <div className="grade-inputs">
                <input
                  type="number"
                  placeholder="Marks"
                  value={grades.find(g => g.student === student.id)?.[type === 'midterm' ? 'midterm_marks' : 'final_marks'] || ''}
                  onChange={(e) => handleGradeChange(
                    student.id, 
                    type === 'midterm' ? 'midterm_marks' : 'final_marks', 
                    parseFloat(e.target.value)
                  )}
                />
                <input
                  type="number"
                  placeholder="Total"
                  value={grades.find(g => g.student === student.id)?.total_marks || 100}
                  onChange={(e) => handleGradeChange(student.id, 'total_marks', parseFloat(e.target.value))}
                />
              </div>
            </div>
          ))}
        </div>
        
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Saving...' : 'Save All Grades'}
        </button>
      </form>
    </div>
  );
};

export default BulkGradeEntry;
```

## 🎨 CSS Styles

```css
/* styles/grades.css */
.grade-entry-form {
  max-width: 500px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.calculated-grade {
  background: #f0f8ff;
  padding: 15px;
  border-radius: 4px;
  margin: 15px 0;
}

.gpa-display {
  max-width: 1200px;
  margin: 20px auto;
}

.gpa-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.cgpa-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.sgpa-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.gpa-value {
  font-size: 2.5em;
  font-weight: bold;
  text-align: center;
  margin-bottom: 10px;
}

.sgpa-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.academic-transcript {
  max-width: 1200px;
  margin: 20px auto;
}

.semester-card {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.courses-table {
  overflow-x: auto;
  margin-top: 15px;
}

.courses-table table {
  width: 100%;
  border-collapse: collapse;
}

.courses-table th,
.courses-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.courses-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.passed {
  color: #4CAF50;
  font-weight: bold;
}

.failed {
  color: #F44336;
  font-weight: bold;
}

.eligible {
  color: #4CAF50;
  font-weight: bold;
}

.not-eligible {
  color: #F44336;
  font-weight: bold;
}

.bulk-grade-entry {
  max-width: 800px;
  margin: 20px auto;
}

.students-grid {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.student-grade-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.student-grade-row:last-child {
  border-bottom: none;
}

.student-info {
  flex: 1;
}

.grade-inputs {
  display: flex;
  gap: 10px;
}

.grade-inputs input {
  width: 80px;
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.btn-primary {
  background: #007bff;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-primary:disabled {
  background: #6c757d;
  cursor: not-allowed;
}
```

## 🔧 Usage Examples

### 1. Initialize Service
```javascript
import GradesService from './api/gradesService';

const gradesService = new GradesService(
  'http://your-domain.com/api/v1/grads',
  'your-jwt-token'
);
```

### 2. Load Grade Scales
```javascript
const gradeScales = await gradesService.getGradeScales();
console.log('Available grade scales:', gradeScales);
```

### 3. Enter Midterm Grade
```javascript
const midtermGrade = await gradesService.createMidtermGrade({
  student: 'student-uuid',
  course_section: 2,
  semester: 1,
  midterm_marks: 28,
  total_marks: 30
});
```

### 4. Get Student's SGPA
```javascript
const sgpas = await gradesService.getSGPAs('student-uuid');
console.log('Student SGPA records:', sgpas);
```

### 5. Generate Academic Transcript
```javascript
const transcript = await gradesService.getAcademicTranscript('cgpa-uuid');
console.log('Academic transcript:', transcript);
```

## 🎯 Key Features

✅ **Indian 10-Point Grading System** (O, A+, A, B+, B, C, P, F)
✅ **Automatic Grade Calculation** (Marks → Percentage → Grade → Points)
✅ **SGPA Calculation** (Semester-wise)
✅ **CGPA Calculation** (Cumulative)
✅ **Academic Standing** (Excellent, Very Good, Good, etc.)
✅ **Degree Classification** (First Class, Second Class, etc.)
✅ **Bulk Grade Entry** (Efficient for multiple students)
✅ **Academic Transcript** (Complete academic history)
✅ **Real-time Updates** (SGPA/CGPA update automatically)

## 🚀 Ready to Use!

This implementation provides a complete frontend solution for the Indian University Grades System with all API endpoints properly integrated and user-friendly interfaces for grade management, GPA tracking, and academic transcript generation.
