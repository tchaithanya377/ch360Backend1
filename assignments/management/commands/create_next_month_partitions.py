from django.core.management.base import BaseCommand
from django.db import connection


SQL = r"""
DO $$
DECLARE
    part_start date := date_trunc('month', now() + interval '1 month')::date;
    part_end date := (part_start + interval '1 month')::date;
BEGIN
    -- assignments_assignmentsubmission
    EXECUTE format('CREATE TABLE IF NOT EXISTS assignments_assignmentsubmission_%s PARTITION OF assignments_assignmentsubmission FOR VALUES FROM (%L) TO (%L)',
                   to_char(part_start, 'YYYY_MM'), part_start, part_end);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_assignments_subm_assign_status_date_%s ON assignments_assignmentsubmission_%s (assignment_id, status, submission_date)',
                   to_char(part_start, 'YYYY_MM'), to_char(part_start, 'YYYY_MM'));
END $$;
"""


class Command(BaseCommand):
    help = 'Create next-month partitions for assignments submissions'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(SQL)
        self.stdout.write(self.style.SUCCESS('Created next-month partitions for assignments submissions'))

