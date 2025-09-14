from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create high-value indexes for attendance at scale (CONCURRENTLY)."

    def handle(self, *args, **options):
        statements = [
            (
                "idx_attendance_record_session_student",
                """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_record_session_student
                ON attendance_attendancerecord (session_id, student_id);
                """,
            ),
            (
                "idx_attendance_record_student_status",
                """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_record_student_status
                ON attendance_attendancerecord (student_id, status);
                """,
            ),
            (
                "idx_attendance_session_date",
                """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_session_date
                ON attendance_attendancesession (date);
                """,
            ),
        ]

        with connection.cursor() as cursor:
            for name, sql in statements:
                self.stdout.write(f"Creating index {name} if missing...")
                cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS("Attendance indexes ensured."))


