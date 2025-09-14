# University Student Division and Assignment API

This document describes the university-level student division and assignment functionality added to the students app.

## Overview

The university student division system allows you to:
- View students grouped by department, academic program, year of study, semester, and section
- Assign individual students to specific departments, programs, years, semesters, and sections
- Perform bulk assignments based on criteria
- Get statistics about student distributions across university programs

## New Model Fields

### Student Model
- **department**: Foreign key to `academics.Department` (optional)
- **academic_program**: Foreign key to `academics.AcademicProgram` (optional) - for B.Tech, MBA, MCA, etc.
- **year_of_study**: CharField with choices (1st Year, 2nd Year, 3rd Year, 4th Year, 5th Year)
- **semester**: CharField with choices (Semester 1-10)
- **section**: CharField with choices (A, B, C, D, E) - already existed
- **academic_year**: CharField (e.g., "2023-2024") - already existed

## API Endpoints

### 1. Get Student Divisions
**GET** `/api/students/divisions/`

Returns students grouped by department, program, year of study, semester, and section.

**Query Parameters:**
- `department` (optional): Filter by department ID
- `academic_program` (optional): Filter by academic program ID
- `academic_year` (optional): Filter by academic year
- `year_of_study` (optional): Filter by year of study (1, 2, 3, 4, 5)
- `semester` (optional): Filter by semester (1-10)
- `section` (optional): Filter by section

**Response Example:**
```json
{
  "CS": {
    "department_id": "uuid",
    "department_name": "Computer Science",
    "department_code": "CS",
    "programs": {
      "BTECH": {
        "program_id": "uuid",
        "program_name": "Bachelor of Technology",
        "program_code": "BTECH",
        "program_level": "UG",
        "years": {
          "2023-2024": {
            "year_of_study": {
              "1": {
                "semesters": {
                  "1": {
                    "sections": {
                      "A": {
                        "students": [...],
                        "count": 30
                      },
                      "B": {
                        "students": [...],
                        "count": 28
                      }
                    },
                    "total_students": 58
                  },
                  "2": {
                    "sections": {
                      "A": {
                        "students": [...],
                        "count": 30
                      }
                    },
                    "total_students": 30
                  }
                },
                "total_students": 88
              }
            },
            "total_students": 88
          }
        }
      }
    }
  }
}
```

### 2. Assign Students
**POST** `/api/students/assign/`

Assign multiple students to department, year, and section.

**Request Body:**
```json
{
  "student_ids": ["uuid1", "uuid2", "uuid3"],
  "department_id": "department-uuid",
  "academic_program_id": "program-uuid",
  "academic_year": "2023-2024",
  "year_of_study": "2",
  "semester": "3",
  "section": "A"
}
```

**Response:**
```json
{
  "updated_students": [...],
  "updated_count": 3,
  "errors": []
}
```

### 3. Bulk Assignment by Criteria
**POST** `/api/students/bulk-assign/`

Assign students based on criteria.

**Request Body:**
```json
{
  "criteria": {
    "current_department": "old-department-uuid",
    "current_academic_program": "old-program-uuid",
    "current_academic_year": "2022-2023",
    "current_year_of_study": "1",
    "current_semester": "2",
    "current_section": "A",
    "gender": "M",
    "quota": "GENERAL"
  },
  "assignment": {
    "department_id": "new-department-uuid",
    "academic_program_id": "new-program-uuid",
    "academic_year": "2023-2024",
    "year_of_study": "2",
    "semester": "3",
    "section": "B"
  }
}
```

**Response:**
```json
{
  "updated_count": 45,
  "criteria_matched": 45,
  "sample_updated_students": [...],
  "assignment": {...}
}
```

### 4. Division Statistics
**GET** `/api/students/division-statistics/`

Get statistics about student distributions.

**Query Parameters:**
- `department` (optional): Filter by department ID
- `academic_year` (optional): Filter by academic year

**Response Example:**
```json
{
  "CS": {
    "department_id": "uuid",
    "department_name": "Computer Science",
    "department_code": "CS",
    "total_students": 500,
    "by_year": {
      "2023-2024": {
        "total": 250,
        "sections": {
          "A": 50,
          "B": 48,
          "C": 52,
          "D": 50,
          "E": 50
        }
      }
    },
    "by_year_of_study": {
      "1": 125,
      "2": 120,
      "3": 115,
      "4": 110
    },
    "by_semester": {
      "1": 60,
      "2": 65,
      "3": 58,
      "4": 62,
      "5": 55,
      "6": 60,
      "7": 52,
      "8": 58
    },
    "by_gender": {
      "M": 300,
      "F": 200
    }
  }
}
```

## Usage Examples

### 1. View all students by department and section
```bash
curl -X GET "http://localhost:8000/api/students/divisions/" \
  -H "Authorization: Bearer your-token"
```

### 2. Assign students to B.Tech Computer Science program
```bash
curl -X POST "http://localhost:8000/api/students/assign/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "student_ids": ["student-uuid-1", "student-uuid-2"],
    "department_id": "cs-department-uuid",
    "academic_program_id": "btech-cs-program-uuid",
    "academic_year": "2023-2024",
    "year_of_study": "2",
    "semester": "3",
    "section": "A"
  }'
```

### 3. Bulk promote all 1st year students to 2nd year
```bash
curl -X POST "http://localhost:8000/api/students/bulk-assign/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "criteria": {
      "current_year_of_study": "1",
      "current_semester": "2"
    },
    "assignment": {
      "year_of_study": "2",
      "semester": "3",
      "academic_year": "2023-2024"
    }
  }'
```

### 4. Transfer MBA students to new semester
```bash
curl -X POST "http://localhost:8000/api/students/bulk-assign/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "criteria": {
      "current_academic_program": "mba-program-uuid",
      "current_semester": "1"
    },
    "assignment": {
      "semester": "2",
      "academic_year": "2023-2024"
    }
  }'
```

### 4. Get statistics for a specific department
```bash
curl -X GET "http://localhost:8000/api/students/division-statistics/?department=cs-department-uuid" \
  -H "Authorization: Bearer your-token"
```

## Migration

To apply the database changes, run:
```bash
python manage.py migrate students
```

## Notes

- All endpoints require authentication
- Department field is optional and can be null
- Bulk operations are limited to active students only
- The system validates department existence before assignment
- Error handling is included for invalid student IDs and departments
