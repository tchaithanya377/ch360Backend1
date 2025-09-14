from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, APIEndpoint, CodeExample, Step, FAQ

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the documentation app with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample documentation data...')

        # Create categories
        categories_data = [
            {
                'name': 'Authentication',
                'slug': 'authentication',
                'description': 'Learn how to authenticate with CampusHub 360 APIs',
                'icon': 'fas fa-key',
                'color': '#e74c3c',
                'order': 1
            },
            {
                'name': 'Students',
                'slug': 'students',
                'description': 'Student management and enrollment APIs',
                'icon': 'fas fa-user-graduate',
                'color': '#3498db',
                'order': 2
            },
            {
                'name': 'Faculty',
                'slug': 'faculty',
                'description': 'Faculty and staff management APIs',
                'icon': 'fas fa-chalkboard-teacher',
                'color': '#2ecc71',
                'order': 3
            },
            {
                'name': 'Academics',
                'slug': 'academics',
                'description': 'Academic programs, courses, and enrollment',
                'icon': 'fas fa-book-open',
                'color': '#f39c12',
                'order': 4
            },
            {
                'name': 'Attendance',
                'slug': 'attendance',
                'description': 'Student attendance tracking and management',
                'icon': 'fas fa-calendar-check',
                'color': '#9b59b6',
                'order': 5
            }
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Get or create a user for tutorials
        try:
            user = User.objects.get(email='admin@campushub360.com')
        except User.DoesNotExist:
            user = User.objects.create_user(
                email='admin@campushub360.com',
                username='docs_admin',
                is_staff=True,
                is_active=True
            )

        # Create tutorials
        tutorials_data = [
            {
                'title': 'Getting Started with CampusHub 360 API',
                'slug': 'getting-started-api',
                'description': 'Learn the basics of integrating with CampusHub 360 APIs, including authentication and making your first API call.',
                'content': '''# Getting Started with CampusHub 360 API

Welcome to the CampusHub 360 API! This tutorial will guide you through the basics of integrating with our platform.

## What You'll Learn

- How to obtain API credentials
- Setting up authentication
- Making your first API request
- Understanding the response format

## Prerequisites

Before you begin, make sure you have:
- A CampusHub 360 account
- Basic knowledge of HTTP requests
- A programming language of your choice (we'll show examples in multiple languages)

## Step 1: Get Your API Credentials

First, you need to obtain your API credentials from the CampusHub 360 dashboard.

1. Log in to your CampusHub 360 account
2. Navigate to Settings > API Keys
3. Click "Generate New API Key"
4. Copy your API key and keep it secure

## Step 2: Understanding Authentication

CampusHub 360 uses API key authentication. Include your API key in the Authorization header of all requests.

## Step 3: Making Your First Request

Let's make a simple request to test your connection.''',
                'category': categories['authentication'],
                'difficulty': 'beginner',
                'estimated_time': 15,
                'prerequisites': 'Basic understanding of HTTP requests and JSON',
                'tags': 'api,authentication,getting-started,http',
                'author': user,
                'featured': True,
                'order': 1
            },
            {
                'title': 'Student Enrollment API Integration',
                'slug': 'student-enrollment-api',
                'description': 'Complete guide to integrating with the student enrollment system using our REST API.',
                'content': '''# Student Enrollment API Integration

This tutorial covers how to integrate with the CampusHub 360 student enrollment system.

## Overview

The Student Enrollment API allows you to:
- Create new student enrollments
- Update existing enrollments
- Retrieve enrollment information
- Manage enrollment status

## Authentication

All requests require authentication using your API key.''',
                'category': categories['students'],
                'difficulty': 'intermediate',
                'estimated_time': 30,
                'prerequisites': 'Completed the Getting Started tutorial',
                'tags': 'students,enrollment,api,integration',
                'author': user,
                'featured': True,
                'order': 2
            },
            {
                'title': 'Advanced Faculty Management',
                'slug': 'advanced-faculty-management',
                'description': 'Learn advanced techniques for managing faculty data, including bulk operations and complex queries.',
                'content': '''# Advanced Faculty Management

This advanced tutorial covers sophisticated faculty management techniques.

## Topics Covered

- Bulk faculty operations
- Complex querying
- Performance optimization
- Error handling strategies''',
                'category': categories['faculty'],
                'difficulty': 'advanced',
                'estimated_time': 45,
                'prerequisites': 'Intermediate knowledge of APIs and database concepts',
                'tags': 'faculty,advanced,bulk-operations,performance',
                'author': user,
                'featured': False,
                'order': 3
            }
        ]

        tutorials = {}
        for tutorial_data in tutorials_data:
            tutorial, created = Tutorial.objects.get_or_create(
                slug=tutorial_data['slug'],
                defaults=tutorial_data
            )
            tutorials[tutorial_data['slug']] = tutorial
            if created:
                self.stdout.write(f'Created tutorial: {tutorial.title}')

        # Create steps for the first tutorial
        steps_data = [
            {
                'tutorial': tutorials['getting-started-api'],
                'title': 'Obtain API Credentials',
                'content': '''To get started with the CampusHub 360 API, you first need to obtain your API credentials.

1. **Log in to CampusHub 360**: Navigate to your CampusHub 360 dashboard
2. **Access API Settings**: Go to Settings > API Keys
3. **Generate New Key**: Click "Generate New API Key"
4. **Copy and Store**: Copy your API key and store it securely

**Important**: Keep your API key secure and never share it publicly. Treat it like a password.''',
                'order': 1
            },
            {
                'tutorial': tutorials['getting-started-api'],
                'title': 'Set Up Authentication',
                'content': '''Now that you have your API key, let's set up authentication for your requests.

The CampusHub 360 API uses API key authentication. Include your API key in the Authorization header of all requests:

```
Authorization: Bearer YOUR_API_KEY_HERE
```

This header must be included with every request to authenticate your application.''',
                'order': 2
            },
            {
                'tutorial': tutorials['getting-started-api'],
                'title': 'Make Your First Request',
                'content': '''Let's make a simple request to test your connection and authentication.

We'll use the health check endpoint which doesn't require any parameters:

**Endpoint**: `GET /api/health/`

This endpoint will return basic information about the API status and confirm that your authentication is working correctly.''',
                'order': 3
            }
        ]

        for step_data in steps_data:
            step, created = Step.objects.get_or_create(
                tutorial=step_data['tutorial'],
                order=step_data['order'],
                defaults=step_data
            )
            if created:
                self.stdout.write(f'Created step: {step.title}')

        # Create code examples
        code_examples_data = [
            {
                'title': 'cURL Example',
                'language': 'curl',
                'code': '''curl -X GET "https://api.campushub360.com/api/health/" \\
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \\
  -H "Content-Type: application/json"''',
                'description': 'Test your API connection using cURL',
                'tutorial': tutorials['getting-started-api'],
                'order': 1
            },
            {
                'title': 'JavaScript Example',
                'language': 'javascript',
                'code': '''const response = await fetch('https://api.campushub360.com/api/health/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY_HERE',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
console.log(data);''',
                'description': 'Make API requests using JavaScript fetch',
                'tutorial': tutorials['getting-started-api'],
                'order': 2
            },
            {
                'title': 'Python Example',
                'language': 'python',
                'code': '''import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY_HERE',
    'Content-Type': 'application/json'
}

response = requests.get('https://api.campushub360.com/api/health/', headers=headers)
data = response.json()
print(data)''',
                'description': 'Make API requests using Python requests library',
                'tutorial': tutorials['getting-started-api'],
                'order': 3
            }
        ]

        for example_data in code_examples_data:
            example, created = CodeExample.objects.get_or_create(
                tutorial=example_data['tutorial'],
                title=example_data['title'],
                defaults=example_data
            )
            if created:
                self.stdout.write(f'Created code example: {example.title}')

        # Create API endpoints
        api_endpoints_data = [
            {
                'title': 'Health Check',
                'endpoint': '/api/health/',
                'method': 'GET',
                'description': 'Check the health status of the API and verify authentication',
                'category': categories['authentication'],
                'request_headers': {
                    'Authorization': {
                        'value': 'Bearer YOUR_API_KEY',
                        'required': True
                    },
                    'Content-Type': {
                        'value': 'application/json',
                        'required': False
                    }
                },
                'response_schema': {
                    'status': 'string',
                    'message': 'string',
                    'timestamp': 'string',
                    'version': 'string'
                },
                'example_response': {
                    'status': 'healthy',
                    'message': 'API is running normally',
                    'timestamp': '2024-01-15T10:30:00Z',
                    'version': '1.0.0'
                },
                'status_codes': {
                    '200': 'API is healthy',
                    '401': 'Invalid or missing API key',
                    '500': 'Internal server error'
                },
                'authentication_required': True,
                'rate_limit': '100 requests per minute',
                'tags': 'health,status,authentication',
                'featured': True,
                'order': 1
            },
            {
                'title': 'Get Student List',
                'endpoint': '/api/v1/students/',
                'method': 'GET',
                'description': 'Retrieve a list of students with optional filtering and pagination',
                'category': categories['students'],
                'request_headers': {
                    'Authorization': {
                        'value': 'Bearer YOUR_API_KEY',
                        'required': True
                    }
                },
                'query_parameters': {
                    'page': {
                        'type': 'integer',
                        'description': 'Page number for pagination',
                        'required': False
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Number of students per page',
                        'required': False
                    },
                    'search': {
                        'type': 'string',
                        'description': 'Search term for student name or ID',
                        'required': False
                    }
                },
                'response_schema': {
                    'count': 'integer',
                    'next': 'string',
                    'previous': 'string',
                    'results': [
                        {
                            'id': 'integer',
                            'name': 'string',
                            'email': 'string',
                            'student_id': 'string',
                            'program': 'string'
                        }
                    ]
                },
                'example_response': {
                    'count': 150,
                    'next': 'https://api.campushub360.com/api/v1/students/?page=2',
                    'previous': None,
                    'results': [
                        {
                            'id': 1,
                            'name': 'John Doe',
                            'email': 'john.doe@university.edu',
                            'student_id': 'STU001',
                            'program': 'Computer Science'
                        }
                    ]
                },
                'status_codes': {
                    '200': 'Success',
                    '401': 'Authentication required',
                    '403': 'Insufficient permissions',
                    '500': 'Internal server error'
                },
                'authentication_required': True,
                'rate_limit': '1000 requests per hour',
                'tags': 'students,list,pagination,search',
                'featured': True,
                'order': 2
            },
            {
                'title': 'Create Student',
                'endpoint': '/api/v1/students/',
                'method': 'POST',
                'description': 'Create a new student record',
                'category': categories['students'],
                'request_headers': {
                    'Authorization': {
                        'value': 'Bearer YOUR_API_KEY',
                        'required': True
                    },
                    'Content-Type': {
                        'value': 'application/json',
                        'required': True
                    }
                },
                'request_body': {
                    'name': {
                        'type': 'string',
                        'required': True,
                        'description': 'Full name of the student'
                    },
                    'email': {
                        'type': 'string',
                        'required': True,
                        'description': 'Email address of the student'
                    },
                    'student_id': {
                        'type': 'string',
                        'required': True,
                        'description': 'Unique student identifier'
                    },
                    'program': {
                        'type': 'string',
                        'required': False,
                        'description': 'Academic program'
                    }
                },
                'response_schema': {
                    'id': 'integer',
                    'name': 'string',
                    'email': 'string',
                    'student_id': 'string',
                    'program': 'string',
                    'created_at': 'string'
                },
                'example_response': {
                    'id': 123,
                    'name': 'Jane Smith',
                    'email': 'jane.smith@university.edu',
                    'student_id': 'STU002',
                    'program': 'Business Administration',
                    'created_at': '2024-01-15T10:30:00Z'
                },
                'status_codes': {
                    '201': 'Student created successfully',
                    '400': 'Invalid request data',
                    '401': 'Authentication required',
                    '403': 'Insufficient permissions',
                    '409': 'Student with this ID already exists',
                    '500': 'Internal server error'
                },
                'authentication_required': True,
                'rate_limit': '100 requests per hour',
                'tags': 'students,create,post',
                'featured': False,
                'order': 3
            }
        ]

        for api_data in api_endpoints_data:
            api, created = APIEndpoint.objects.get_or_create(
                endpoint=api_data['endpoint'],
                method=api_data['method'],
                defaults=api_data
            )
            if created:
                self.stdout.write(f'Created API endpoint: {api.title}')

        # Create code examples for API endpoints
        api_code_examples_data = [
            {
                'title': 'cURL Example',
                'language': 'curl',
                'code': '''curl -X GET "https://api.campushub360.com/api/v1/students/" \\
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \\
  -H "Content-Type: application/json"''',
                'description': 'Get student list using cURL',
                'api_endpoint': APIEndpoint.objects.get(endpoint='/api/v1/students/', method='GET'),
                'order': 1
            },
            {
                'title': 'JavaScript Example',
                'language': 'javascript',
                'code': '''const response = await fetch('https://api.campushub360.com/api/v1/students/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY_HERE',
    'Content-Type': 'application/json'
  }
});

const students = await response.json();
console.log(students);''',
                'description': 'Get student list using JavaScript',
                'api_endpoint': APIEndpoint.objects.get(endpoint='/api/v1/students/', method='GET'),
                'order': 2
            }
        ]

        for example_data in api_code_examples_data:
            example, created = CodeExample.objects.get_or_create(
                api_endpoint=example_data['api_endpoint'],
                title=example_data['title'],
                defaults=example_data
            )
            if created:
                self.stdout.write(f'Created API code example: {example.title}')

        # Create FAQs
        faqs_data = [
            {
                'question': 'How do I get an API key?',
                'answer': 'To get an API key, log in to your CampusHub 360 dashboard, navigate to Settings > API Keys, and click "Generate New API Key". Keep your API key secure and never share it publicly.',
                'category': categories['authentication'],
                'order': 1
            },
            {
                'question': 'What is the rate limit for API requests?',
                'answer': 'Rate limits vary by endpoint. Most endpoints allow 1000 requests per hour, while some sensitive operations have lower limits. Check the specific endpoint documentation for exact limits.',
                'category': categories['authentication'],
                'order': 2
            },
            {
                'question': 'How do I handle pagination in API responses?',
                'answer': 'Many list endpoints support pagination. Use the "page" parameter to specify which page to retrieve, and "limit" to control the number of items per page. The response includes "next" and "previous" URLs for navigation.',
                'category': categories['students'],
                'order': 3
            },
            {
                'question': 'What authentication methods are supported?',
                'answer': 'CampusHub 360 API currently supports API key authentication. Include your API key in the Authorization header as "Bearer YOUR_API_KEY".',
                'category': categories['authentication'],
                'order': 4
            },
            {
                'question': 'How do I handle errors in API responses?',
                'answer': 'API errors are returned with appropriate HTTP status codes and error messages in the response body. Always check the status code and handle errors gracefully in your application.',
                'category': categories['authentication'],
                'order': 5
            }
        ]

        for faq_data in faqs_data:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                self.stdout.write(f'Created FAQ: {faq.question}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated documentation with sample data!')
        )
