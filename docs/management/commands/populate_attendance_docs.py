from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Attendance module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Attendance documentation...')

        category, _ = Category.objects.get_or_create(
            slug='attendance-api',
            defaults={
                'name': 'Attendance API',
                'description': 'Attendance sessions and records for course sections',
                'icon': 'fas fa-calendar-check',
                'color': '#9b59b6',
                'order': 40,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'attendance-overview',
                'title': 'Attendance – Overview',
                'desc': 'Create a session for a course section and generate per-student records, then mark present/absent.',
                'order': 1,
                'steps': [
                    ('Base URLs', 'Sessions: `/api/v1/attendance/attendance/sessions/` Records: `/api/v1/attendance/attendance/records/`'),
                    ('Auth', 'Use JWT access token in header `Authorization: Bearer ACCESS_TOKEN`.'),
                    ('Flow', '1) Create session -> 2) Generate records -> 3) Update records (present/absent) -> 4) List reports.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/attendance/attendance/sessions/"),
                ],
            },
            {
                'slug': 'attendance-sessions-guide',
                'title': 'Sessions – Create and Generate Records',
                'desc': 'Start a session for a timetable or course section and auto-create records for enrolled students.',
                'order': 2,
                'steps': [
                    ('Create session', 'POST `/api/v1/attendance/attendance/sessions/` with JSON including `course_section`, optional `timetable`, `session_date`. Returns session id.'),
                    ('Generate records', 'POST `/api/v1/attendance/attendance/sessions/{id}/generate_records/` to create `AttendanceRecord` for each enrolled student.'),
                    ('List sessions', 'GET `/api/v1/attendance/attendance/sessions/` with filters.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/attendance/attendance/sessions/UUID/generate_records/ -H 'Authorization: Bearer ACCESS_TOKEN'"),
                    ('javascript', "// src/attendance/sessions.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function createSession(payload){\n  const {data}=await api.post('/api/v1/attendance/attendance/sessions/',payload);\n  return data;\n}\nexport async function generateRecords(id){\n  const {data}=await api.post(`/api/v1/attendance/attendance/sessions/${id}/generate_records/`);\n  return data;\n}"),
                ],
            },
            {
                'slug': 'attendance-records-guide',
                'title': 'Records – Mark Present/Absent',
                'desc': 'Update attendance for each student record in a session.',
                'order': 3,
                'steps': [
                    ('List records for a session', 'GET `/api/v1/attendance/attendance/records/?session=<session_id>`'),
                    ('Mark present', 'PATCH `/api/v1/attendance/attendance/records/<record_id>/` with `{ "status": "PRESENT" }`'),
                    ('Mark absent', 'PATCH `/api/v1/attendance/attendance/records/<record_id>/` with `{ "status": "ABSENT" }`'),
                ],
                'code': [
                    ('bash', "curl -X PATCH http://127.0.0.1:8000/api/v1/attendance/attendance/records/UUID/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"status\":\"PRESENT\"}'"),
                    ('javascript', "// src/attendance/records.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function updateRecord(id, payload){\n  const {data}=await api.patch(`/api/v1/attendance/attendance/records/${id}/`,payload);\n  return data;\n}"),
                ],
            },
        ]

        for spec in tutorials:
            tut, _ = Tutorial.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'title': spec['title'],
                    'description': spec['desc'],
                    'content': spec['desc'],
                    'category': category,
                    'difficulty': 'beginner',
                    'estimated_time': 10,
                    'tags': 'attendance,sessions,records,postman,react',
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

        self.stdout.write(self.style.SUCCESS('Attendance documentation ready. Visit /docs/tutorials/'))


