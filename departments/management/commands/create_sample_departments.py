from django.core.management.base import BaseCommand
from departments.models import Department


class Command(BaseCommand):
    help = 'Create sample departments for testing'

    def handle(self, *args, **options):
        departments_data = [
            {
                'name': 'Computer Science',
                'short_name': 'CS',
                'code': 'CS001',
                'department_type': 'ACADEMIC',
                'email': 'cs@university.edu',
                'phone': '+1234567890',
                'building': 'Engineering Building',
                'floor': '2nd Floor',
                'room_number': 'E201',
                'established_date': '2020-01-01',
                'description': 'Department of Computer Science and Engineering',
                'mission': 'To provide quality education in computer science',
                'vision': 'To be a leading computer science department',
            },
            {
                'name': 'Mathematics',
                'short_name': 'MATH',
                'code': 'MATH001',
                'department_type': 'ACADEMIC',
                'email': 'math@university.edu',
                'phone': '+1234567891',
                'building': 'Science Building',
                'floor': '1st Floor',
                'room_number': 'S101',
                'established_date': '2020-01-01',
                'description': 'Department of Mathematics',
                'mission': 'To provide quality education in mathematics',
                'vision': 'To be a leading mathematics department',
            },
            {
                'name': 'Physics',
                'short_name': 'PHY',
                'code': 'PHY001',
                'department_type': 'ACADEMIC',
                'email': 'physics@university.edu',
                'phone': '+1234567892',
                'building': 'Science Building',
                'floor': '2nd Floor',
                'room_number': 'S201',
                'established_date': '2020-01-01',
                'description': 'Department of Physics',
                'mission': 'To provide quality education in physics',
                'vision': 'To be a leading physics department',
            },
            {
                'name': 'Chemistry',
                'short_name': 'CHEM',
                'code': 'CHEM001',
                'department_type': 'ACADEMIC',
                'email': 'chemistry@university.edu',
                'phone': '+1234567893',
                'building': 'Science Building',
                'floor': '3rd Floor',
                'room_number': 'S301',
                'established_date': '2020-01-01',
                'description': 'Department of Chemistry',
                'mission': 'To provide quality education in chemistry',
                'vision': 'To be a leading chemistry department',
            },
            {
                'name': 'Biology',
                'short_name': 'BIO',
                'code': 'BIO001',
                'department_type': 'ACADEMIC',
                'email': 'biology@university.edu',
                'phone': '+1234567894',
                'building': 'Science Building',
                'floor': '1st Floor',
                'room_number': 'S102',
                'established_date': '2020-01-01',
                'description': 'Department of Biology',
                'mission': 'To provide quality education in biology',
                'vision': 'To be a leading biology department',
            },
            {
                'name': 'English',
                'short_name': 'ENG',
                'code': 'ENG001',
                'department_type': 'ACADEMIC',
                'email': 'english@university.edu',
                'phone': '+1234567895',
                'building': 'Arts Building',
                'floor': '1st Floor',
                'room_number': 'A101',
                'established_date': '2020-01-01',
                'description': 'Department of English',
                'mission': 'To provide quality education in English',
                'vision': 'To be a leading English department',
            },
            {
                'name': 'History',
                'short_name': 'HIST',
                'code': 'HIST001',
                'department_type': 'ACADEMIC',
                'email': 'history@university.edu',
                'phone': '+1234567896',
                'building': 'Arts Building',
                'floor': '2nd Floor',
                'room_number': 'A201',
                'established_date': '2020-01-01',
                'description': 'Department of History',
                'mission': 'To provide quality education in history',
                'vision': 'To be a leading history department',
            },
            {
                'name': 'Economics',
                'short_name': 'ECON',
                'code': 'ECON001',
                'department_type': 'ACADEMIC',
                'email': 'economics@university.edu',
                'phone': '+1234567897',
                'building': 'Commerce Building',
                'floor': '1st Floor',
                'room_number': 'C101',
                'established_date': '2020-01-01',
                'description': 'Department of Economics',
                'mission': 'To provide quality education in economics',
                'vision': 'To be a leading economics department',
            },
            {
                'name': 'Administration',
                'short_name': 'ADMIN',
                'code': 'ADMIN001',
                'department_type': 'ADMINISTRATIVE',
                'email': 'admin@university.edu',
                'phone': '+1234567898',
                'building': 'Administrative Building',
                'floor': 'Ground Floor',
                'room_number': 'ADM001',
                'established_date': '2020-01-01',
                'description': 'Administrative Department',
                'mission': 'To provide administrative support',
                'vision': 'To be an efficient administrative department',
            },
        ]

        created_count = 0
        for dept_data in departments_data:
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

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new departments')
        )
