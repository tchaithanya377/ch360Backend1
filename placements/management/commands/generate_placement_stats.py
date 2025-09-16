from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from placements.models import PlacementStatistics, Offer, PlacementDrive
from students.models import Student
from departments.models import Department
from academics.models import AcademicProgram


class Command(BaseCommand):
    help = 'Generate placement statistics for NIRF compliance and reporting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--academic-year',
            type=str,
            help='Academic year to generate statistics for (e.g., 2024-2025)',
        )
        parser.add_argument(
            '--department',
            type=str,
            help='Department ID to generate statistics for specific department',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing statistics',
        )

    def handle(self, *args, **options):
        academic_year = options.get('academic_year')
        department_id = options.get('department')
        force = options.get('force', False)

        if not academic_year:
            current_year = timezone.now().year
            academic_year = f"{current_year}-{current_year + 1}"

        self.stdout.write(f"Generating placement statistics for academic year: {academic_year}")

        # Get departments to process
        if department_id:
            departments = Department.objects.filter(id=department_id)
        else:
            departments = Department.objects.all()

        total_stats_created = 0
        total_stats_updated = 0

        for department in departments:
            self.stdout.write(f"Processing department: {department.name}")
            
            # Get all programs in this department
            programs = AcademicProgram.objects.filter(department=department)
            
            for program in programs:
                # Check if statistics already exist
                stats, created = PlacementStatistics.objects.get_or_create(
                    academic_year=academic_year,
                    department=department,
                    program=program,
                    defaults={
                        'total_students': 0,
                        'eligible_students': 0,
                        'placed_students': 0,
                        'placement_percentage': 0.00,
                        'average_salary': 0.00,
                        'highest_salary': 0.00,
                        'lowest_salary': 0.00,
                        'total_companies_visited': 0,
                        'total_job_offers': 0,
                        'students_higher_studies': 0,
                        'students_entrepreneurship': 0
                    }
                )

                if created:
                    total_stats_created += 1
                    self.stdout.write(f"  Created statistics for {program.name}")
                elif force:
                    total_stats_updated += 1
                    self.stdout.write(f"  Updating statistics for {program.name}")

                # Calculate student counts
                total_students = Student.objects.filter(
                    enrollment__department=department,
                    enrollment__program=program
                ).count()

                # Calculate placed students (those with accepted offers)
                placed_students = Offer.objects.filter(
                    application__student__enrollment__department=department,
                    application__student__enrollment__program=program,
                    status='ACCEPTED'
                ).count()

                # Calculate salary statistics
                salary_stats = Offer.objects.filter(
                    application__student__enrollment__department=department,
                    application__student__enrollment__program=program,
                    status='ACCEPTED'
                ).aggregate(
                    avg_salary=Avg('package_annual_ctc'),
                    max_salary=Sum('package_annual_ctc'),
                    min_salary=Sum('package_annual_ctc')
                )

                # Calculate company visits
                companies_visited = PlacementDrive.objects.filter(
                    eligible_departments=department,
                    eligible_programs=program
                ).values('company').distinct().count()

                # Calculate total job offers
                total_offers = Offer.objects.filter(
                    application__student__enrollment__department=department,
                    application__student__enrollment__program=program
                ).count()

                # Update statistics
                stats.total_students = total_students
                stats.eligible_students = total_students  # Assuming all students are eligible
                stats.placed_students = placed_students
                stats.placement_percentage = (placed_students / total_students * 100) if total_students > 0 else 0
                stats.average_salary = salary_stats['avg_salary'] or 0
                stats.highest_salary = salary_stats['max_salary'] or 0
                stats.lowest_salary = salary_stats['min_salary'] or 0
                stats.total_companies_visited = companies_visited
                stats.total_job_offers = total_offers

                stats.save()

                self.stdout.write(
                    f"    Total Students: {total_students}, "
                    f"Placed: {placed_students}, "
                    f"Placement %: {stats.placement_percentage:.2f}%, "
                    f"Avg Salary: ₹{stats.average_salary:,.2f}"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated placement statistics. "
                f"Created: {total_stats_created}, Updated: {total_stats_updated}"
            )
        )
