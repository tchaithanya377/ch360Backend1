from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    Department, DepartmentResource, 
    DepartmentAnnouncement, DepartmentEvent, DepartmentDocument
)
from .serializers import (
    DepartmentSerializer, DepartmentListSerializer, DepartmentDetailSerializer,
    DepartmentResourceSerializer,
    DepartmentAnnouncementSerializer, DepartmentEventSerializer,
    DepartmentDocumentSerializer, DepartmentStatsSerializer,
    DepartmentSearchSerializer
)

User = get_user_model()


class DepartmentPagination(PageNumberPagination):
    """Custom pagination for department views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments with comprehensive CRUD operations
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    lookup_field = 'id'
    lookup_value_regex = r'[0-9a-fA-F-]{36}'
    pagination_class = DepartmentPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department_type', 'status', 'is_active', 'head_of_department']
    search_fields = ['name', 'short_name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at', 'current_faculty_count', 'current_student_count']
    ordering = ['name']
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        Public read for list, stats and retrieve to support unauthenticated discovery.
        Admin required for mutations.
        """
        if self.action in ['list', 'stats', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action in ['create']:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return DepartmentListSerializer
        elif self.action == 'retrieve':
            return DepartmentDetailSerializer
        return DepartmentSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not admin, filter based on their department access
        if not self.request.user.is_staff:
            # Users can only see departments they have access to
            if hasattr(self.request.user, 'faculty_profile'):
                faculty = self.request.user.faculty_profile
                if faculty.department_ref:
                    # Faculty can see their own department and sub-departments
                    queryset = queryset.filter(
                        Q(id=faculty.department_ref.id) |
                        Q(parent_department=faculty.department_ref)
                    )
            elif hasattr(self.request.user, 'student_profile'):
                student = self.request.user.student_profile
                if student.department:
                    # Students can see their own department
                    queryset = queryset.filter(id=student.department.id)
            else:
                # Regular users can only see active departments
                queryset = queryset.filter(is_active=True, status='ACTIVE')
        
        return queryset.select_related(
            'head_of_department', 'deputy_head', 'parent_department',
            'created_by', 'updated_by'
        ).prefetch_related(
            'resources', 'announcements', 'events', 'documents'
        )
    
    def perform_create(self, serializer):
        """Set created_by when creating a department"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by when updating a department"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def resources(self, request, pk=None):
        """Get all resources for a department"""
        department = self.get_object()
        resources = department.resources.all()
        serializer = DepartmentResourceSerializer(resources, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def announcements(self, request, pk=None):
        """Get all announcements for a department"""
        department = self.get_object()
        announcements = department.announcements.filter(is_published=True)
        serializer = DepartmentAnnouncementSerializer(announcements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get all events for a department"""
        department = self.get_object()
        events = department.events.filter(
            start_date__gte=timezone.now()
        ).order_by('start_date')
        serializer = DepartmentEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents for a department"""
        department = self.get_object()
        documents = department.documents.all()
        
        # Filter public documents for non-admin users
        if not request.user.is_staff:
            documents = documents.filter(is_public=True)
        
        serializer = DepartmentDocumentSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_counts(self, request, pk=None):
        """Update faculty and student counts for a department"""
        department = self.get_object()
        department.update_counts()
        serializer = self.get_serializer(department)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get department statistics"""
        stats = {
            'total_departments': Department.objects.count(),
            'active_departments': Department.objects.filter(is_active=True).count(),
            'academic_departments': Department.objects.filter(department_type='ACADEMIC').count(),
            'administrative_departments': Department.objects.filter(department_type='ADMINISTRATIVE').count(),
            'research_departments': Department.objects.filter(department_type='RESEARCH').count(),
            'total_faculty': Department.objects.aggregate(
                total=Sum('current_faculty_count')
            )['total'] or 0,
            'total_students': Department.objects.aggregate(
                total=Sum('current_student_count')
            )['total'] or 0,
            'total_resources': DepartmentResource.objects.count(),
            'upcoming_events': DepartmentEvent.objects.filter(
                start_date__gte=timezone.now()
            ).count(),
            'active_announcements': DepartmentAnnouncement.objects.filter(
                is_published=True
            ).count(),
        }
        serializer = DepartmentStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced search for departments"""
        serializer = DepartmentSearchSerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data.get('query', '')
            queryset = self.get_queryset()
            
            # Apply search filters
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) |
                    Q(short_name__icontains=query) |
                    Q(code__icontains=query) |
                    Q(description__icontains=query)
                )
            
            # Apply additional filters
            if serializer.validated_data.get('department_type'):
                queryset = queryset.filter(department_type=serializer.validated_data['department_type'])
            
            if serializer.validated_data.get('status'):
                queryset = queryset.filter(status=serializer.validated_data['status'])
            
            if serializer.validated_data.get('is_active') is not None:
                queryset = queryset.filter(is_active=serializer.validated_data['is_active'])
            
            if serializer.validated_data.get('has_head'):
                queryset = queryset.filter(head_of_department__isnull=False)
            
            if serializer.validated_data.get('min_faculty_count'):
                queryset = queryset.filter(current_faculty_count__gte=serializer.validated_data['min_faculty_count'])
            
            if serializer.validated_data.get('max_faculty_count'):
                queryset = queryset.filter(current_faculty_count__lte=serializer.validated_data['max_faculty_count'])
            
            if serializer.validated_data.get('min_student_count'):
                queryset = queryset.filter(current_student_count__gte=serializer.validated_data['min_student_count'])
            
            if serializer.validated_data.get('max_student_count'):
                queryset = queryset.filter(current_student_count__lte=serializer.validated_data['max_student_count'])
            
            # Paginate results
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = DepartmentListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = DepartmentListSerializer(queryset, many=True)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentResourceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing department resources"""
    queryset = DepartmentResource.objects.all()
    serializer_class = DepartmentResourceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'resource_type', 'status', 'responsible_person']
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'resource_type', 'purchase_date', 'cost']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]


class DepartmentAnnouncementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing department announcements"""
    queryset = DepartmentAnnouncement.objects.all()
    serializer_class = DepartmentAnnouncementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'announcement_type', 'priority', 'is_published', 'target_audience']
    search_fields = ['title', 'content']
    ordering_fields = ['title', 'publish_date', 'created_at', 'priority']
    ordering = ['-publish_date', '-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter announcements based on user permissions"""
        queryset = super().get_queryset()
        
        # Non-admin users can only see published announcements
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        return queryset.select_related('department', 'created_by')


class DepartmentEventViewSet(viewsets.ModelViewSet):
    """ViewSet for managing department events"""
    queryset = DepartmentEvent.objects.all()
    serializer_class = DepartmentEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'event_type', 'status', 'is_public', 'organizer']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['title', 'start_date', 'end_date', 'event_type']
    ordering = ['start_date']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter events based on user permissions"""
        queryset = super().get_queryset()
        
        # Non-admin users can only see public events
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)
        
        return queryset.select_related('department', 'organizer', 'created_by')


class DepartmentDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing department documents"""
    queryset = DepartmentDocument.objects.all()
    serializer_class = DepartmentDocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'document_type', 'is_public', 'uploaded_by']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'document_type', 'created_at', 'version']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter documents based on user permissions"""
        queryset = super().get_queryset()
        
        # Non-admin users can only see public documents
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)
        
        return queryset.select_related('department', 'uploaded_by')
    
    def get_serializer_context(self):
        """Add request to serializer context for file URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context