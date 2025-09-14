from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Mentoring module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Mentoring documentation...')

        category, _ = Category.objects.get_or_create(
            slug='mentoring-api',
            defaults={
                'name': 'Mentoring API',
                'description': 'Mentorships, projects, meetings, and feedback between mentors and mentees',
                'icon': 'fas fa-users',
                'color': '#9b59b6',
                'order': 120,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'mentoring-overview',
                'title': 'Mentoring – Overview',
                'desc': 'Set up mentorships, track projects, schedule meetings, and collect feedback.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints under `/api/v1/mentoring/`'),
                    ('Roles', 'Mentor and mentee can create meetings and exchange feedback; projects track deliverables.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/mentoring/mentorships/"),
                ],
            },
            {
                'slug': 'mentoring-mentorships-guide',
                'title': 'Mentorships – Create and Manage',
                'desc': 'Create a mentor–mentee pairing and set goals.',
                'order': 2,
                'steps': [
                    ('List mentorships', 'GET `/api/v1/mentoring/mentorships/`'),
                    ('Create mentorship', 'POST `/api/v1/mentoring/mentorships/` with mentor, mentee, goals, start_date.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/mentoring/mentorships/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"mentor\":1,\"mentee\":2,\"goals\":\"Career guidance\"}'"),
                ],
            },
            {
                'slug': 'mentoring-projects-meetings-guide',
                'title': 'Projects & Meetings – Plan and Record',
                'desc': 'Create projects under a mentorship and schedule meetings with notes and action items.',
                'order': 3,
                'steps': [
                    ('Create project', 'POST `/api/v1/mentoring/projects/` with `mentorship`, `title`, `description`.'),
                    ('Schedule meeting', 'POST `/api/v1/mentoring/meetings/` with `mentorship`, date/time, agenda.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/mentoring/meetings/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"mentorship\":1,\"scheduled_at\":\"2025-01-10T10:00:00Z\",\"agenda\":\"Weekly sync\"}'"),
                ],
            },
            {
                'slug': 'mentoring-feedback-guide',
                'title': 'Mentoring Feedback – Share and Track',
                'desc': 'Record qualitative feedback after meetings or milestones.',
                'order': 4,
                'steps': [
                    ('Create feedback', 'POST `/api/v1/mentoring/feedback/` with `mentorship`, rating, comments.'),
                    ('List feedback', 'GET `/api/v1/mentoring/feedback/?mentorship=<id>`'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/mentoring/feedback/?mentorship=1 -H 'Authorization: Bearer ACCESS_TOKEN'"),
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
                    'tags': 'mentoring,projects,meetings,feedback',
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

        self.stdout.write(self.style.SUCCESS('Mentoring documentation ready. Visit /docs/tutorials/'))


