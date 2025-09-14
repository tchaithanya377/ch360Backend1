from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Feedback module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Feedback documentation...')

        category, _ = Category.objects.get_or_create(
            slug='feedback-api',
            defaults={
                'name': 'Feedback API',
                'description': 'Collect feedback items, comments, attachments and votes',
                'icon': 'fas fa-comment-dots',
                'color': '#8e44ad',
                'order': 90,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'feedback-overview',
                'title': 'Feedback – Overview',
                'desc': 'Create categories and tags, collect feedback items from users, comment, attach files, and vote.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints under `/api/v1/feedback/`'),
                    ('Auth', 'Most actions require JWT access token.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/feedback/categories/"),
                ],
            },
            {
                'slug': 'feedback-items-guide',
                'title': 'Feedback Items – Create and List',
                'desc': 'Create feedback items with title, description, category, and tags; list and filter them.',
                'order': 2,
                'steps': [
                    ('List items', 'GET `/api/v1/feedback/items/`'),
                    ('Create item', 'POST `/api/v1/feedback/items/` with `{ "title":"Improve UI", "description":"Add dark mode", "category": <id> }`'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/feedback/items/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"title\":\"Improve UI\",\"description\":\"Add dark mode\",\"category\":1}'"),
                ],
            },
            {
                'slug': 'feedback-comments-attachments-votes',
                'title': 'Comments, Attachments, and Votes',
                'desc': 'Discuss items with comments, upload screenshots, and upvote ideas.',
                'order': 3,
                'steps': [
                    ('Comment', 'POST `/api/v1/feedback/comments/` with `{ "feedback": <id>, "text": "Great idea" }`'),
                    ('Attachment', 'POST `/api/v1/feedback/attachments/` multipart with `file` and `feedback`'),
                    ('Vote', 'POST `/api/v1/feedback/votes/` with `{ "feedback": <id>, "value": 1 }`'),
                ],
                'code': [
                    ('bash', "echo 'Use multipart/form-data for attachments; JSON for comments and votes'"),
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
                    'estimated_time': 8,
                    'tags': 'feedback,comments,attachments,votes',
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

        self.stdout.write(self.style.SUCCESS('Feedback documentation ready. Visit /docs/tutorials/'))
