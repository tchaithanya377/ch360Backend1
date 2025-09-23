from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Create high-value indexes for attendance at scale (CONCURRENTLY)."

    def handle(self, *args, **options):
        # Check if we're using PostgreSQL
        is_postgresql = connection.vendor == 'postgresql'
        
        if is_postgresql:
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
        else:
            # SQLite and other databases
            statements = [
                (
                    "idx_attendance_record_session_student",
                    """
                    CREATE INDEX IF NOT EXISTS idx_attendance_record_session_student
                    ON attendance_attendancerecord (session_id, student_id);
                    """,
                ),
                (
                    "idx_attendance_record_student_status",
                    """
                    CREATE INDEX IF NOT EXISTS idx_attendance_record_student_status
                    ON attendance_attendancerecord (student_id, status);
                    """,
                ),
                (
                    "idx_attendance_session_date",
                    """
                    CREATE INDEX IF NOT EXISTS idx_attendance_session_date
                    ON attendance_attendancesession (date);
                    """,
                ),
            ]

        with connection.cursor() as cursor:
            for name, sql in statements:
                self.stdout.write(f"Creating index {name} if missing...")
                try:
                    cursor.execute(sql)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to create index {name}: {e}")
                    )
        self.stdout.write(self.style.SUCCESS("Attendance indexes ensured."))


