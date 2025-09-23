from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import (
    Student, StudentRepresentative, StudentRepresentativeType,
    AcademicYear, StudentBatch
)
from departments.models import Department
from academics.models import AcademicProgram
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample student representatives (CR, LR) for AP University'

    def add_arguments(self, parser):
        parser.add_argument(
            '--academic-year',
            type=str,
            default='2024-2025',
            help='Academic year for representatives'
        )
        parser.add_argument(
            '--semester',
            type=str,
            default='5',
            help='Semester for representatives'
        )
        parser.add_argument(
            '--department-code',
            type=str,
            default='CS',
            help='Department code for representatives'
        )

    def handle(self, *args, **options):
        academic_year_str = options['academic_year']
        semester = options['semester']
        dept_code = options['department_code']

        # Get or create academic year
        academic_year, created = AcademicYear.objects.get_or_create(
            year=academic_year_str,
            defaults={
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date().replace(year=timezone.now().year + 1),
                'is_current': True,
                'is_active': True
            }
        )

        # Get department
        try:
            department = Department.objects.get(code=dept_code)
        except Department.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Department with code {dept_code} not found')
            )
            return

        # Get academic program (first one for the department)
        academic_program = AcademicProgram.objects.filter(
            department=department
        ).first()

        if not academic_program:
            self.stdout.write(
                self.style.ERROR(f'No academic program found for department {dept_code}')
            )
            return

        # Get students for the department
        students = Student.objects.filter(
            student_batch__department=department,
            student_batch__academic_year=academic_year,
            student_batch__semester=semester,
            status='ACTIVE'
        ).select_related('student_batch')

        if not students.exists():
            self.stdout.write(
                self.style.ERROR(f'No students found for {dept_code} department')
            )
            return

        # Group students by year and section
        students_by_year_section = {}
        for student in students:
            batch = student.student_batch
            key = (batch.year_of_study, batch.section)
            if key not in students_by_year_section:
                students_by_year_section[key] = []
            students_by_year_section[key].append(student)

        created_count = 0

        # Create representatives for each year and section
        for (year, section), section_students in students_by_year_section.items():
            if len(section_students) < 2:
                continue

            # Create Class Representative (CR)
            cr_student = section_students[0]  # First student as CR
            cr_rep, cr_created = StudentRepresentative.objects.get_or_create(
                student=cr_student,
                representative_type=StudentRepresentativeType.CR,
                academic_year=academic_year,
                semester=semester,
                defaults={
                    'department': department,
                    'academic_program': academic_program,
                    'year_of_study': year,
                    'section': section,
                    'is_active': True,
                    'start_date': timezone.now().date(),
                    'responsibilities': 'Represent class in academic matters, coordinate with faculty, collect feedback from students',
                    'contact_email': cr_student.email,
                    'contact_phone': cr_student.student_mobile,
                    'notes': f'Class Representative for {department.name} - Year {year}, Section {section}'
                }
            )

            if cr_created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created CR: {cr_student.full_name} ({cr_student.roll_number}) - {department.name} Year {year} Section {section}'
                    )
                )

            # Create Ladies Representative (LR) - find a female student
            lr_student = None
            for student in section_students[1:]:  # Skip the CR
                if student.gender == 'F':
                    lr_student = student
                    break

            if lr_student:
                lr_rep, lr_created = StudentRepresentative.objects.get_or_create(
                    student=lr_student,
                    representative_type=StudentRepresentativeType.LR,
                    academic_year=academic_year,
                    semester=semester,
                    defaults={
                        'department': department,
                        'academic_program': academic_program,
                        'year_of_study': year,
                        'section': section,
                        'is_active': True,
                        'start_date': timezone.now().date(),
                        'responsibilities': 'Represent female students, address gender-specific issues, coordinate women-related activities',
                        'contact_email': lr_student.email,
                        'contact_phone': lr_student.student_mobile,
                        'notes': f'Ladies Representative for {department.name} - Year {year}, Section {section}'
                    }
                )

                if lr_created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created LR: {lr_student.full_name} ({lr_student.roll_number}) - {department.name} Year {year} Section {section}'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'No female student found for LR in {department.name} Year {year} Section {section}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} student representatives for {department.name} department'
            )
        )

        # Display summary
        total_cr = StudentRepresentative.objects.filter(
            representative_type=StudentRepresentativeType.CR,
            academic_year=academic_year,
            semester=semester,
            department=department,
            is_active=True
        ).count()

        total_lr = StudentRepresentative.objects.filter(
            representative_type=StudentRepresentativeType.LR,
            academic_year=academic_year,
            semester=semester,
            department=department,
            is_active=True
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Total active representatives for {department.name}: {total_cr} CR, {total_lr} LR'
            )
        )
