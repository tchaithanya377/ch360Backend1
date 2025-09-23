"""
Core viewsets for CampusHub360
Shared base viewsets and utilities across all apps
"""

from django.core.cache import cache
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
import time
import logging

from .models import CustomField, CustomFieldValue, Document, Contact
from .serializers import (
    CustomFieldSerializer, CustomFieldValueSerializer, DocumentSerializer,
    ContactSerializer, BulkOperationSerializer, SearchSerializer,
    StatisticsSerializer, ExportSerializer, ImportSerializer
)

logger = logging.getLogger(__name__)


class BaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with common functionality
    All ViewSets should inherit from this
    """
    permission_classes = [IsAuthenticated]
    # Disable pagination at the viewset level so list endpoints return plain lists
    # Tests across the project expect non-paginated responses
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return self.get_list_serializer()
        elif self.action in ['retrieve', 'detail']:
            return self.get_detail_serializer()
        return self.serializer_class
    
    def get_list_serializer(self):
        """Override in subclasses to return list serializer"""
        return self.serializer_class
    
    def get_detail_serializer(self):
        """Override in subclasses to return detail serializer"""
        return self.serializer_class
    
    def get_queryset(self):
        """Override in subclasses to return optimized queryset"""
        return self.queryset
    
    def perform_create(self, serializer):
        """Set created_by field when creating"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by field when updating"""
        serializer.save(updated_by=self.request.user)


class HighPerformanceViewSet(BaseViewSet):
    """
    High-performance ViewSet with caching and optimization
    """
    
    def list(self, request, *args, **kwargs):
        """Optimized list view with caching"""
        # Generate cache key based on query parameters
        cache_key = self._generate_cache_key(request)
        
        # Try cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            request._cache_hit = True
            return Response(cached_result)
        
        request._cache_hit = False
        
        # Get queryset and apply filters
        queryset = self.filter_queryset(self.get_queryset())
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            # Cache the result
            cache.set(cache_key, result.data, 300)  # 5 minutes
            return result
        
        serializer = self.get_serializer(queryset, many=True)
        result = serializer.data
        cache.set(cache_key, result, 300)
        return Response(result)
    
    def retrieve(self, request, *args, **kwargs):
        """Optimized retrieve view with caching"""
        instance_id = kwargs.get('pk')
        cache_key = f"{self.__class__.__name__.lower()}_detail:{instance_id}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            request._cache_hit = True
            return Response(cached_result)
        
        request._cache_hit = False
        
        # Get instance with optimized queries
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        result = serializer.data
        
        # Cache the result
        cache.set(cache_key, result, 600)  # 10 minutes
        return Response(result)
    
    def _generate_cache_key(self, request):
        """Generate cache key based on request parameters"""
        params = sorted(request.query_params.items())
        param_str = '&'.join([f"{k}={v}" for k, v in params])
        return f"{self.__class__.__name__.lower()}_list:{hash(param_str)}"
    
    def perform_create(self, serializer):
        """Override create to invalidate related caches"""
        instance = serializer.save(created_by=self.request.user)
        self._invalidate_related_caches()
        return instance
    
    def perform_update(self, serializer):
        """Override update to invalidate related caches"""
        instance = serializer.save(updated_by=self.request.user)
        self._invalidate_related_caches()
        # Invalidate specific instance cache
        cache.delete(f"{self.__class__.__name__.lower()}_detail:{instance.id}")
        return instance
    
    def perform_destroy(self, instance):
        """Override destroy to invalidate related caches"""
        instance_id = instance.id
        instance.delete()
        self._invalidate_related_caches()
        cache.delete(f"{self.__class__.__name__.lower()}_detail:{instance_id}")
    
    def _invalidate_related_caches(self):
        """Invalidate related caches efficiently"""
        # This should be overridden in subclasses to invalidate specific caches
        pass


