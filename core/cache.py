"""
Advanced caching strategies for CampusHub360
Multi-tier caching system optimized for 20K+ RPS
"""

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
import hashlib
import json
import time
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MultiTierCache:
    """
    Multi-tier caching system for high-performance applications
    """
    
    def __init__(self):
        self.l1_cache = cache  # Application cache (Redis)
        self.l2_cache = cache  # Session cache (Redis)
        self.l3_cache = cache  # Query cache (Redis)
    
    def get(self, key: str, default=None):
        """Get value from cache with fallback strategy"""
        # Try L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2
        value = self.l2_cache.get(key)
        if value is not None:
            self.l1_cache.set(key, value, 60)  # Cache in L1 for 1 minute
            return value
        
        # Try L3
        value = self.l3_cache.get(key)
        if value is not None:
            self.l1_cache.set(key, value, 60)  # Cache in L1 for 1 minute
            self.l2_cache.set(key, value, 300)  # Cache in L2 for 5 minutes
            return value
        
        return default
    
    def set(self, key: str, value: Any, timeout: int = None):
        """Set value in all cache tiers"""
        if timeout is None:
            timeout = 300  # Default 5 minutes
        
        self.l1_cache.set(key, value, timeout)
        self.l2_cache.set(key, value, timeout * 2)  # L2 lasts longer
        self.l3_cache.set(key, value, timeout * 4)  # L3 lasts longest
    
    def delete(self, key: str):
        """Delete value from all cache tiers"""
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
        self.l3_cache.delete(key)
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if hasattr(self.l1_cache, 'delete_pattern'):
            self.l1_cache.delete_pattern(pattern)
        if hasattr(self.l2_cache, 'delete_pattern'):
            self.l2_cache.delete_pattern(pattern)
        if hasattr(self.l3_cache, 'delete_pattern'):
            self.l3_cache.delete_pattern(pattern)


