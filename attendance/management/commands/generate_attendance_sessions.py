from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from academics.models import Timetable
from attendance.models import AttendanceSession


class Command(BaseCommand):
    help = 'Generate AttendanceSession entries from Timetable for a given date range.'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=str, required=True, help='Start date YYYY-MM-DD')
        parser.add_argument('--end', type=str, required=True, help='End date YYYY-MM-DD')
        parser.add_argument('--section-id', type=int, help='Optional CourseSection ID to limit generation')

    def handle(self, *args, **options):
        start = date.fromisoformat(options['start'])
        end = date.fromisoformat(options['end'])
        section_id = options.get('section_id')

        if end < start:
            self.stderr.write('End date must be after start date')
            return

        days_map = {
            'MON': 0,
            'TUE': 1,
            'WED': 2,
            'THU': 3,
            'FRI': 4,
            'SAT': 5,
            'SUN': 6,
        }

        timetables = Timetable.objects.filter(is_active=True)
        if section_id:
            timetables = timetables.filter(course_section_id=section_id)

        by_weekday = {}
        for t in timetables.select_related('course_section'):
            by_weekday.setdefault(days_map[t.day_of_week], []).append(t)

        created_count = 0
        with transaction.atomic():
            current = start
            while current <= end:
                weekday = current.weekday()
                for t in by_weekday.get(weekday, []):
                    session, created = AttendanceSession.objects.get_or_create(
                        course_section=t.course_section,
                        date=current,
                        start_time=t.start_time,
                        defaults={
                            'end_time': t.end_time,
                            'room': t.room,
                            'timetable': t,
                        }
                    )
                    if created:
                        created_count += 1
                current += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f'Created {created_count} attendance sessions.'))

