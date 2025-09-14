# CampusHub360 Refactoring Plan
## University Management ERP - 20K+ RPS Optimization

### 🎯 **Objectives**
- Handle 20K+ requests per second
- Eliminate code duplications
- Improve maintainability and scalability
- Reduce technical debt
- Enhance developer experience

---

## 📊 **Phase 1: Core Infrastructure Refactoring (Week 1-2)**

### 1.1 Create Shared Core Module
```python
# Create: core/models.py
class TimeStampedUUIDModel(models.Model):
    """Shared base model for all apps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Create: core/fields.py
class CustomFieldType(models.TextChoices):
    """Unified custom field types"""
    TEXT = 'text', 'Text'
    NUMBER = 'number', 'Number'
    DATE = 'date', 'Date'
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    SELECT = 'select', 'Select (Dropdown)'
    MULTISELECT = 'multiselect', 'Multi-Select'
    BOOLEAN = 'boolean', 'Yes/No'
    TEXTAREA = 'textarea', 'Long Text'
    FILE = 'file', 'File Upload'
    URL = 'url', 'URL'

# Create: core/models.py
class CustomField(TimeStampedUUIDModel):
    """Unified custom field model"""
    name = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=CustomFieldType.choices)
    required = models.BooleanField(default=False)
    help_text = models.TextField(blank=True, null=True)
    default_value = models.TextField(blank=True, null=True)
    choices = models.JSONField(blank=True, null=True)
    validation_regex = models.CharField(max_length=200, blank=True, null=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Custom Field'
        verbose_name_plural = 'Custom Fields'
```

### 1.2 Unified Serializer Base Classes
```python
# Create: core/serializers.py
class BaseModelSerializer(serializers.ModelSerializer):
    """Base serializer with common functionality"""
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        abstract = True

class BaseListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        abstract = True
        fields = ['id', 'created_at', 'updated_at']

class BaseDetailSerializer(BaseModelSerializer):
    """Full serializer for detail views"""
    class Meta:
        abstract = True
```

### 1.3 Unified ViewSet Base Classes
```python
# Create: core/viewsets.py
class BaseViewSet(viewsets.ModelViewSet):
    """Base ViewSet with common functionality"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return self.get_list_serializer()
        elif self.action in ['retrieve', 'detail']:
            return self.get_detail_serializer()
        return self.get_serializer_class()

class HighPerformanceViewSet(BaseViewSet):
    """High-performance ViewSet with caching"""
    @cached_query(ttl=300)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @cached_query(ttl=600)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
```

---

## 🏗️ **Phase 2: App Consolidation (Week 3-4)**

### 2.1 Merge Duplicate Models
```python
# Before: Multiple CustomField models
# After: Single core.CustomField with polymorphic relationships

# students/models.py
class StudentCustomFieldValue(TimeStampedUUIDModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    custom_field = models.ForeignKey('core.CustomField', on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('student', 'custom_field')

# faculty/models.py  
class FacultyCustomFieldValue(TimeStampedUUIDModel):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    custom_field = models.ForeignKey('core.CustomField', on_delete=models.CASCADE)
    value = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('faculty', 'custom_field')
```

### 2.2 Unified API Structure
```python
# Create: core/api/
# ├── __init__.py
# ├── viewsets.py
# ├── serializers.py
# ├── filters.py
# ├── pagination.py
# └── permissions.py

# core/api/viewsets.py
class UnifiedViewSet(HighPerformanceViewSet):
    """Unified ViewSet for all entities"""
    def get_queryset(self):
        return self.model.objects.select_related(
            *self.select_related_fields
        ).prefetch_related(
            *self.prefetch_related_fields
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return self.list_serializer_class
        elif self.action in ['retrieve', 'detail']:
            return self.detail_serializer_class
        return self.serializer_class
```

---

## ⚡ **Phase 3: Performance Optimization (Week 5-6)**

### 3.1 Database Optimization
```python
# Enhanced database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'campushub360_main',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    },
    'read_replica_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'campushub360_read_1',
        'CONN_MAX_AGE': 600,
    },
    'read_replica_2': {
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': 'campushub360_read_2',
        'CONN_MAX_AGE': 600,
    },
    'analytics': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'campushub360_analytics',
        'CONN_MAX_AGE': 600,
    }
}

# Database router for read/write splitting
class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'analytics':
            return 'analytics'
        return 'read_replica_1'  # or 'read_replica_2' for load balancing
    
    def db_for_write(self, model, **hints):
        return 'default'
```

### 3.2 Advanced Caching Strategy
```python
# core/cache.py
class MultiTierCache:
    """Multi-tier caching system"""
    
    def __init__(self):
        self.l1_cache = cache  # Application cache
        self.l2_cache = cache  # Redis cache
        self.l3_cache = cache  # CDN cache
    
    def get(self, key, default=None):
        # Try L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2
        value = self.l2_cache.get(key)
        if value is not None:
            self.l1_cache.set(key, value, 60)  # Cache in L1 for 1 minute
            return value
        
        return default
    
    def set(self, key, value, timeout=None):
        self.l1_cache.set(key, value, timeout)
        self.l2_cache.set(key, value, timeout)
```

