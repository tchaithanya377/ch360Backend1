"""
Django management command to warm up caches for high-performance student queries
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from students.cache_strategies import CacheWarmingService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Warm up caches for high-performance student queries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--statistics',
            action='store_true',
            help='Warm up statistics cache',
        )
        parser.add_argument(
            '--dashboard',
            action='store_true',
            help='Warm up dashboard metrics cache',
        )
        parser.add_argument(
            '--students',
            action='store_true',
            help='Warm up frequently accessed students cache',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Warm up all caches',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.warm_all_caches()
        else:
            if options['statistics']:
                self.warm_statistics_cache()
            if options['dashboard']:
                self.warm_dashboard_cache()
            if options['students']:
                self.warm_students_cache()

        self.stdout.write(
            self.style.SUCCESS('Cache warming completed successfully!')
        )

    def warm_all_caches(self):
        """Warm up all caches"""
        self.stdout.write('Warming up all caches...')
        CacheWarmingService.warm_all_caches()
        self.stdout.write('✓ All caches warmed up')

    def warm_statistics_cache(self):
        """Warm up statistics cache"""
        self.stdout.write('Warming up statistics cache...')
        CacheWarmingService.warm_student_statistics()
        self.stdout.write('✓ Statistics cache warmed up')

    def warm_dashboard_cache(self):
        """Warm up dashboard cache"""
        self.stdout.write('Warming up dashboard cache...')
        CacheWarmingService.warm_dashboard_metrics()
        self.stdout.write('✓ Dashboard cache warmed up')

    def warm_students_cache(self):
        """Warm up students cache"""
        self.stdout.write('Warming up students cache...')
        CacheWarmingService.warm_frequently_accessed_students()
        self.stdout.write('✓ Students cache warmed up')
