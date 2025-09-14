from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Fees module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Fees documentation...')

        category, _ = Category.objects.get_or_create(
            slug='fees-api',
            defaults={
                'name': 'Fees API',
                'description': 'Fee categories, structures, student fees, payments and receipts',
                'icon': 'fas fa-receipt',
                'color': '#16a085',
                'order': 100,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'fees-overview',
                'title': 'Fees – Overview',
                'desc': 'Define fee categories/structures, assign fees to students, record payments, and generate receipts.',
                'order': 1,
                'steps': [
                    ('Base URL', 'All endpoints under `/api/v1/fees/api/`'),
                    ('Flow', '1) Create categories -> 2) Build structures -> 3) Assign student fees -> 4) Record payments -> 5) Generate receipts.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/api/v1/fees/api/categories/"),
                ],
            },
            {
                'slug': 'fees-structures-guide',
                'title': 'Fee Structures – Create and Assign',
                'desc': 'Define structure (components, amounts) and assign to program/semester.',
                'order': 2,
                'steps': [
                    ('Create category', 'POST `/api/v1/fees/api/categories/` with `{ "name": "Tuition" }`'),
                    ('Create structure', 'POST `/api/v1/fees/api/structures/` with title, program/semester and totals.'),
                    ('Add structure details', 'POST `/api/v1/fees/api/structure-details/` with `structure`, `component`, `amount`.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/fees/api/categories/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"name\":\"Tuition\"}'"),
                ],
            },
            {
                'slug': 'fees-student-payments-guide',
                'title': 'Student Fees & Payments – Record and Receipt',
                'desc': 'Assign fee to a student, record a payment, and download receipt.',
                'order': 3,
                'steps': [
                    ('Assign student fee', 'POST `/api/v1/fees/api/student-fees/` with `student`, `structure`, `due_date`.'),
                    ('Record payment', 'POST `/api/v1/fees/api/payments/` with `student_fee`, `amount`, `mode`.'),
                    ('Receipt', 'GET `/api/v1/fees/api/receipts/?payment=<id>` to fetch receipt data.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/v1/fees/api/payments/ -H 'Authorization: Bearer ACCESS_TOKEN' -H 'Content-Type: application/json' -d '{\"student_fee\":1,\"amount\":5000,\"mode\":\"CASH\"}'"),
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
                    'tags': 'fees,structures,payments,receipts',
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

        self.stdout.write(self.style.SUCCESS('Fees documentation ready. Visit /docs/tutorials/'))


