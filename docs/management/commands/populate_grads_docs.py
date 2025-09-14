from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Grads module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Grads documentation...')

        category, _ = Category.objects.get_or_create(
            slug='grads-api',
            defaults={
                'name': 'Grading & Graduation API',
                'description': 'Grade scales, course results, term GPA, and graduate records',
                'icon': 'fas fa-graduation-cap',
                'color': '#1abc9c',
                'order': 110,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'grads-overview',
                'title': 'Grading & Graduation – Overview',
                'desc': 'Define grade scales and compute results. Track term GPA and graduation records.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints under `/api/v1/grads/`'),
                    ('Health check', 'GET `/api/v1/grads/health/` should return OK'),
                    ('Flow', '1) Create grade scales -> 2) Record course results -> 3) Compute term GPA -> 4) Generate graduate record.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/grads/health/"),
                ],
            },
            {
                'slug': 'grads-grade-scales-guide',
                'title': 'Grade Scales – Create and List',
                'desc': 'Define letter grades with min/max marks and grade points.',
                'order': 2,
                'steps': [
                    ('List scales', 'GET `/api/v1/grads/grade-scales/`'),
                    ('Create scale', 'POST `/api/v1/grads/grade-scales/` with entries like A, B, C with ranges and points.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/grads/grade-scales/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"name\":\"UG Scale\"}'"),
                ],
            },
            {
                'slug': 'grads-course-results-gpa-guide',
                'title': 'Course Results & Term GPA',
                'desc': 'Submit course results per student and compute term GPA.',
                'order': 3,
                'steps': [
                    ('Record course result', 'POST `/api/v1/grads/course-results/` with student, course_section, marks, grade.'),
                    ('Compute term GPA', 'GET `/api/v1/grads/term-gpa/?student=<id>&term=<id>`'),
                ],
                'code': [
                    ('bash', "curl 'http://127.0.0.1:8000/api/v1/grads/term-gpa/?student=1&term=2024-ODD'"),
                ],
            },
            {
                'slug': 'grads-graduates-guide',
                'title': 'Graduate Records – Create and Verify',
                'desc': 'After all terms complete, create a graduate record with final CGPA and graduation date.',
                'order': 4,
                'steps': [
                    ('Create record', 'POST `/api/v1/grads/graduates/` with student, program, CGPA, graduation_date.'),
                    ('List/verify', 'GET `/api/v1/grads/graduates/?student=<id>`'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/grads/graduates/ -H 'Authorization: Bearer ACCESS_TOKEN'"),
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
                    'tags': 'grades,gpa,graduation,results',
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

        self.stdout.write(self.style.SUCCESS('Grads documentation ready. Visit /docs/tutorials/'))


