from rest_framework import viewsets, permissions, filters, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import date, timedelta
import json

from . import models, serializers


class DefaultPermissions(permissions.IsAuthenticated):
    pass


class ResearcherViewSet(viewsets.ModelViewSet):
    queryset = models.Researcher.objects.all().select_related('user')
    serializer_class = serializers.ResearcherSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'department', 'orcid']
    ordering = ['department', 'title']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.ResearcherDetailSerializer
        return serializers.ResearcherSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get researcher statistics"""
        stats = {
            'by_department': dict(models.Researcher.objects.values_list('department').annotate(count=Count('id'))),
            'publication_stats': {
                'total_publications': models.Publication.objects.count(),
                'avg_per_researcher': models.Publication.objects.count() / max(models.Researcher.objects.count(), 1)
            },
            'project_participation': {
                'total_projects': models.Project.objects.count(),
                'researchers_with_projects': models.Researcher.objects.filter(projects__isnull=False).distinct().count()
            }
        }
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for researchers"""
        query = request.query_params.get('q', '')
        department = request.query_params.get('department', '')
        has_publications = request.query_params.get('has_publications', '')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(department__icontains=query)
            )
        
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        if has_publications == 'true':
            queryset = queryset.filter(publications__isnull=False).distinct()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GrantViewSet(viewsets.ModelViewSet):
    queryset = models.Grant.objects.all()
    serializer_class = serializers.GrantSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['start_date', 'end_date']
    search_fields = ['title', 'sponsor', 'reference_code']
    ordering = ['-start_date']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get grant statistics"""
        stats = {
            'total_grants': models.Grant.objects.count(),
            'total_amount': models.Grant.objects.aggregate(total=Sum('amount'))['total'] or 0,
            'by_sponsor': dict(models.Grant.objects.values_list('sponsor').annotate(count=Count('id'))),
            'by_year': dict(models.Grant.objects.filter(start_date__isnull=False).values_list('start_date__year').annotate(count=Count('id')))
        }
        return Response(stats)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all().select_related('principal_investigator').prefetch_related('members', 'grants')
    serializer_class = serializers.ProjectSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'start_date', 'end_date']
    search_fields = ['title', 'abstract', 'keywords']
    ordering = ['-start_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.ProjectDetailSerializer
        return serializers.ProjectSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get project statistics"""
        stats = {
            'total_projects': models.Project.objects.count(),
            'by_status': dict(models.Project.objects.values_list('status').annotate(count=Count('id'))),
            'by_department': dict(models.Project.objects.values_list('principal_investigator__department').annotate(count=Count('id'))),
            'active_projects': models.Project.objects.filter(status='active').count(),
            'completed_projects': models.Project.objects.filter(status='completed').count()
        }
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for projects"""
        query = request.query_params.get('q', '')
        status_filter = request.query_params.get('status', '')
        department = request.query_params.get('department', '')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query) |
                Q(keywords__contains=[query])
            )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if department:
            queryset = queryset.filter(principal_investigator__department__icontains=department)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = models.Publication.objects.all().prefetch_related('authors', 'projects')
    serializer_class = serializers.PublicationSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['publication_type', 'year']
    search_fields = ['title', 'venue', 'doi']
    ordering = ['-year', 'title']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get publication statistics"""
        stats = {
            'total_publications': models.Publication.objects.count(),
            'by_type': dict(models.Publication.objects.values_list('publication_type').annotate(count=Count('id'))),
            'by_year': dict(models.Publication.objects.filter(year__isnull=False).values_list('year').annotate(count=Count('id'))),
            'by_venue': dict(models.Publication.objects.values_list('venue').annotate(count=Count('id'))[:10])
        }
        return Response(stats)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search for publications"""
        query = request.query_params.get('q', '')
        pub_type = request.query_params.get('publication_type', '')
        year = request.query_params.get('year', '')
        
        queryset = self.get_queryset()
        
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(venue__icontains=query) |
                Q(doi__icontains=query)
            )
        
        if pub_type:
            queryset = queryset.filter(publication_type=pub_type)
        
        if year:
            queryset = queryset.filter(year=int(year))
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PatentViewSet(viewsets.ModelViewSet):
    queryset = models.Patent.objects.all().prefetch_related('inventors', 'projects')
    serializer_class = serializers.PatentSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['filing_date', 'grant_date']
    search_fields = ['title', 'application_number', 'grant_number']
    ordering = ['-filing_date']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get patent statistics"""
        stats = {
            'total_patents': models.Patent.objects.count(),
            'by_year': dict(models.Patent.objects.filter(filing_date__isnull=False).values_list('filing_date__year').annotate(count=Count('id'))),
            'by_inventor': dict(models.Patent.objects.values_list('inventors__user__last_name').annotate(count=Count('id'))[:10])
        }
        return Response(stats)


