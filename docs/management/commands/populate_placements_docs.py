from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Placements module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Placements documentation...')

        category, _ = Category.objects.get_or_create(
            slug='placements-api',
            defaults={
                'name': 'Placements API',
                'description': 'Companies, jobs, placement drives, applications, interview rounds, and offers',
                'icon': 'fas fa-briefcase',
                'color': '#2980b9',
                'order': 130,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'placements-overview',
                'title': 'Placements – Overview',
                'desc': 'Add companies and jobs, run placement drives, collect applications, record interview rounds, and issue offers.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints under `/api/v1/placements/api/`'),
                    ('Flow', '1) Create company & job -> 2) Create drive -> 3) Students apply -> 4) Interview rounds -> 5) Offer.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/placements/api/companies/"),
                ],
            },
            {
                'slug': 'placements-companies-jobs-guide',
                'title': 'Companies & Jobs – Create and List',
                'desc': 'Register a company and post job openings.',
                'order': 2,
                'steps': [
                    ('Create company', 'POST `/api/v1/placements/api/companies/` with name, industry, website.'),
                    ('Create job', 'POST `/api/v1/placements/api/jobs/` with `company`, role, ctc, eligibility.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/placements/api/companies/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"name\":\"Acme Corp\"}'"),
                ],
            },
            {
                'slug': 'placements-drives-applications-guide',
                'title': 'Placement Drives & Applications',
                'desc': 'Create a drive for a job and allow students to apply. Track application status across stages.',
                'order': 3,
                'steps': [
                    ('Create drive', 'POST `/api/v1/placements/api/drives/` with `job`, date, location.'),
                    ('Student applies', 'POST `/api/v1/placements/api/applications/` with `job`, `student`, resume link.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/placements/api/applications/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"job\":1,\"student\":1,\"resume_url\":\"http://example.com/resume.pdf\"}'"),
                ],
            },
            {
                'slug': 'placements-rounds-offers-guide',
                'title': 'Interview Rounds & Offers',
                'desc': 'Record round outcomes and issue final offer letters.',
                'order': 4,
                'steps': [
                    ('Add round result', 'POST `/api/v1/placements/api/rounds/` with `application`, round type, result.'),
                    ('Create offer', 'POST `/api/v1/placements/api/offers/` with `application`, CTC, joining date.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/placements/api/offers/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"application\":1,\"ctc\":\"12 LPA\",\"joining_date\":\"2025-07-01\"}'"),
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
                    'tags': 'placements,companies,jobs,drives,applications,offers',
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

        self.stdout.write(self.style.SUCCESS('Placements documentation ready. Visit /docs/tutorials/'))


