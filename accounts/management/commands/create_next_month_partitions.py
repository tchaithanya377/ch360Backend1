from django.core.management.base import BaseCommand
from django.db import connection


SQL = r"""
DO $$
DECLARE
    part_start date := date_trunc('month', now() + interval '1 month')::date;
    part_end date := (part_start + interval '1 month')::date;
BEGIN
    -- accounts_auditlog
    EXECUTE format('CREATE TABLE IF NOT EXISTS accounts_auditlog_%s PARTITION OF accounts_auditlog FOR VALUES FROM (%L) TO (%L)',
                   to_char(part_start, 'YYYY_MM'), part_start, part_end);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_accounts_auditlog_user_created_at_%s ON accounts_auditlog_%s (user_id, created_at DESC)',
                   to_char(part_start, 'YYYY_MM'), to_char(part_start, 'YYYY_MM'));

    -- accounts_usersession
    EXECUTE format('CREATE TABLE IF NOT EXISTS accounts_usersession_%s PARTITION OF accounts_usersession FOR VALUES FROM (%L) TO (%L)',
                   to_char(part_start, 'YYYY_MM'), part_start, part_end);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_accounts_usersession_user_expires_%s ON accounts_usersession_%s (user_id, expires_at)',
                   to_char(part_start, 'YYYY_MM'), to_char(part_start, 'YYYY_MM'));
END $$;
"""


class Command(BaseCommand):
    help = 'Create next-month partitions for accounts tables (auditlog, usersession)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(SQL)
        self.stdout.write(self.style.SUCCESS('Created next-month partitions for accounts'))

