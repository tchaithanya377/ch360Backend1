from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count, Avg, Sum
from .models import (
    Company, JobPosting, Application, PlacementDrive, Offer,
    PlacementStatistics, CompanyFeedback
)
from students.models import Student
from departments.models import Department
from academics.models import AcademicProgram


@receiver(post_save, sender=Offer)
def update_company_statistics_on_offer(sender, instance, created, **kwargs):
    """Update company statistics when an offer is created or updated."""
    if instance.status == 'ACCEPTED':
        company = instance.application.job.company
        company.total_placements = Offer.objects.filter(
            application__job__company=company,
            status='ACCEPTED'
        ).count()
        company.save(update_fields=['total_placements'])


@receiver(post_save, sender=PlacementDrive)
def update_company_drive_count(sender, instance, created, **kwargs):
    """Update company drive count when a placement drive is created."""
    if created:
        company = instance.company
        company.total_drives = PlacementDrive.objects.filter(company=company).count()
        company.last_visit_date = instance.start_date
        company.save(update_fields=['total_drives', 'last_visit_date'])


@receiver(post_save, sender=CompanyFeedback)
def update_company_rating(sender, instance, created, **kwargs):
    """Update company rating based on feedback."""
    company = instance.company
    feedbacks = CompanyFeedback.objects.filter(company=company)
    
    if feedbacks.exists():
        avg_rating = feedbacks.aggregate(avg_rating=Avg('overall_rating'))['avg_rating']
        company.rating = round(avg_rating, 2)
        company.save(update_fields=['rating'])


@receiver(post_save, sender=Offer)
def update_placement_statistics(sender, instance, created, **kwargs):
    """Update placement statistics when offers are created/updated."""
    if instance.status == 'ACCEPTED':
        student = instance.application.student
        if hasattr(student, 'enrollment') and student.enrollment:
            department = student.enrollment.department
            program = student.enrollment.program
            
            # Get current academic year
            from django.utils import timezone
            current_year = timezone.now().year
            academic_year = f"{current_year}-{current_year + 1}"
            
            # Get or create placement statistics
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
            
            # Update statistics
            stats.placed_students = Offer.objects.filter(
                application__student__enrollment__department=department,
                application__student__enrollment__program=program,
                status='ACCEPTED'
            ).count()
            
            # Calculate placement percentage
            if stats.total_students > 0:
                stats.placement_percentage = (stats.placed_students / stats.total_students) * 100
            
            # Update salary statistics
            salary_stats = Offer.objects.filter(
                application__student__enrollment__department=department,
                application__student__enrollment__program=program,
                status='ACCEPTED'
            ).aggregate(
                avg_salary=Avg('package_annual_ctc'),
                max_salary=Sum('package_annual_ctc'),
                min_salary=Sum('package_annual_ctc')
            )
            
            stats.average_salary = salary_stats['avg_salary'] or 0
            stats.highest_salary = salary_stats['max_salary'] or 0
            stats.lowest_salary = salary_stats['min_salary'] or 0
            
            stats.save()
