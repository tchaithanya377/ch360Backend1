from django.core.management.base import BaseCommand
from departments.models import Department


class Command(BaseCommand):
    help = 'Add missing departments that are shown in the old hardcoded choices'

    def handle(self, *args, **options):
        # Add the missing departments that were in the old hardcoded choices
        missing_departments = [
            {
                'name': 'Geography',
                'short_name': 'GEO',
                'code': 'GEO001',
                'department_type': 'ACADEMIC',
                'email': 'geography@university.edu',
                'phone': '+1234567899',
                'building': 'Arts Building',
                'floor': '3rd Floor',
                'room_number': 'A301',
                'established_date': '2020-01-01',
                'description': 'Department of Geography',
                'mission': 'To provide quality education in geography',
                'vision': 'To be a leading geography department',
            },
            {
                'name': 'Commerce',
                'short_name': 'COMM',
                'code': 'COMM001',
                'department_type': 'ACADEMIC',
                'email': 'commerce@university.edu',
                'phone': '+1234567900',
                'building': 'Commerce Building',
                'floor': '2nd Floor',
                'room_number': 'C201',
                'established_date': '2020-01-01',
                'description': 'Department of Commerce',
                'mission': 'To provide quality education in commerce',
                'vision': 'To be a leading commerce department',
            },
            {
                'name': 'Physical Education',
                'short_name': 'PE',
                'code': 'PE001',
                'department_type': 'ACADEMIC',
                'email': 'pe@university.edu',
                'phone': '+1234567901',
                'building': 'Sports Complex',
                'floor': 'Ground Floor',
                'room_number': 'SC001',
                'established_date': '2020-01-01',
                'description': 'Department of Physical Education',
                'mission': 'To provide quality education in physical education',
                'vision': 'To be a leading physical education department',
            },
            {
                'name': 'Arts',
                'short_name': 'ARTS',
                'code': 'ARTS001',
                'department_type': 'ACADEMIC',
                'email': 'arts@university.edu',
                'phone': '+1234567902',
                'building': 'Arts Building',
                'floor': '1st Floor',
                'room_number': 'A103',
                'established_date': '2020-01-01',
                'description': 'Department of Arts',
                'mission': 'To provide quality education in arts',
                'vision': 'To be a leading arts department',
            },
            {
                'name': 'Music',
                'short_name': 'MUSIC',
                'code': 'MUSIC001',
                'department_type': 'ACADEMIC',
                'email': 'music@university.edu',
                'phone': '+1234567903',
                'building': 'Arts Building',
                'floor': '2nd Floor',
                'room_number': 'A202',
                'established_date': '2020-01-01',
                'description': 'Department of Music',
                'mission': 'To provide quality education in music',
                'vision': 'To be a leading music department',
            },
        ]

        created_count = 0
        for dept_data in missing_departments:
            department, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created department: {department.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Department already exists: {department.name}')
                )

        # Also add an "Other" department for flexibility
        other_dept, created = Department.objects.get_or_create(
            code='OTHER001',
            defaults={
                'name': 'Other',
                'short_name': 'OTHER',
                'code': 'OTHER001',
                'department_type': 'ACADEMIC',
                'email': 'other@university.edu',
                'phone': '+1234567904',
                'building': 'General Building',
                'floor': 'Ground Floor',
                'room_number': 'G001',
                'established_date': '2020-01-01',
                'description': 'Other Department',
                'mission': 'To handle other academic areas',
                'vision': 'To be a flexible department for various academic areas',
            }
        )
        if created:
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created department: {other_dept.name}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new departments')
        )
        
        # Show all departments
        all_depts = Department.objects.filter(is_active=True, status='ACTIVE').order_by('name')
        self.stdout.write(f'\nAll active departments ({all_depts.count()}):')
        for dept in all_depts:
            self.stdout.write(f'  - {dept.name} ({dept.code})')
