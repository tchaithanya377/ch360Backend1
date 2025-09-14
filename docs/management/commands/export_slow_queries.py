import json
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Export top slow queries from pg_stat_statements as JSON to stdout."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20, help="Number of rows to return")

    def handle(self, *args, **options):
        limit = options["limit"]
        sql = """
        SELECT query, calls, total_exec_time, mean_exec_time, rows
        FROM pg_stat_statements
        ORDER BY mean_exec_time DESC
        LIMIT %s;
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, [limit])
                cols = [c[0] for c in cursor.description]
                rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            self.stdout.write(json.dumps({"slow_queries": rows}, indent=2))
        except Exception as exc:
            self.stderr.write(f"Error reading pg_stat_statements: {exc}")


