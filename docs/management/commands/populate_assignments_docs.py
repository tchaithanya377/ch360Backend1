from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Assignments module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Assignments documentation...')

        category, _ = Category.objects.get_or_create(
            slug='assignments-api',
            defaults={
                'name': 'Assignments API',
                'description': 'Categories, Templates, Assignments, Submissions, Grades, Comments',
                'icon': 'fas fa-tasks',
                'color': '#2980b9',
                'order': 30,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'assignments-overview',
                'title': 'Assignments – Overview',
                'desc': 'Understand the flow: Create Template/Category -> Create Assignment -> Publish -> Students Submit -> Grade.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints live under `http://127.0.0.1:8000/api/v1/assignments/`. Requires JWT access token.'),
                    ('Roles', 'Faculty: create templates and assignments, publish and grade. Students: view published assignments and submit.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/assignments/")
                ],
            },
            {
                'slug': 'assignment-categories-guide',
                'title': 'Assignment Categories – List & Create',
                'desc': 'Group assignments into categories (e.g., Homework, Project).',
                'order': 2,
                'steps': [
                    ('List categories', 'GET `/api/v1/assignments/categories/`'),
                    ('Create category', 'POST to `/api/v1/assignments/categories/` with JSON `{ "name": "Homework" }`'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/assignments/categories/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"name\":\"Homework\"}'"),
                    ('javascript', "// src/assignments/categories.js\nimport axios from 'axios';\nconst api=axios.create({baseURL:'http://127.0.0.1:8000'});\nexport async function createCategory(name){\n  const {data}=await api.post('/api/v1/assignments/categories/',{name});\n  return data;\n}")
                ],
            },
            {
                'slug': 'assignment-templates-guide',
                'title': 'Assignment Templates – Reusable Structure',
                'desc': 'Create templates with title, description, due days etc. Use them when creating assignments.',
                'order': 3,
                'steps': [
                    ('List templates', 'GET `/api/v1/assignments/templates/`'),
                    ('Create template', 'POST to `/api/v1/assignments/templates/` with JSON containing title/description/due_date rules'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/assignments/templates/"),
                ],
            },
            {
                'slug': 'assignments-create-publish-guide',
                'title': 'Assignments – Create, Publish, Close',
                'desc': 'Create an assignment from template/category, publish it, later close it.',
                'order': 4,
                'steps': [
                    ('Create assignment', 'POST `/api/v1/assignments/` JSON includes template, course_section, due_date.'),
                    ('Publish', 'POST `/api/v1/assignments/<assignment_id>/publish/`'),
                    ('Close', 'POST `/api/v1/assignments/<assignment_id>/close/`'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/assignments/UUID/publish/ -H 'Authorization: Bearer ACCESS_TOKEN'"),
                ],
            },
            {
                'slug': 'assignment-submissions-guide',
                'title': 'Submissions – Submit and View',
                'desc': 'Students submit work; faculty view submissions for an assignment.',
                'order': 5,
                'steps': [
                    ('Submit', 'POST `/api/v1/assignments/<assignment_id>/submit/` with JSON or file upload via `/files/upload/`'),
                    ('List submissions', 'GET `/api/v1/assignments/<assignment_id>/submissions/`'),
                    ('My assignments', 'GET `/api/v1/assignments/my-assignments/` to see assigned to you.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/v1/assignments/UUID/submissions/"),
                ],
            },
            {
                'slug': 'assignment-grading-guide',
                'title': 'Grades & Comments – Evaluate work',
                'desc': 'Faculty grade a submission and leave comments.',
                'order': 6,
                'steps': [
                    ('Grade', 'POST `/api/v1/assignments/submissions/<submission_id>/grade/` with JSON `{ "score": 95, "feedback": "Great job" }`'),
                    ('Comments', 'POST `/api/v1/assignments/<assignment_id>/comments/` to add discussion'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/assignments/submissions/UUID/grade/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"score\":95,\"feedback\":\"Great job\"}'"),
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
                    'tags': 'assignments,postman,react',
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

        self.stdout.write(self.style.SUCCESS('Assignments documentation ready. Visit /docs/tutorials/'))


