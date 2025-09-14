from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Faculty module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Faculty documentation...')

        category, _ = Category.objects.get_or_create(
            slug='faculty-api',
            defaults={
                'name': 'Faculty API',
                'description': 'Manage faculty profiles, schedules, leaves, performance, and documents',
                'icon': 'fas fa-chalkboard-teacher',
                'color': '#2ecc71',
                'order': 80,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'faculty-overview',
                'title': 'Faculty – Overview',
                'desc': 'Endpoints under `/api/v1/faculty/api/` help you read/update faculty info, schedules, leaves, and performance.',
                'order': 1,
                'steps': [
                    ('Base URL', 'Example list: `GET /api/v1/faculty/api/faculty/`'),
                    ('Auth', 'Use JWT access token in Authorization header.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/faculty/api/faculty/"),
                ],
            },
            {
                'slug': 'faculty-profiles-guide',
                'title': 'Profiles – List and Update',
                'desc': 'Find faculty by department and update basic details.',
                'order': 2,
                'steps': [
                    ('List faculty', 'GET `/api/v1/faculty/api/faculty/`'),
                    ('Filter', 'Use `?search=name` or department filter if supported.'),
                    ('Update', 'PATCH `/api/v1/faculty/api/faculty/<id>/` with fields to update.'),
                ],
                'code': [
                    ('bash', "curl -X PATCH http://127.0.0.1:8000/api/v1/faculty/api/faculty/1/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"phone\":\"9999999999\"}'"),
                ],
            },
            {
                'slug': 'faculty-schedules-guide',
                'title': 'Schedules – Weekly View',
                'desc': 'Fetch schedules assigned to a faculty member.',
                'order': 3,
                'steps': [
                    ('List schedules', 'GET `/api/v1/faculty/api/schedules/?faculty=<id>`'),
                ],
                'code': [
                    ('bash', "curl 'http://127.0.0.1:8000/api/v1/faculty/api/schedules/?faculty=1' -H 'Authorization: Bearer ACCESS_TOKEN'"),
                ],
            },
            {
                'slug': 'faculty-leaves-guide',
                'title': 'Leaves – Apply and Approve',
                'desc': 'Create leave requests and approve/reject them.',
                'order': 4,
                'steps': [
                    ('Apply leave', 'POST `/api/v1/faculty/api/leaves/` with dates and reason.'),
                    ('Approve/Reject', 'PATCH `/api/v1/faculty/api/leaves/<id>/` to change status.'),
                ],
                'code': [
                    ('bash', "echo 'POST /api/v1/faculty/api/leaves/ with JSON payload'"),
                ],
            },
            {
                'slug': 'faculty-performance-docs-guide',
                'title': 'Performance & Documents',
                'desc': 'Record performance metrics and upload documents like certificates.',
                'order': 5,
                'steps': [
                    ('Performance', 'POST `/api/v1/faculty/api/performance/` with metrics.'),
                    ('Documents', 'POST `/api/v1/faculty/api/documents/` with file and metadata.'),
                ],
                'code': [
                    ('bash', "echo 'Use multipart/form-data to upload documents to /api/v1/faculty/api/documents/'"),
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
                    'tags': 'faculty,profile,schedule,leave,performance,documents',
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

        self.stdout.write(self.style.SUCCESS('Faculty documentation ready. Visit /docs/tutorials/'))