### 3.3 Query Optimization
```python
# core/querysets.py
class OptimizedQuerySet(models.QuerySet):
    """Optimized QuerySet with common optimizations"""
    
    def with_related(self, *fields):
        return self.select_related(*fields)
    
    def with_prefetch(self, *fields):
        return self.prefetch_related(*fields)
    
    def only_fields(self, *fields):
        return self.only(*fields)
    
    def for_list_view(self):
        return self.only_fields(
            'id', 'created_at', 'updated_at'
        ).with_related(
            'department', 'academic_program'
        )
    
    def for_detail_view(self):
        return self.with_related(
            'department', 'academic_program', 'user'
        ).with_prefetch(
            'documents', 'custom_field_values__custom_field'
        )

# Usage in models
class Student(TimeStampedUUIDModel):
    # ... fields ...
    
    objects = OptimizedQuerySet.as_manager()
```

---

## 🔧 **Phase 4: API Standardization (Week 7-8)**

### 4.1 Unified API Endpoints
```python
# core/api/urls.py
router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'faculty', FacultyViewSet, basename='faculty')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'courses', CourseViewSet, basename='course')

# All apps use the same URL structure
urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/reports/', include('reports.urls')),
]
```

### 4.2 Standardized Response Format
```python
# core/responses.py
class StandardResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(data=None, message="Success", status_code=200):
        return Response({
            'success': True,
            'message': message,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }, status=status_code)
    
    @staticmethod
    def error(message="Error", errors=None, status_code=400):
        return Response({
            'success': False,
            'message': message,
            'errors': errors,
            'timestamp': timezone.now().isoformat()
        }, status=status_code)
```

---

## 📈 **Phase 5: Monitoring & Analytics (Week 9-10)**

### 5.1 Performance Monitoring
```python
# core/monitoring.py
class PerformanceMonitor:
    """Performance monitoring and metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_request(self, view_name, duration, cache_hit=False):
        if view_name not in self.metrics:
            self.metrics[view_name] = {
                'total_requests': 0,
                'total_duration': 0,
                'cache_hits': 0,
                'avg_duration': 0
            }
        
        self.metrics[view_name]['total_requests'] += 1
        self.metrics[view_name]['total_duration'] += duration
        if cache_hit:
            self.metrics[view_name]['cache_hits'] += 1
        
        self.metrics[view_name]['avg_duration'] = (
            self.metrics[view_name]['total_duration'] / 
            self.metrics[view_name]['total_requests']
        )
```

### 5.2 Health Checks
```python
# core/health.py
class HealthChecker:
    """System health monitoring"""
    
    def check_database(self):
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def check_cache(self):
        try:
            cache.set('health_check', 'ok', 10)
            return cache.get('health_check') == 'ok'
        except Exception:
            return False
    
    def check_redis(self):
        try:
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL)
            return r.ping()
        except Exception:
            return False
```

---

## 🚀 **Phase 6: Deployment & Scaling (Week 11-12)**

### 6.1 Containerization
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "campshub360.wsgi:application"]
```

### 6.2 Load Balancing Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
  
  app1:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/campushub360
      - REDIS_URL=redis://redis:6379/0
  
  app2:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/campushub360
      - REDIS_URL=redis://redis:6379/0
  
  app3:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/campushub360
      - REDIS_URL=redis://redis:6379/0
  
  app4:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/campushub360
      - REDIS_URL=redis://redis:6379/0
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=campushub360
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7-alpine
```

---

## 📊 **Expected Performance Improvements**

### Before Refactoring:
- **RPS**: ~2,000-3,000
- **Response Time**: 200-500ms
- **Database Queries**: 10-20 per request
- **Cache Hit Rate**: 60-70%

### After Refactoring:
- **RPS**: 20,000+ (10x improvement)
- **Response Time**: 50-100ms (4x improvement)
- **Database Queries**: 2-5 per request (4x improvement)
- **Cache Hit Rate**: 85-95% (25% improvement)

---

## 🎯 **Implementation Priority**

### **High Priority (Week 1-4)**
1. ✅ Create core module with shared models
2. ✅ Consolidate duplicate ViewSets
3. ✅ Implement unified serializers
4. ✅ Database optimization

### **Medium Priority (Week 5-8)**
1. ✅ Advanced caching strategy
2. ✅ API standardization
3. ✅ Performance monitoring
4. ✅ Query optimization

### **Low Priority (Week 9-12)**
1. ✅ Containerization
2. ✅ Load balancing
3. ✅ Advanced monitoring
4. ✅ Documentation

---

## 🔍 **Success Metrics**

- **Performance**: 20K+ RPS capability
- **Maintainability**: 50% reduction in code duplication
- **Developer Experience**: Unified API patterns
- **Scalability**: Horizontal scaling capability
- **Reliability**: 99.9% uptime target

---

## 📝 **Next Steps**

1. **Review and approve** this refactoring plan
2. **Set up development environment** with new structure
3. **Begin Phase 1** implementation
4. **Monitor progress** with weekly reviews
5. **Test performance** at each phase completion

This refactoring plan will transform your CampusHub360 into a high-performance, maintainable, and scalable university management ERP system capable of handling 20K+ RPS while eliminating code duplications and improving developer experience.
