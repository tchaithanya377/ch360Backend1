from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = "Enable RLS on key tables and create permissive department policy keyed by app.current_department."

    def handle(self, *args, **options):
        if not getattr(settings, "ENABLE_RLS", False):
            self.stdout.write("ENABLE_RLS is false; skipping.")
            return

        statements = [
            # Students table policy based on department_id; allows all if setting is NULL
            (
                "students_student",
                """
                ALTER TABLE IF EXISTS students_student ENABLE ROW LEVEL SECURITY;
                DO $$ BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'students_student' AND policyname = 'dept_isolation'
                  ) THEN
                    CREATE POLICY dept_isolation ON students_student
                      USING (
                        current_setting('app.current_department', true) IS NULL OR
                        department_id = NULLIF(current_setting('app.current_department', true), '')::int
                      );
                  END IF;
                END $$;
                """,
            ),
        ]

        with connection.cursor() as cursor:
            for table, sql in statements:
                self.stdout.write(f"Applying RLS on {table}...")
                cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS("RLS policies ensured."))


