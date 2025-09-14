from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from pathlib import Path
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Students module (beginner friendly, detailed)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Students documentation...')

        category, _ = Category.objects.get_or_create(
            slug='students-api',
            defaults={
                'name': 'Students API',
                'description': 'Manage students, documents, custom fields, bulk operations, and analytics',
                'icon': 'fas fa-user-graduate',
                'color': '#3498db',
                'order': 10,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        # Load markdown sources from tutorials/students
        tutorials_dir = Path(settings.BASE_DIR) / 'tutorials' / 'students'
        md_sources = [
            ('students-api-guide', 'Students API Guide', tutorials_dir / 'api.md', True, 1),
            ('students-default-fields', 'Students – Default Fields', tutorials_dir / 'fields.md', False, 2),
            ('students-frontend-integration', 'Students – Frontend Integration', tutorials_dir / 'frontend.md', False, 3),
        ]

        for slug, title, file_path, featured, order in md_sources:
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                Tutorial.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'title': title,
                        'description': title,
                        'content': content,
                        'category': category,
                        'difficulty': 'beginner',
                        'estimated_time': 15,
                        'tags': 'students,api,frontend,docs',
                        'author': author,
                        'featured': featured,
                        'order': order,
                        'is_published': True,
                    },
                )

        # Overview
        overview, _ = Tutorial.objects.update_or_create(
            slug='students-overview',
            defaults={
                'title': 'Students – Overview',
                'description': 'Base routes, auth, and common headers. Learn how to list, create, search, and manage student resources.',
                'content': 'Use JWT access token. Base: `/api/v1/students/` for dashboard HTML and `/api/v1/students/` API under `students/api_urls.py`. The key routes are in this tutorial set.',
                'category': category,
                'difficulty': 'beginner',
                'estimated_time': 12,
                'tags': 'students,crud,search,bulk,documents,custom-fields',
                'author': author,
                'featured': True,
                'order': 1,
            },
        )

        Step.objects.filter(tutorial=overview).delete()
        steps = [
            ('Base URL and Auth', 'API prefix: `/api/v1/students/`. Set header `Authorization: Bearer ACCESS_TOKEN`. Content-Type: `application/json` for POST/PUT/PATCH.'),
            ('Postman setup', 'Create a collection variable `base` = `http://127.0.0.1:8000`. Use `{{base}}/api/v1/students/`.'),
            ('React setup', 'Create an Axios instance with baseURL `http://127.0.0.1:8000`. After login, set `Authorization` header.'),
        ]
        for idx, (title, content) in enumerate(steps, start=1):
            Step.objects.create(tutorial=overview, title=title, content=content, order=idx)

        CodeExample.objects.update_or_create(
            tutorial=overview,
            title='Axios instance',
            defaults={
                'language': 'javascript',
                'code': "import axios from 'axios';\nexport const api = axios.create({ baseURL: 'http://127.0.0.1:8000' });\nexport function setToken(token){ api.defaults.headers.common.Authorization = `Bearer ${token}`;}\n",
                'order': 1,
            },
        )

        # Detailed guides
        guides = [
            {
                'slug': 'students-crud-guide',
                'title': 'Students – Create, Read, Update, Delete',
                'desc': 'End-to-end CRUD with validation tips and examples.',
                'order': 10,
                'steps': [
                    ('List', 'GET `/api/v1/students/students/` with `search`, `ordering`, and pagination (`?page=1&page_size=20`). Response includes a list of students with keys like `id`, `first_name`, `last_name`, `email`, `roll_number`.'),
                    ('Create', 'POST `/api/v1/students/students/` with JSON: ```json\n{\n  "first_name":"John",\n  "last_name":"Doe",\n  "email":"john@example.com",\n  "roll_number":"20CS001"\n}\n``` Expected 201 Created with student object.'),
                    ('Retrieve', 'GET `/api/v1/students/students/{id}/`'),
                    ('Update', 'PATCH `/api/v1/students/students/{id}/` with fields to change. Example: `{ "phone":"9999999999" }`.'),
                    ('Delete', 'DELETE `/api/v1/students/students/{id}/`'),
                    ('Common errors', '400 for missing fields or duplicate roll/email; 404 if id not found; 401 if missing/invalid token.'),
                    ('Postman tests', 'After Create, save `pm.environment.set("studentId", pm.response.json().id)` then reuse in next requests.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/students/students/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"first_name\":\"John\",\"last_name\":\"Doe\",\"email\":\"john@example.com\",\"roll_number\":\"20CS001\"}'"),
                    ('javascript', "// create student + simple form handling\nimport { api } from './api';\nexport async function createStudent(p){ const {data}=await api.post('/api/v1/students/students/', p); return data;}\nexport async function listStudents(params){ const {data}=await api.get('/api/v1/students/students/',{params}); return data;}"),
                ],
            },
            {
                'slug': 'students-search-stats-guide',
                'title': 'Search and Statistics',
                'desc': 'Use search endpoints and get aggregate stats for dashboards.',
                'order': 11,
                'steps': [
                    ('Search', 'GET `/api/v1/students/students/search/?q=john`. You can combine with filters like `program` if supported.'),
                    ('Stats', 'GET `/api/v1/students/students/stats/` returns counts by status/program/year. Useful for dashboards.'),
                    ('React tip', 'Cache search input (debounce 300ms) before calling the endpoint to reduce requests.'),
                ],
                'code': [
                    ('bash', "curl 'http://127.0.0.1:8000/api/v1/students/students/search/?q=john'"),
                ],
            },
            {
                'slug': 'students-documents-guide',
                'title': 'Documents – Upload and List',
                'desc': 'Attach documents to a student (ID proof, certificates).',
                'order': 12,
                'steps': [
                    ('Upload', 'POST `/api/v1/students/documents/` multipart with `student`, `file`, `doc_type`. In Postman, choose Body > form-data, key `file` type File.'),
                    ('List by student', 'GET `/api/v1/students/students/{id}/documents/`'),
                    ('Errors', '413 if file too large; 400 if missing `file` or `doc_type`.'),
                ],
                'code': [
                    ('bash', "echo 'Use multipart/form-data for /api/v1/students/documents/ with file field'"),
                ],
            },
            {
                'slug': 'students-custom-fields-guide',
                'title': 'Custom Fields – Define and Set Values',
                'desc': 'Create custom field definitions and assign values per student.',
                'order': 13,
                'steps': [
                    ('Create field', 'POST `/api/v1/students/custom-fields/` with `name`, `field_type` (e.g., TEXT, NUMBER, DATE).'),
                    ('Set value', 'POST `/api/v1/students/custom-field-values/` with `student`, `field`, `value`.'),
                    ('Query values', 'GET `/api/v1/students/custom-field-values/by-student/?student=<id>`'),
                    ('React tip', 'Render dynamic forms from custom-field definitions, then POST values.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/students/custom-field-values/by-student/?student=1"),
                ],
            },
            {
                'slug': 'students-bulk-import-guide',
                'title': 'Bulk Import/Update/Delete',
                'desc': 'Automate onboarding and maintenance with CSV imports and bulk operations.',
                'order': 14,
                'steps': [
                    ('Bulk create', 'POST `/api/v1/students/students/bulk-create/` with array of students. Example payload: `[{"first_name":"A","last_name":"B","email":"a@b.com","roll_number":"R1"}]`.'),
                    ('Bulk update', 'POST `/api/v1/students/students/bulk-update/` with updates.'),
                    ('Bulk delete', 'DELETE `/api/v1/students/students/bulk-delete/` with ids to remove.'),
                    ('Imports stats', 'GET `/api/v1/students/imports/stats/` to track processed rows and errors. Use it to show progress bars.'),
                    ('Postman tip', 'Use Collection Runner to send arrays or CSV to bulk endpoints. Assert `pm.response.code === 200` and check counts.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/students/students/bulk-create/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '[{\"first_name\":\"A\",\"last_name\":\"B\",\"email\":\"a@b.com\",\"roll_number\":\"R1\"}]'"),
                ],
            },
        ]

        for spec in guides:
            tut, _ = Tutorial.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'title': spec['title'],
                    'description': spec['desc'],
                    'content': spec['desc'],
                    'category': category,
                    'difficulty': 'beginner',
                    'estimated_time': 15,
                    'tags': 'students,api,postman,react',
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

        self.stdout.write(self.style.SUCCESS('Students documentation ready. Visit /docs/tutorials/'))


