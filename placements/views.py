from rest_framework import viewsets, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer,
    PlacementStatistics, CompanyFeedback, PlacementDocument, AlumniPlacement
)
from .serializers import (
    CompanySerializer, JobPostingSerializer, ApplicationSerializer, PlacementDriveSerializer,
    InterviewRoundSerializer, OfferSerializer, PlacementStatisticsSerializer,
    CompanyFeedbackSerializer, PlacementDocumentSerializer, AlumniPlacementSerializer
)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    class CompanyCursorPagination(CursorPagination):
        ordering = '-created_at'

    pagination_class = CompanyCursorPagination

    @action(detail=True, methods=['get'], url_path='statistics')
    def company_statistics(self, request, pk=None):
        """Get detailed statistics for a company."""
        company = self.get_object()
        
        # Get placement statistics
        total_drives = company.drives.count()
        total_applications = Application.objects.filter(job__company=company).count()
        total_offers = Offer.objects.filter(application__job__company=company).count()
        total_hired = Offer.objects.filter(
            application__job__company=company,
            status='ACCEPTED'
        ).count()
        
        # Calculate conversion rates
        conversion_rate = (total_hired / total_applications * 100) if total_applications > 0 else 0
        
        # Get average salary
        avg_salary = Offer.objects.filter(
            application__job__company=company,
            status='ACCEPTED'
        ).aggregate(avg_salary=Avg('package_annual_ctc'))['avg_salary'] or 0
        
        # Get feedback statistics
        feedbacks = CompanyFeedback.objects.filter(company=company)
        avg_rating = feedbacks.aggregate(avg_rating=Avg('overall_rating'))['avg_rating'] or 0
        
        return Response({
            'company': CompanySerializer(company).data,
            'statistics': {
                'total_drives': total_drives,
                'total_applications': total_applications,
                'total_offers': total_offers,
                'total_hired': total_hired,
                'conversion_rate': round(conversion_rate, 2),
                'average_salary': float(avg_salary),
                'average_rating': round(avg_rating, 2),
                'total_feedbacks': feedbacks.count()
            }
        })


class JobPostingViewSet(viewsets.ModelViewSet):
    queryset = JobPosting.objects.select_related('company', 'posted_by').all()
    serializer_class = JobPostingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

    @action(detail=True, methods=['get'], url_path='applications')
    def list_applications(self, request, pk=None):
        job = self.get_object()
        qs = job.applications.select_related('student').all()
        serializer = ApplicationSerializer(qs, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.select_related('student', 'job', 'job__company').all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

class PlacementDriveViewSet(viewsets.ModelViewSet):
    queryset = PlacementDrive.objects.select_related('company').all()
    serializer_class = PlacementDriveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InterviewRoundViewSet(viewsets.ModelViewSet):
    queryset = InterviewRound.objects.select_related('drive').all()
    serializer_class = InterviewRoundSerializer
    permission_classes = [permissions.IsAuthenticated]


class OfferViewSet(viewsets.ModelViewSet):
    queryset = Offer.objects.select_related('application', 'application__student', 'application__job', 'application__job__company').all()
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]


class PlacementStatisticsViewSet(viewsets.ModelViewSet):
    queryset = PlacementStatistics.objects.select_related('department', 'program').all()
    serializer_class = PlacementStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='overview')
    def placement_overview(self, request):
        """Get overall placement statistics for the institution."""
        current_year = timezone.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        # Get overall statistics
        stats = PlacementStatistics.objects.filter(academic_year=academic_year)
        
        total_students = stats.aggregate(total=Sum('total_students'))['total'] or 0
        total_placed = stats.aggregate(total=Sum('placed_students'))['total'] or 0
        total_companies = stats.aggregate(total=Sum('total_companies_visited'))['total'] or 0
        total_offers = stats.aggregate(total=Sum('total_job_offers'))['total'] or 0
        
        # Calculate overall placement percentage
        placement_percentage = (total_placed / total_students * 100) if total_students > 0 else 0
        
        # Get salary statistics
        salary_stats = stats.aggregate(
            avg_salary=Avg('average_salary'),
            highest_salary=Sum('highest_salary'),
            lowest_salary=Sum('lowest_salary')
        )
        
        return Response({
            'academic_year': academic_year,
            'overview': {
                'total_students': total_students,
                'total_placed': total_placed,
                'placement_percentage': round(placement_percentage, 2),
                'total_companies_visited': total_companies,
                'total_job_offers': total_offers,
                'average_salary': float(salary_stats['avg_salary'] or 0),
                'highest_salary': float(salary_stats['highest_salary'] or 0),
                'lowest_salary': float(salary_stats['lowest_salary'] or 0)
            },
            'department_wise': PlacementStatisticsSerializer(stats, many=True).data
        })


