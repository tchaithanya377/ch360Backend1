from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials for Facilities module (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Facilities documentation...')

        category, _ = Category.objects.get_or_create(
            slug='facilities-api',
            defaults={
                'name': 'Facilities API',
                'description': 'Buildings, rooms, equipment, bookings, and maintenance',
                'icon': 'fas fa-building',
                'color': '#34495e',
                'order': 70,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'facilities-overview',
                'title': 'Facilities – Overview',
                'desc': 'Manage physical infrastructure: buildings and rooms, equipment inventory, room bookings, and maintenance tickets.',
                'order': 1,
                'steps': [
                    ('Note about routes', 'The API router is commented in `facilities/urls.py`. Enable it to expose REST endpoints, or use the dashboard pages meanwhile.'),
                    ('Suggested API base', 'When enabled: `/api/v1/facilities/api/` with resources: buildings, rooms, equipment, bookings, maintenance.'),
                ],
                'code': [
                    ('bash', "sed -n '1,80p' facilities/urls.py"),
                ],
            },
            {
                'slug': 'facilities-rooms-bookings-guide',
                'title': 'Rooms & Bookings – Availability and Create',
                'desc': 'Check availability and create bookings (via existing dashboard endpoints or API when enabled).',
                'order': 2,
                'steps': [
                    ('Check availability', 'GET `/facilities/rooms/<room_id>/availability/` returns free slots.'),
                    ('Create booking (dashboard view)', 'POST form to `/facilities/bookings/create/` or, via API (when enabled), POST `/api/v1/facilities/api/bookings/`.'),
                ],
                'code': [
                    ('bash', "curl http://127.0.0.1:8000/facilities/rooms/1/availability/"),
                ],
            },
            {
                'slug': 'facilities-maintenance-guide',
                'title': 'Maintenance – Create and Track',
                'desc': 'Open maintenance tickets for rooms/equipment and track status.',
                'order': 3,
                'steps': [
                    ('Create ticket (when API enabled)', 'POST `/api/v1/facilities/api/maintenance/` with `room/equipment`, description, priority.'),
                    ('Track status', 'GET `/facilities/maintenance/` dashboard page lists current tickets.'),
                ],
                'code': [
                    ('bash', "echo 'Enable API routes in facilities/urls.py to POST maintenance tickets'"),
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
                    'tags': 'facilities,rooms,bookings,maintenance',
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

        self.stdout.write(self.style.SUCCESS('Facilities documentation ready. Visit /docs/tutorials/'))