class EntityViewSet(HighPerformanceViewSet):
    """
    ViewSet for entities (Student, Faculty, etc.) with common functionality
    """
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get documents for a specific entity"""
        cache_key = f"{self.__class__.__name__.lower()}_documents:{pk}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        entity = self.get_object()
        content_type = ContentType.objects.get_for_model(entity)
        documents = Document.objects.filter(
            content_type=content_type,
            object_id=entity.id
        ).select_related('uploaded_by', 'verified_by')
        
        serializer = DocumentSerializer(documents, many=True)
        result = serializer.data
        
        cache.set(cache_key, result, 300)  # 5 minutes
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """Upload a document for an entity"""
        entity = self.get_object()
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            content_type = ContentType.objects.get_for_model(entity)
            serializer.save(
                content_type=content_type,
                object_id=entity.id,
                uploaded_by=request.user
            )
            # Invalidate documents cache
            cache.delete(f"{self.__class__.__name__.lower()}_documents:{entity.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get contacts for a specific entity"""
        cache_key = f"{self.__class__.__name__.lower()}_contacts:{pk}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        entity = self.get_object()
        content_type = ContentType.objects.get_for_model(entity)
        contacts = Contact.objects.filter(
            content_type=content_type,
            object_id=entity.id
        )
        
        serializer = ContactSerializer(contacts, many=True)
        result = serializer.data
        
        cache.set(cache_key, result, 600)  # 10 minutes
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def add_contact(self, request, pk=None):
        """Add a contact for an entity"""
        entity = self.get_object()
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            content_type = ContentType.objects.get_for_model(entity)
            serializer.save(
                content_type=content_type,
                object_id=entity.id
            )
            # Invalidate contacts cache
            cache.delete(f"{self.__class__.__name__.lower()}_contacts:{entity.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def custom_fields(self, request, pk=None):
        """Get custom field values for a specific entity"""
        cache_key = f"{self.__class__.__name__.lower()}_custom_fields:{pk}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        entity = self.get_object()
        content_type = ContentType.objects.get_for_model(entity)
        custom_values = CustomFieldValue.objects.filter(
            content_type=content_type,
            object_id=entity.id
        ).select_related('custom_field')
        
        serializer = CustomFieldValueSerializer(custom_values, many=True)
        result = serializer.data
        
        cache.set(cache_key, result, 600)  # 10 minutes
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def set_custom_field(self, request, pk=None):
        """Set a custom field value for an entity"""
        entity = self.get_object()
        custom_field_id = request.data.get('custom_field_id')
        value = request.data.get('value')
        file_value = request.FILES.get('file_value')
        
        if not custom_field_id:
            return Response(
                {'error': 'custom_field_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            custom_field = CustomField.objects.get(id=custom_field_id, is_active=True)
        except CustomField.DoesNotExist:
            return Response(
                {'error': 'Custom field not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        content_type = ContentType.objects.get_for_model(entity)
        
        # Create or update the custom field value
        custom_value, created = CustomFieldValue.objects.get_or_create(
            content_type=content_type,
            object_id=entity.id,
            custom_field=custom_field,
            defaults={'value': value, 'file_value': file_value}
        )
        
        if not created:
            custom_value.value = value
            if file_value:
                custom_value.file_value = file_value
            custom_value.save()
        
        # Invalidate custom fields cache
        cache.delete(f"{self.__class__.__name__.lower()}_custom_fields:{entity.id}")
        
        serializer = CustomFieldValueSerializer(custom_value)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def available_custom_fields(self, request):
        """Get all available custom fields"""
        cache_key = "available_custom_fields"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        custom_fields = CustomField.objects.filter(is_active=True)
        serializer = CustomFieldSerializer(custom_fields, many=True)
        result = serializer.data
        
        cache.set(cache_key, result, 1800)  # 30 minutes
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get entity statistics"""
        cache_key = f"{self.__class__.__name__.lower()}_statistics"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        queryset = self.get_queryset()
        
        # Calculate statistics
        stats = {
            'total_count': queryset.count(),
            'active_count': queryset.filter(status='ACTIVE').count(),
            'inactive_count': queryset.filter(status='INACTIVE').count(),
            'created_today': queryset.filter(created_at__date=timezone.now().date()).count(),
            'created_this_week': queryset.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7)).count(),
            'created_this_month': queryset.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30)).count(),
        }
        
        cache.set(cache_key, stats, 900)  # 15 minutes
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def bulk_operation(self, request):
        """Perform bulk operations on entities"""
        serializer = BulkOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ids = serializer.validated_data['ids']
        operation = request.data.get('operation', 'update')
        
        if operation == 'update':
            return self._bulk_update(request, ids)
        elif operation == 'delete':
            return self._bulk_delete(request, ids)
        elif operation == 'change_status':
            return self._bulk_change_status(request, ids)
        else:
            return Response(
                {'error': 'Invalid operation'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _bulk_update(self, request, ids):
        """Bulk update entities"""
        update_data = request.data.get('update_data', {})
        queryset = self.get_queryset().filter(id__in=ids)
        
        updated_count = queryset.update(**update_data)
        
        # Invalidate caches
        self._invalidate_related_caches()
        
        return Response({
            'message': f'Updated {updated_count} entities',
            'updated_count': updated_count
        })
    
    def _bulk_delete(self, request, ids):
        """Bulk delete entities"""
        queryset = self.get_queryset().filter(id__in=ids)
        deleted_count = queryset.count()
        queryset.delete()
        
        # Invalidate caches
        self._invalidate_related_caches()
        
        return Response({
            'message': f'Deleted {deleted_count} entities',
            'deleted_count': deleted_count
        })
    
    def _bulk_change_status(self, request, ids):
        """Bulk change status of entities"""
        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {'error': 'status is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(id__in=ids)
        updated_count = queryset.update(status=new_status)
        
        # Invalidate caches
        self._invalidate_related_caches()
        
        return Response({
            'message': f'Updated status for {updated_count} entities',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced search with full-text search capabilities"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter required'}, status=400)
        
        # Use database full-text search if available
        if len(query) > 2:
            # PostgreSQL full-text search
            queryset = self.get_queryset().extra(
                where=["to_tsvector('english', first_name || ' ' || last_name || ' ' || COALESCE(email, '')) @@ plainto_tsquery('english', %s)"],
                params=[query]
            )[:50]  # Limit results
        else:
            # Fallback to regular search
            queryset = self.get_queryset().filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )[:50]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def _invalidate_related_caches(self):
        """Invalidate related caches efficiently"""
        # Invalidate list caches
        cache.delete_many([
            f"{self.__class__.__name__.lower()}_statistics",
            f"{self.__class__.__name__.lower()}_list:*",
        ])
