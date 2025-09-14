from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Company, JobPosting, Application, PlacementDrive, InterviewRound, Offer
from .serializers import CompanySerializer, JobPostingSerializer, ApplicationSerializer, PlacementDriveSerializer, InterviewRoundSerializer, OfferSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]


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

