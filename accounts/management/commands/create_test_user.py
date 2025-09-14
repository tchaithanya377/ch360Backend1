from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create or update a test user with given email and password.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--username', required=False)

    def handle(self, *args, **options):
        User = get_user_model()
        email = options['email']
        password = options['password']
        username = options.get('username') or email.split('@')[0]
        user, created = User.objects.get_or_create(email=email, defaults={'username': username})
        user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(('Created' if created else 'Updated') + f' user: {email}'))