class DatasetViewSet(viewsets.ModelViewSet):
    queryset = models.Dataset.objects.all().prefetch_related('projects')
    serializer_class = serializers.DatasetSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public']
    search_fields = ['name', 'description']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dataset statistics"""
        stats = {
            'total_datasets': models.Dataset.objects.count(),
            'public_datasets': models.Dataset.objects.filter(is_public=True).count(),
            'private_datasets': models.Dataset.objects.filter(is_public=False).count(),
            'by_project': dict(models.Dataset.objects.values_list('projects__title').annotate(count=Count('id'))[:10])
        }
        return Response(stats)


class CollaborationViewSet(viewsets.ModelViewSet):
    queryset = models.Collaboration.objects.all().select_related('project')
    serializer_class = serializers.CollaborationSerializer
    permission_classes = [DefaultPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['start_date', 'end_date']
    search_fields = ['partner_institution', 'contact_person']
    ordering = ['-start_date']

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get collaboration statistics"""
        stats = {
            'total_collaborations': models.Collaboration.objects.count(),
            'by_institution': dict(models.Collaboration.objects.values_list('partner_institution').annotate(count=Count('id'))),
            'by_project': dict(models.Collaboration.objects.values_list('project__title').annotate(count=Count('id'))[:10])
        }
        return Response(stats)


