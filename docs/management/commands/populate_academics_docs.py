from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample, APIEndpoint


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials and API docs for Academics endpoints (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Academics documentation...')

        category, _ = Category.objects.get_or_create(
            slug='academics-api',
            defaults={
                'name': 'Academics API',
                'description': 'Courses, Syllabi, Timetables, Enrollments, Academic Calendar',
                'icon': 'fas fa-book-open',
                'color': '#f39c12',
                'order': 20,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        # High-level getting started tutorial
        getting_started, _ = Tutorial.objects.update_or_create(
            slug='academics-api-overview',
            defaults={
                'title': 'Academics API – Overview',
                'description': 'Understand resources and base URLs for Courses, Syllabi, Timetables, Enrollments, and Academic Calendar.',
                'content': 'This guide explains the endpoints under /api/v1/academics/api/. You need a valid JWT access token from Accounts. Each tutorial below shows Postman steps and React + Vite code.',
                'category': category,
                'difficulty': 'beginner',
                'estimated_time': 8,
                'tags': 'academics,courses,syllabi,timetable,enrollment,calendar',
                'author': author,
                'featured': True,
                'order': 1,
            },
        )

        # Detailed multi-step overview
        Step.objects.filter(tutorial=getting_started).delete()
        Step.objects.create(
            tutorial=getting_started,
            order=1,
            title='Base URLs',
            content='All endpoints live under `http://127.0.0.1:8000/api/v1/academics/api/`. Example: Courses list is `GET /api/v1/academics/api/courses/`.'
        )
        Step.objects.create(
            tutorial=getting_started,
            order=2,
            title='Authentication',
            content='Get a JWT `access` token from Accounts Login. In Postman set header `Authorization: Bearer ACCESS_TOKEN` for every request.'
        )
        Step.objects.create(
            tutorial=getting_started,
            order=3,
            title='Postman setup',
            content='Create a collection, add a variable `base` = `http://127.0.0.1:8000`. Use `{{base}}/api/v1/academics/api/courses/` in requests.'
        )
        Step.objects.create(
            tutorial=getting_started,
            order=4,
            title='Common headers',
            content='Add headers: `Authorization: Bearer {{access}}`, `Content-Type: application/json` for POST/PUT/PATCH.'
        )
        Step.objects.create(
            tutorial=getting_started,
            order=5,
            title='React quick start',
            content='Use Axios instance with `baseURL` = `http://127.0.0.1:8000` and set `Authorization` header after login. Then call academics endpoints.'
        )

        # Per-resource simple, focused tutorials
        specs = [
            {
                'slug': 'academics-courses-guide',
                'title': 'Courses – List, Create, Detail',
                'desc': 'Work with course catalog. Filter, search, and fetch details.',
                'order': 2,
                'endpoints': [
                    ('GET', '/api/v1/academics/api/courses/'),
                    ('POST', '/api/v1/academics/api/courses/'),
                    ('GET', '/api/v1/academics/api/courses/{id}/'),
                    ('GET', '/api/v1/academics/api/courses/{id}/detail/'),
                ],
                'steps': [
                    ('List courses', 'GET `/api/v1/academics/api/courses/` with header `Authorization: Bearer ACCESS_TOKEN`. Supports `search` and `ordering` query params`. Example response contains `id, code, title, credits, department`. Use pagination params if enabled: `?page=1&page_size=20`.'),
                    ('Filter and search', 'Use `?search=DS` or `?ordering=title`. Combine with pagination params if enabled.'),
                    ('Create course (admin only)', 'POST `/api/v1/academics/api/courses/` with JSON: ```json\n{\n  "code":"CS101",\n  "title":"Intro CS",\n  "credits":4,\n  "level":"UG",\n  "status":"ACTIVE"\n}\n``` Error 400: missing required fields or duplicate `code`. Error 403: insufficient permissions.'),
                    ('Get course detail', 'GET `/api/v1/academics/api/courses/{id}/detail/` to fetch syllabus, timetables and more.'),
                    ('React tip', 'Make a component that lists courses and on click fetches `/detail/` to show extended info.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/academics/api/courses/"),
                    ('javascript', "// src/courses.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function listCourses(params={}){\n  const {data}=await api.get('/api/v1/academics/api/courses/',{params});\n  return data;\n}\nexport async function createCourse(payload){\n  const {data}=await api.post('/api/v1/academics/api/courses/',payload);\n  return data;\n}"),
                ],
            },
            {
                'slug': 'academics-syllabi-guide',
                'title': 'Syllabi – List, Approve, Topics',
                'desc': 'Manage syllabi and see topic breakdown.',
                'order': 3,
                'endpoints': [
                    ('GET', '/api/v1/academics/api/syllabi/'),
                    ('GET', '/api/v1/academics/api/syllabi/{id}/detail/'),
                    ('POST', '/api/v1/academics/api/syllabi/{id}/approve/'),
                    ('GET', '/api/v1/academics/api/syllabus-topics/'),
                ],
                'steps': [
                    ('List syllabi', 'GET `/api/v1/academics/api/syllabi/`. Each item links to a course and includes `academic_year`, `semester`, `status`. Use `?course=<id>` to narrow down.'),
                    ('View details', 'GET `/api/v1/academics/api/syllabi/{id}/detail/`'),
                    ('Approve (draft only)', 'POST `/api/v1/academics/api/syllabi/{id}/approve/`. Error 400 if status is not DRAFT.'),
                    ('By academic year', 'GET `/api/v1/academics/api/syllabi/by_academic_year/?academic_year=2024-25`'),
                    ('React tip', 'Render topics from `syllabus.topics` array to show a weekly plan.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/academics/api/syllabi/"),
                    ('javascript', "// src/syllabi.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function syllabusDetail(id){\n  const {data}=await api.get(`/api/v1/academics/api/syllabi/${id}/detail/`);\n  return data;\n}"),
                ],
            },
            {
                'slug': 'academics-timetables-guide',
                'title': 'Timetables – Weekly Schedule & Conflicts',
                'desc': 'Query weekly schedules and detect conflicts.',
                'order': 4,
                'endpoints': [
                    ('GET', '/api/v1/academics/api/timetables/'),
                    ('GET', '/api/v1/academics/api/timetables/weekly_schedule/'),
                    ('GET', '/api/v1/academics/api/timetables/conflicts/'),
                ],
                'steps': [
                    ('Weekly schedule', 'GET `/api/v1/academics/api/timetables/weekly_schedule/?faculty_id=1&academic_year=2024-25&semester=ODD`'),
                    ('Filter by course', 'Add `&course_id=10` to view a specific course schedule.'),
                    ('Conflicts', 'GET `/api/v1/academics/api/timetables/conflicts/?faculty_id=1&room=R101&academic_year=2024-25&semester=ODD`'),
                    ('React tip', 'Group results by `day_of_week` to render a weekly grid.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' 'http://127.0.0.1:8000/api/v1/academics/api/timetables/weekly_schedule/?faculty_id=1'"),
                    ('javascript', "// src/timetables.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function weeklySchedule(params){\n  const {data}=await api.get('/api/v1/academics/api/timetables/weekly_schedule/',{params});\n  return data.weekly_schedule;\n}"),
                ],
            },
            {
                'slug': 'academics-enrollments-guide',
                'title': 'Course Enrollments – By Student/Course',
                'desc': 'Create enrollments and query by student or course.',
                'order': 5,
                'endpoints': [
                    ('GET', '/api/v1/academics/api/enrollments/'),
                    ('POST', '/api/v1/academics/api/enrollments/'),
                    ('GET', '/api/v1/academics/api/enrollments/by_student/'),
                    ('GET', '/api/v1/academics/api/enrollments/by_course/'),
                ],
                'steps': [
                    ('List enrollments', 'GET `/api/v1/academics/api/enrollments/`'),
                    ('By student', 'GET `/api/v1/academics/api/enrollments/by_student/?student_id=123`'),
                    ('By course', 'GET `/api/v1/academics/api/enrollments/by_course/?course_id=10`'),
                    ('Create enrollment', 'POST `/api/v1/academics/api/enrollments/` with JSON: `{ "student":1, "course_section":10 }`'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' 'http://127.0.0.1:8000/api/v1/academics/api/enrollments/by_student/?student_id=1'"),
                    ('javascript', "// src/enrollments.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function enroll(payload){\n  const {data}=await api.post('/api/v1/academics/api/enrollments/',payload);\n  return data;\n}"),
                ],
            },
            {
                'slug': 'academics-calendar-guide',
                'title': 'Academic Calendar – Upcoming & By Month',
                'desc': 'Upcoming events and days within a period.',
                'order': 6,
                'endpoints': [
                    ('GET', '/api/v1/academics/api/academic-calendar/'),
                    ('GET', '/api/v1/academics/api/academic-calendar/upcoming_events/'),
                    ('GET', '/api/v1/academics/api/academic-calendar/by_month/'),
                    ('GET', '/api/v1/academics/api/academic-calendar/academic_days/'),
                ],
                'steps': [
                    ('Upcoming', 'GET `/api/v1/academics/api/academic-calendar/upcoming_events/`'),
                    ('By month', 'GET `/api/v1/academics/api/academic-calendar/by_month/?year=2025&month=1`'),
                    ('Academic days', 'GET `/api/v1/academics/api/academic-calendar/academic_days/?start_date=2025-01-01&end_date=2025-01-31`'),
                    ('React tip', 'Map events to a calendar component and color-code by `event_type`.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/academics/api/academic-calendar/upcoming_events/"),
                    ('javascript', "// src/calendar.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function eventsByMonth(year,month){\n  const {data}=await api.get('/api/v1/academics/api/academic-calendar/by_month/',{params:{year,month}});\n  return data;\n}"),
                ],
            },
        ]

        for spec in specs:
            tut, _ = Tutorial.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'title': spec['title'],
                    'description': spec['desc'],
                    'content': spec['desc'],
                    'category': category,
                    'difficulty': 'beginner',
                    'estimated_time': 12,
                    'tags': 'academics,api,postman,react',
                    'author': author,
                    'order': spec['order'],
                },
            )
            Step.objects.filter(tutorial=tut).delete()
            for idx, (title, content) in enumerate(spec['steps'], start=1):
                Step.objects.create(tutorial=tut, title=title, content=content, order=idx)
            CodeExample.objects.filter(tutorial=tut).delete()
            for idx, (lang, code) in enumerate(spec['code'], start=1):
                CodeExample.objects.create(tutorial=tut, language=lang, code=code, title=f'Example {idx}', order=idx)

        self.stdout.write(self.style.SUCCESS('Academics documentation ready. Visit /docs/tutorials/'))