class CompanyFeedbackViewSet(viewsets.ModelViewSet):
    queryset = CompanyFeedback.objects.select_related('company', 'drive').all()
    serializer_class = CompanyFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]


class PlacementDocumentViewSet(viewsets.ModelViewSet):
    queryset = PlacementDocument.objects.select_related('company', 'student', 'drive', 'created_by').all()
    serializer_class = PlacementDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AlumniPlacementViewSet(viewsets.ModelViewSet):
    queryset = AlumniPlacement.objects.select_related('student').all()
    serializer_class = AlumniPlacementSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='alumni-network')
    def alumni_network(self, request):
        """Get alumni network statistics and willing mentors/recruiters."""
        alumni = AlumniPlacement.objects.all()
        
        # Get statistics
        total_alumni = alumni.count()
        willing_mentors = alumni.filter(willing_to_mentor=True).count()
        willing_recruiters = alumni.filter(willing_to_recruit=True).count()
        entrepreneurs = alumni.filter(is_entrepreneur=True).count()
        higher_studies = alumni.filter(pursuing_higher_studies=True).count()
        
        # Get top companies where alumni work
        top_companies = alumni.values('current_company').annotate(
            count=Count('current_company')
        ).order_by('-count')[:10]
        
        return Response({
            'statistics': {
                'total_alumni': total_alumni,
                'willing_mentors': willing_mentors,
                'willing_recruiters': willing_recruiters,
                'entrepreneurs': entrepreneurs,
                'pursuing_higher_studies': higher_studies
            },
            'top_companies': list(top_companies),
            'alumni_list': AlumniPlacementSerializer(alumni, many=True).data
        })


class PlacementAnalyticsViewSet(viewsets.ViewSet):
    """Analytics and reporting endpoints for placement data."""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='trends')
    def placement_trends(self, request):
        """Get placement trends over the years."""
        years = request.query_params.getlist('years', [])
        
        if not years:
            # Default to last 5 years
            current_year = timezone.now().year
            years = [f"{year}-{year + 1}" for year in range(current_year - 4, current_year + 1)]
        
        trends = []
        for year in years:
            stats = PlacementStatistics.objects.filter(academic_year=year)
            if stats.exists():
                year_data = stats.aggregate(
                    total_students=Sum('total_students'),
                    placed_students=Sum('placed_students'),
                    avg_salary=Avg('average_salary'),
                    companies_visited=Sum('total_companies_visited')
                )
                
                placement_percentage = (
                    year_data['placed_students'] / year_data['total_students'] * 100
                ) if year_data['total_students'] else 0
                
                trends.append({
                    'academic_year': year,
                    'total_students': year_data['total_students'] or 0,
                    'placed_students': year_data['placed_students'] or 0,
                    'placement_percentage': round(placement_percentage, 2),
                    'average_salary': float(year_data['avg_salary'] or 0),
                    'companies_visited': year_data['companies_visited'] or 0
                })
        
        return Response({'trends': trends})

    @action(detail=False, methods=['get'], url_path='nirf-report')
    def nirf_report(self, request):
        """Generate NIRF compliance report for placements."""
        current_year = timezone.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        stats = PlacementStatistics.objects.filter(academic_year=academic_year)
        
        # Calculate NIRF metrics
        total_students = stats.aggregate(total=Sum('total_students'))['total'] or 0
        placed_students = stats.aggregate(total=Sum('placed_students'))['total'] or 0
        higher_studies = stats.aggregate(total=Sum('students_higher_studies'))['total'] or 0
        entrepreneurs = stats.aggregate(total=Sum('students_entrepreneurship'))['total'] or 0
        
        # Calculate placement percentage (NIRF metric)
        placement_percentage = (placed_students / total_students * 100) if total_students > 0 else 0
        
        # Calculate higher studies percentage
        higher_studies_percentage = (higher_studies / total_students * 100) if total_students > 0 else 0
        
        # Calculate entrepreneurship percentage
        entrepreneurship_percentage = (entrepreneurs / total_students * 100) if total_students > 0 else 0
        
        return Response({
            'academic_year': academic_year,
            'nirf_metrics': {
                'total_students': total_students,
                'placed_students': placed_students,
                'placement_percentage': round(placement_percentage, 2),
                'students_higher_studies': higher_studies,
                'higher_studies_percentage': round(higher_studies_percentage, 2),
                'entrepreneurs': entrepreneurs,
                'entrepreneurship_percentage': round(entrepreneurship_percentage, 2)
            },
            'department_wise_data': PlacementStatisticsSerializer(stats, many=True).data
        })

