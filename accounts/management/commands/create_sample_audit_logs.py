from django.core.management.base import BaseCommand
from accounts.utils import create_sample_audit_logs


class Command(BaseCommand):
    help = 'Create sample audit logs for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample audit logs...')
        
        logs = create_sample_audit_logs()
        
        if logs:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {len(logs)} sample audit logs')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Failed to create sample audit logs')
            )