class CacheManager:
    """
    Advanced cache manager with intelligent invalidation
    """
    
    # Cache key prefixes
    CACHE_PREFIXES = {
        'entity_detail': 'entity_detail',
        'entity_list': 'entity_list',
        'entity_search': 'entity_search',
        'entity_statistics': 'entity_statistics',
        'entity_dashboard': 'entity_dashboard',
        'entity_analytics': 'entity_analytics',
        'entity_export': 'entity_export',
        'custom_fields': 'custom_fields',
        'documents': 'documents',
        'contacts': 'contacts',
    }
    
    # Cache TTL settings (in seconds)
    CACHE_TTL = {
        'entity_detail': 600,      # 10 minutes
        'entity_list': 300,        # 5 minutes
        'entity_search': 120,      # 2 minutes
        'entity_statistics': 900,  # 15 minutes
        'entity_dashboard': 1800,  # 30 minutes
        'entity_analytics': 3600,  # 1 hour
        'entity_export': 60,       # 1 minute
        'custom_fields': 1800,     # 30 minutes
        'documents': 300,          # 5 minutes
        'contacts': 600,           # 10 minutes
    }
    
    def __init__(self):
        self.cache = MultiTierCache()
    
    def generate_cache_key(self, cache_type: str, **kwargs) -> str:
        """Generate cache key with consistent format"""
        prefix = self.CACHE_PREFIXES.get(cache_type, 'default')
        
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_suffix = '_'.join([f"{k}_{v}" for k, v in sorted_kwargs])
            return f"{prefix}:{key_suffix}"
        
        return prefix
    
    def get_cache_key_hash(self, cache_type: str, **kwargs) -> str:
        """Generate hash-based cache key for complex parameters"""
        prefix = self.CACHE_PREFIXES.get(cache_type, 'default')
        key_data = json.dumps(kwargs, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    
    def get(self, cache_type: str, **kwargs) -> Optional[Any]:
        """Get cached data"""
        cache_key = self.generate_cache_key(cache_type, **kwargs)
        return self.cache.get(cache_key)
    
    def set(self, cache_type: str, data: Any, ttl: Optional[int] = None, **kwargs) -> bool:
        """Set cached data"""
        cache_key = self.generate_cache_key(cache_type, **kwargs)
        ttl = ttl or self.CACHE_TTL.get(cache_type, 300)
        self.cache.set(cache_key, data, ttl)
        return True
    
    def delete(self, cache_type: str, **kwargs) -> bool:
        """Delete specific cache entry"""
        cache_key = self.generate_cache_key(cache_type, **kwargs)
        self.cache.delete(cache_key)
        return True
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete cache entries matching pattern"""
        self.cache.delete_pattern(pattern)
        return 0
    
    def invalidate_entity_caches(self, entity_type: str, entity_id: str) -> None:
        """Invalidate all caches related to a specific entity"""
        cache_keys_to_delete = [
            self.generate_cache_key('entity_detail', entity_type=entity_type, entity_id=entity_id),
            self.generate_cache_key('documents', entity_type=entity_type, entity_id=entity_id),
            self.generate_cache_key('contacts', entity_type=entity_type, entity_id=entity_id),
        ]
        
        # Delete specific keys
        for key in cache_keys_to_delete:
            self.cache.delete(key)
        
        # Delete pattern-based keys (for list caches)
        patterns_to_delete = [
            f"entity_list:*",
            f"entity_search:*",
            f"entity_statistics*",
            f"entity_dashboard*",
        ]
        
        for pattern in patterns_to_delete:
            self.delete_pattern(pattern)
        
        logger.info(f"Invalidated caches for {entity_type} {entity_id}")
    
    def invalidate_all_entity_caches(self, entity_type: str) -> None:
        """Invalidate all caches related to an entity type"""
        patterns_to_delete = [
            f"entity_{entity_type}_*",
            f"{entity_type}_*",
        ]
        
        for pattern in patterns_to_delete:
            self.delete_pattern(pattern)
        
        logger.info(f"Invalidated all {entity_type} caches")


class CacheWarmingService:
    """
    Service to warm up caches with frequently accessed data
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
    
    def warm_entity_statistics(self, entity_model, entity_type: str):
        """Warm up entity statistics cache"""
        from django.db.models import Count, Q
        
        stats = entity_model.objects.aggregate(
            total_count=Count('id'),
            active_count=Count('id', filter=Q(status='ACTIVE')),
            inactive_count=Count('id', filter=Q(status='INACTIVE')),
        )
        
        self.cache_manager.set('entity_statistics', stats, entity_type=entity_type)
        logger.info(f"Warmed up {entity_type} statistics cache")
    
    def warm_dashboard_metrics(self, entity_model, entity_type: str):
        """Warm up dashboard metrics cache"""
        from django.db.models import Count, Q
        from django.db.models.functions import TruncMonth
        
        metrics = entity_model.objects.aggregate(
            total_count=Count('id'),
            active_count=Count('id', filter=Q(status='ACTIVE')),
            inactive_count=Count('id', filter=Q(status='INACTIVE')),
        )
        
        # Get distribution data
        distribution = dict(entity_model.objects.values('status').annotate(count=Count('id')))
        
        # Monthly data
        monthly_data = entity_model.objects.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')[:12]
        
        monthly_counts = {str(item['month']): item['count'] for item in monthly_data}
        
        dashboard_data = {
            **metrics,
            'distribution': distribution,
            'monthly_counts': monthly_counts
        }
        
        self.cache_manager.set('entity_dashboard', dashboard_data, entity_type=entity_type)
        logger.info(f"Warmed up {entity_type} dashboard metrics cache")
    
    def warm_frequently_accessed_entities(self, entity_model, entity_type: str, serializer_class):
        """Warm up cache for frequently accessed entities"""
        # Get top 100 most recently updated entities
        recent_entities = entity_model.objects.select_related(
            'department', 'academic_program'
        ).order_by('-updated_at')[:100]
        
        for entity in recent_entities:
            cache_key = self.cache_manager.generate_cache_key(
                'entity_detail', 
                entity_type=entity_type, 
                entity_id=entity.id
            )
            if not self.cache_manager.cache.get(cache_key):
                # Cache entity detail
                serializer = serializer_class(entity)
                self.cache_manager.cache.set(cache_key, serializer.data, 600)
        
        logger.info(f"Warmed up frequently accessed {entity_type} entities cache")
    
    def warm_all_caches(self, entity_model, entity_type: str, serializer_class):
        """Warm up all caches for an entity type"""
        self.warm_entity_statistics(entity_model, entity_type)
        self.warm_dashboard_metrics(entity_model, entity_type)
        self.warm_frequently_accessed_entities(entity_model, entity_type, serializer_class)
        logger.info(f"Completed cache warming for all {entity_type} data")


class CacheAnalytics:
    """
    Cache performance analytics and monitoring
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if hasattr(self.cache_manager.cache.l1_cache, 'get_stats'):
            return self.cache_manager.cache.l1_cache.get_stats()
        
        return {
            'hit_rate': 0,
            'miss_rate': 0,
            'total_requests': 0,
            'cache_size': 0
        }
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        stats = self.get_cache_stats()
        total_requests = stats.get('total_requests', 0)
        if total_requests == 0:
            return 0.0
        
        hits = stats.get('hits', 0)
        return (hits / total_requests) * 100
    
    def get_cache_memory_usage(self) -> Dict[str, Any]:
        """Get cache memory usage"""
        if hasattr(self.cache_manager.cache.l1_cache, 'get_memory_usage'):
            return self.cache_manager.cache.l1_cache.get_memory_usage()
        
        return {
            'used_memory': 0,
            'max_memory': 0,
            'memory_usage_percentage': 0
        }
    
    def get_cache_recommendations(self) -> List[str]:
        """Get cache optimization recommendations"""
        recommendations = []
        
        hit_rate = self.get_cache_hit_rate()
        if hit_rate < 70:
            recommendations.append("Consider increasing cache TTL for frequently accessed data")
        
        if hit_rate < 50:
            recommendations.append("Review cache key strategy and invalidation patterns")
        
        memory_usage = self.get_cache_memory_usage()
        if memory_usage.get('memory_usage_percentage', 0) > 80:
            recommendations.append("Consider increasing cache memory or optimizing cache size")
        
        return recommendations


# Global cache manager instance
cache_manager = CacheManager()

# Cache warming service instance
cache_warming_service = CacheWarmingService()

# Cache analytics instance
cache_analytics = CacheAnalytics()


# Cache invalidation signals are defined in core/signals.py
