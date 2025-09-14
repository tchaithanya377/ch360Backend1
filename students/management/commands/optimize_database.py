"""
Django management command to optimize database for high-performance student queries
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database for high-performance student queries (20K+ RPS)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze current database performance',
        )
        parser.add_argument(
            '--create-indexes',
            action='store_true',
            help='Create optimized indexes',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Run VACUUM ANALYZE on student tables',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.analyze_performance()
            self.create_indexes()
            self.vacuum_tables()
            self.optimize_settings()
        else:
            if options['analyze']:
                self.analyze_performance()
            if options['create_indexes']:
                self.create_indexes()
            if options['vacuum']:
                self.vacuum_tables()

        self.stdout.write(
            self.style.SUCCESS('Database optimization completed successfully!')
        )

    def analyze_performance(self):
        """Analyze current database performance"""
        self.stdout.write('Analyzing database performance...')
        
        with connection.cursor() as cursor:
            # Check current indexes
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename LIKE '%student%'
                ORDER BY tablename, indexname;
            """)
            
            indexes = cursor.fetchall()
            self.stdout.write(f'Found {len(indexes)} indexes on student tables')
            
            # Check table sizes
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE tablename LIKE '%student%'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            
            table_sizes = cursor.fetchall()
            self.stdout.write('Table sizes:')
            for table in table_sizes:
                self.stdout.write(f'  {table[1]}: {table[2]}')
            
            # Check slow queries
            cursor.execute("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE query LIKE '%student%'
                ORDER BY mean_time DESC
                LIMIT 10;
            """)
            
            slow_queries = cursor.fetchall()
            if slow_queries:
                self.stdout.write('Slow queries:')
                for query in slow_queries:
                    self.stdout.write(f'  {query[0][:100]}... - {query[3]:.2f}ms avg')

    def create_indexes(self):
        """Create optimized indexes for student queries"""
        self.stdout.write('Creating optimized indexes...')
        
        indexes = [
            # Critical composite indexes
            {
                'name': 'idx_student_dept_year_section_status',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_dept_year_section_status 
                    ON students_student (department_id, year_of_study, section, status) 
                    WHERE status = 'ACTIVE';
                """
            },
            {
                'name': 'idx_student_program_year_status',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_program_year_status 
                    ON students_student (academic_program_id, year_of_study, status) 
                    WHERE status = 'ACTIVE';
                """
            },
            {
                'name': 'idx_student_roll_number_gin',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_roll_number_gin 
                    ON students_student USING gin (roll_number gin_trgm_ops);
                """
            },
            {
                'name': 'idx_student_fulltext_search',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_fulltext_search 
                    ON students_student USING gin (
                        to_tsvector('english', first_name || ' ' || last_name || ' ' || roll_number || ' ' || COALESCE(email, ''))
                    );
                """
            },
            {
                'name': 'idx_student_email_gin',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_email_gin 
                    ON students_student USING gin (email gin_trgm_ops) 
                    WHERE email IS NOT NULL;
                """
            },
            {
                'name': 'idx_student_academic_year_semester',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_academic_year_semester 
                    ON students_student (academic_year, semester, status) 
                    WHERE status = 'ACTIVE';
                """
            },
            {
                'name': 'idx_student_created_at_status',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_created_at_status 
                    ON students_student (created_at DESC, status) 
                    WHERE status = 'ACTIVE';
                """
            },
            {
                'name': 'idx_student_user_id',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_user_id 
                    ON students_student (user_id) 
                    WHERE user_id IS NOT NULL;
                """
            },
            {
                'name': 'idx_student_current_academic_semester',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_current_academic_semester 
                    ON students_student (current_academic_year_id, current_semester_id, status) 
                    WHERE status = 'ACTIVE';
                """
            },
            {
                'name': 'idx_student_active_only',
                'sql': """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_active_only 
                    ON students_student (department_id, academic_program_id, year_of_study, semester, section) 
                    WHERE status = 'ACTIVE';
                """
            }
        ]
        
        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    self.stdout.write(f'Creating index: {index["name"]}')
                    cursor.execute(index['sql'])
                    self.stdout.write(f'  ✓ Created successfully')
                except Exception as e:
                    self.stdout.write(f'  ✗ Error: {e}')

    def vacuum_tables(self):
        """Run VACUUM ANALYZE on student tables"""
        self.stdout.write('Running VACUUM ANALYZE on student tables...')
        
        tables = [
            'students_student',
            'students_studentenrollmenthistory',
            'students_studentdocument',
            'students_studentcustomfieldvalue',
            'students_customfield'
        ]
        
        with connection.cursor() as cursor:
            for table in tables:
                try:
                    self.stdout.write(f'VACUUM ANALYZE {table}...')
                    cursor.execute(f'VACUUM ANALYZE {table};')
                    self.stdout.write(f'  ✓ Completed')
                except Exception as e:
                    self.stdout.write(f'  ✗ Error: {e}')

    def optimize_settings(self):
        """Optimize database settings for high performance"""
        self.stdout.write('Optimizing database settings...')
        
        # These settings should be configured in postgresql.conf
        # This is just for reference
        recommended_settings = {
            'shared_preload_libraries': 'pg_stat_statements',
            'track_activities': 'on',
            'track_counts': 'on',
            'track_io_timing': 'on',
            'track_functions': 'all',
            'log_statement': 'all',
            'log_min_duration_statement': 1000,
            'random_page_cost': 1.1,
            'effective_cache_size': '4GB',
            'work_mem': '256MB',
            'maintenance_work_mem': '1GB',
            'checkpoint_completion_target': 0.9,
            'wal_buffers': '64MB',
            'default_statistics_target': 100,
            'effective_io_concurrency': 200,
        }
        
        self.stdout.write('Recommended PostgreSQL settings:')
        for setting, value in recommended_settings.items():
            self.stdout.write(f'  {setting} = {value}')
        
        self.stdout.write('\nNote: These settings should be configured in postgresql.conf and require a restart.')
