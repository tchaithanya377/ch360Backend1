import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):
    help = "Drop and recreate DB schema, run migrations, and seed RBAC (DANGEROUS in production)."

    def add_arguments(self, parser):
        parser.add_argument('--yes-i-am-sure', action='store_true', help='Confirm destructive action')
        parser.add_argument('--skip-seed', action='store_true', help='Skip seeding roles/admin')

    def handle(self, *args, **options):
        if not options['yes_i_am_sure']:
            raise CommandError('Refusing to run without --yes-i-am-sure')

        # Use migrate with zero for each app to flush schema
        apps = [
            'students', 'academics', 'departments', 'faculty', 'enrollment', 'attendance', 'assignments',
            'exams', 'fees', 'transportation', 'grads', 'rnd', 'facilities', 'feedback', 'open_requests',
            'docs', 'dashboard', 'accounts'
        ]

        self.stdout.write(self.style.WARNING('Resetting schema to zero...'))
        for app in apps:
            try:
                call_command('migrate', app, 'zero', interactive=False)
            except Exception:
                # Ignore apps without migrations
                pass

        self.stdout.write(self.style.WARNING('Applying fresh migrations...'))
        call_command('migrate', interactive=False)

        if not options['skip_seed']:
            self.stdout.write(self.style.WARNING('Seeding roles/permissions/admin...'))
            call_command('seed_rbac')

        self.stdout.write(self.style.SUCCESS('Rebuild complete.'))


