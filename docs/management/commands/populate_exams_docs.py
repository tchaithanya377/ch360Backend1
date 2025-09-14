from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Exams module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Exams documentation...')

        category, _ = Category.objects.get_or_create(
            slug='exams-api',
            defaults={
                'name': 'Exams API',
                'description': 'Sessions, schedules, hall tickets, attendance, results and reports',
                'icon': 'fas fa-file-alt',
                'color': '#e67e22',
                'order': 60,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'exams-overview',
                'title': 'Exams – Overview',
                'desc': 'End-to-end flow: create exam session, build schedule, allocate rooms and staff, generate hall tickets, mark attendance, publish results.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints are under `/api/v1/exams/api/`. Example: `GET /api/v1/exams/api/exam-sessions/`'),
                    ('Auth', 'Use JWT access token: header `Authorization: Bearer ACCESS_TOKEN`.'),
                    ('Data flow', '1) Session -> 2) Schedule -> 3) Rooms/Staff -> 4) Hall tickets -> 5) Attendance -> 6) Results -> 7) Reports.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/exams/api/exam-sessions/"),
                ],
            },
            {
                'slug': 'exams-sessions-schedules-guide',
                'title': 'Exam Sessions & Schedules – Create and List',
                'desc': 'Create an exam session (e.g., Midterm Mar-2025) and add schedules for each course/section.',
                'order': 2,
                'steps': [
                    ('Create session', 'POST `/api/v1/exams/api/exam-sessions/` with title/date range.'),
                    ('Add schedule', 'POST `/api/v1/exams/api/exam-schedules/` with `session`, `course_section`, `exam_date`, `start_time`, `end_time`.'),
                    ('List schedules', 'GET `/api/v1/exams/api/exam-schedules/?session=<id>`'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' 'http://127.0.0.1:8000/api/v1/exams/api/exam-schedules/?session=1'"),
                ],
            },
            {
                'slug': 'exams-halltickets-rooms-staff-guide',
                'title': 'Hall Tickets, Room & Staff Allocation',
                'desc': 'Bulk-generate hall tickets and allocate rooms/staff for invigilation.',
                'order': 3,
                'steps': [
                    ('Generate hall tickets', 'POST `/api/v1/exams/api/bulk-operations/generate-hall-tickets/` for a session.'),
                    ('Assign rooms', 'POST `/api/v1/exams/api/bulk-operations/assign-rooms/` with mapping rules.'),
                    ('Assign staff', 'POST `/api/v1/exams/api/bulk-operations/assign-staff/`'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/exams/api/bulk-operations/generate-hall-tickets/ -H 'Authorization: Bearer ACCESS_TOKEN'"),
                ],
            },
            {
                'slug': 'exams-attendance-results-guide',
                'title': 'Exam Attendance & Results – Mark and Publish',
                'desc': 'Record who attended and publish results per student.',
                'order': 4,
                'steps': [
                    ('Mark attendance', 'POST/PUT `/api/v1/exams/api/exam-attendance/` entries for each hall-ticket/student.'),
                    ('Publish results', 'POST `/api/v1/exams/api/exam-results/` with `student`, `course_section`, `marks`, `grade`.'),
                    ('Reports', 'GET `/api/v1/exams/api/reports/exam-summary/` and `/api/v1/exams/api/reports/student-performance/`.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/exams/api/reports/exam-summary/"),
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
                    'estimated_time': 12,
                    'tags': 'exams,hall-tickets,schedule,attendance,results,postman,react',
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

        self.stdout.write(self.style.SUCCESS('Exams documentation ready. Visit /docs/tutorials/'))


