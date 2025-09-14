from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create high-value indexes for assignments at scale (CONCURRENTLY)."

    def handle(self, *args, **options):
        statements = [
            (
                "idx_submission_assignment_student",
                """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submission_assignment_student
                ON assignments_assignmentsubmission (assignment_id, student_id);
                """,
            ),
            (
                "idx_submission_status_created",
                """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_submission_status_created
                ON assignments_assignmentsubmission (status, created_at);
                """,
            ),
        ]

        with connection.cursor() as cursor:
            for name, sql in statements:
                self.stdout.write(f"Creating index {name} if missing...")
                cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS("Assignments indexes ensured."))