# Dashboard Statistics View
class DashboardStatsView(views.APIView):
    permission_classes = [DefaultPermissions]
    
    def get(self, request):
        """Get comprehensive dashboard statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_researchers': models.Researcher.objects.count(),
            'total_projects': models.Project.objects.count(),
            'total_grants': models.Grant.objects.count(),
            'total_publications': models.Publication.objects.count(),
            'total_patents': models.Patent.objects.count(),
            'total_datasets': models.Dataset.objects.count(),
            'total_collaborations': models.Collaboration.objects.count(),
            'active_projects': models.Project.objects.filter(status='active').count(),
            'completed_projects': models.Project.objects.filter(status='completed').count(),
            'total_grant_amount': models.Grant.objects.aggregate(total=Sum('amount'))['total'] or 0,
            'recent_activities': {
                'new_projects': models.Project.objects.filter(start_date__gte=today - timedelta(days=30)).count(),
                'new_publications': models.Publication.objects.filter(year=today.year).count(),
                'new_grants': models.Grant.objects.filter(start_date__gte=today - timedelta(days=30)).count()
            }
        }
        
        return Response(stats)


# Search and Filter View
class SearchFilterView(views.APIView):
    permission_classes = [DefaultPermissions]
    
    def get(self, request):
        """Search across all R&D models"""
        query = request.query_params.get('q', '')
        model_type = request.query_params.get('model_type', '')
        
        if not query:
            return Response({'error': 'Query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        results = {}
        
        if not model_type or model_type == 'researcher':
            researchers = models.Researcher.objects.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(department__icontains=query)
            )[:10]
            results['researchers'] = serializers.ResearcherSerializer(researchers, many=True).data
        
        if not model_type or model_type == 'project':
            projects = models.Project.objects.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query)
            )[:10]
            results['projects'] = serializers.ProjectSerializer(projects, many=True).data
        
        if not model_type or model_type == 'publication':
            publications = models.Publication.objects.filter(
                Q(title__icontains=query) |
                Q(venue__icontains=query)
            )[:10]
            results['publications'] = serializers.PublicationSerializer(publications, many=True).data
        
        return Response(results)


# Bulk Operations View
class BulkOperationsView(views.APIView):
    permission_classes = [DefaultPermissions]
    
    def post(self, request):
        """Handle bulk operations"""
        operation_type = request.data.get('operation_type')
        model_type = request.data.get('model_type')
        data = request.data.get('data', [])
        
        if not all([operation_type, model_type, data]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
        
        model_map = {
            'researcher': models.Researcher,
            'project': models.Project,
            'publication': models.Publication,
            'patent': models.Patent,
            'dataset': models.Dataset,
            'collaboration': models.Collaboration
        }
        
        if model_type not in model_map:
            return Response({'error': 'Invalid model type'}, status=status.HTTP_400_BAD_REQUEST)
        
        model_class = model_map[model_type]
        
        if operation_type == 'create':
            serializer_class = getattr(serializers, f'{model_type.capitalize()}Serializer')
            created_objects = []
            
            for item_data in data:
                serializer = serializer_class(data=item_data)
                if serializer.is_valid():
                    obj = serializer.save()
                    created_objects.append(obj)
            
            return Response({
                'message': f'Created {len(created_objects)} {model_type}s',
                'created_count': len(created_objects)
            })
        
        elif operation_type == 'update':
            updated_count = 0
            for item_data in data:
                obj_id = item_data.get('id')
                if obj_id:
                    try:
                        obj = model_class.objects.get(id=obj_id)
                        for field, value in item_data.items():
                            if field != 'id' and hasattr(obj, field):
                                setattr(obj, field, value)
                        obj.save()
                        updated_count += 1
                    except model_class.DoesNotExist:
                        continue
            
            return Response({
                'message': f'Updated {updated_count} {model_type}s',
                'updated_count': updated_count
            })
        
        elif operation_type == 'delete':
            obj_ids = data
            deleted_count = 0
            
            for obj_id in obj_ids:
                try:
                    obj = model_class.objects.get(id=obj_id)
                    obj.delete()
                    deleted_count += 1
                except model_class.DoesNotExist:
                    continue
            
            return Response({
                'message': f'Deleted {deleted_count} {model_type}s',
                'deleted_count': deleted_count
            })
        
        return Response({'error': 'Invalid operation type'}, status=status.HTTP_400_BAD_REQUEST)


# Import/Export View
class ImportExportView(views.APIView):
    permission_classes = [DefaultPermissions]
    
    def post(self, request):
        """Handle data import/export"""
        operation = request.data.get('operation')
        model_type = request.data.get('model_type')
        format_type = request.data.get('format')
        
        if not all([operation, model_type, format_type]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)
        
        model_map = {
            'researcher': models.Researcher,
            'project': models.Project,
            'publication': models.Publication,
            'patent': models.Patent,
            'dataset': models.Dataset,
            'collaboration': models.Collaboration
        }
        
        if model_type not in model_map:
            return Response({'error': 'Invalid model type'}, status=status.HTTP_400_BAD_REQUEST)
        
        model_class = model_map[model_type]
        
        if operation == 'export':
            queryset = model_class.objects.all()
            serializer_class = getattr(serializers, f'{model_type.capitalize()}Serializer')
            serializer = serializer_class(queryset, many=True)
            
            return Response({
                'message': f'Exported {queryset.count()} {model_type}s',
                'data': serializer.data,
                'format': format_type
            })
        
        elif operation == 'import':
            data = request.data.get('data', [])
            if not data:
                return Response({'error': 'No data provided for import'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer_class = getattr(serializers, f'{model_type.capitalize()}Serializer')
            imported_count = 0
            
            for item_data in data:
                serializer = serializer_class(data=item_data)
                if serializer.is_valid():
                    serializer.save()
                    imported_count += 1
            
            return Response({
                'message': f'Imported {imported_count} {model_type}s',
                'imported_count': imported_count
            })
        
        return Response({'error': 'Invalid operation'}, status=status.HTTP_400_BAD_REQUEST)


# Alert System View
class AlertView(views.APIView):
    permission_classes = [DefaultPermissions]
    
    def get(self, request):
        """Get system alerts"""
        today = timezone.now().date()
        alerts = []
        
        # Project deadline alerts
        upcoming_deadlines = models.Project.objects.filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30)
        )
        
        for project in upcoming_deadlines:
            days_remaining = (project.end_date - today).days
            alerts.append({
                'type': 'deadline',
                'title': f'Project Deadline: {project.title}',
                'message': f'Project ends in {days_remaining} days',
                'severity': 'medium' if days_remaining > 7 else 'high',
                'related_object_type': 'project',
                'related_object_id': project.id,
                'due_date': project.end_date
            })
        
        # Grant deadline alerts
        upcoming_grant_deadlines = models.Grant.objects.filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30)
        )
        
        for grant in upcoming_grant_deadlines:
            days_remaining = (grant.end_date - today).days
            alerts.append({
                'type': 'deadline',
                'title': f'Grant Deadline: {grant.title}',
                'message': f'Grant ends in {days_remaining} days',
                'severity': 'medium' if days_remaining > 7 else 'high',
                'related_object_type': 'grant',
                'related_object_id': grant.id,
                'due_date': grant.end_date
            })
        
        return Response(alerts)


# Dashboard Widget View
class DashboardWidgetView(views.APIView):
    permission_classes = [DefaultPermissions]
    
    def get(self, request):
        """Get dashboard widget data"""
        widget_type = request.query_params.get('widget_type', 'stats')
        
        if widget_type == 'stats':
            data = {
                'total_researchers': models.Researcher.objects.count(),
                'total_projects': models.Project.objects.count(),
                'total_publications': models.Publication.objects.count(),
                'total_grants': models.Grant.objects.count()
            }
        elif widget_type == 'chart':
            # Project status chart
            project_status_data = dict(models.Project.objects.values_list('status').annotate(count=Count('id')))
            data = {
                'labels': list(project_status_data.keys()),
                'data': list(project_status_data.values())
            }
        elif widget_type == 'table':
            # Recent projects
            recent_projects = models.Project.objects.order_by('-start_date')[:5]
            data = serializers.ProjectSerializer(recent_projects, many=True).data
        else:
            data = {}
        
        return Response({
            'widget_type': widget_type,
            'data': data
        })


