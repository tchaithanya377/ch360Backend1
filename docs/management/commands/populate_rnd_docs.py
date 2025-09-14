from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for R&D module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating R&D documentation...')

        category, _ = Category.objects.get_or_create(
            slug='rnd-api',
            defaults={
                'name': 'Research & Development API',
                'description': 'Researchers, grants, projects, publications, patents, datasets and collaborations',
                'icon': 'fas fa-flask',
                'color': '#8e44ad',
                'order': 140,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'rnd-overview',
                'title': 'R&D – Overview',
                'desc': 'Catalogue researchers and track grants, projects, publications, patents, and datasets.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints under `/api/v1/rnd/`'),
                    ('Flow', '1) Add researcher -> 2) Create project/grant -> 3) Attach publications/datasets -> 4) Record patents/collaborations.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/rnd/researchers/"),
                ],
            },
            {
                'slug': 'rnd-researchers-projects-guide',
                'title': 'Researchers & Projects',
                'desc': 'Create researcher profiles and create projects with start/end dates and sponsors.',
                'order': 2,
                'steps': [
                    ('Create researcher', 'POST `/api/v1/rnd/researchers/` with name, email, department.'),
                    ('Create project', 'POST `/api/v1/rnd/projects/` with title, PI (researcher), budget.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/rnd/projects/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"title\":\"AI for Education\",\"principal_investigator\":1}'"),
                ],
            },
            {
                'slug': 'rnd-publications-patents-guide',
                'title': 'Publications & Patents',
                'desc': 'Record outputs of research projects.',
                'order': 3,
                'steps': [
                    ('Add publication', 'POST `/api/v1/rnd/publications/` with authors, venue, year, doi.'),
                    ('Add patent', 'POST `/api/v1/rnd/patents/` with title, application_no, status.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/rnd/publications/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"title\":\"Smart Campus\",\"year\":2025}'"),
                ],
            },
            {
                'slug': 'rnd-datasets-collab-guide',
                'title': 'Datasets & Collaborations',
                'desc': 'Publish datasets and manage collaborations with other institutions.',
                'order': 4,
                'steps': [
                    ('Add dataset', 'POST `/api/v1/rnd/datasets/` with `project`, name, link, license.'),
                    ('Add collaboration', 'POST `/api/v1/rnd/collaborations/` with partners and MoU details.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/rnd/datasets/ -H 'Authorization: Bearer ACCESS_TOKEN'"),
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
                    'tags': 'rnd,research,grants,projects,publications,patents',
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

        self.stdout.write(self.style.SUCCESS('R&D documentation ready. Visit /docs/tutorials/'))


