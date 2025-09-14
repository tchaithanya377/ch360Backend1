"""
Core signals for CampusHub360
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .cache import cache_manager
import logging

logger = logging.getLogger(__name__)


@receiver(post_save)
def invalidate_cache_on_save(sender, instance, **kwargs):
    """Invalidate cache when any model is saved"""
    if hasattr(instance, '_meta'):
        entity_type = instance._meta.model_name
        
        # Skip cache invalidation for certain models that don't need it
        skip_models = ['session', 'logentry', 'contenttype', 'permission']
        if entity_type in skip_models:
            return
            
        # Get the appropriate ID field based on the model
        entity_id = None
        if hasattr(instance, 'id'):
            entity_id = str(instance.id)
        elif hasattr(instance, 'session_key'):  # Django Session model
            entity_id = str(instance.session_key)
        elif hasattr(instance, 'pk'):
            entity_id = str(instance.pk)
        
        if entity_id:
            cache_manager.invalidate_entity_caches(entity_type, entity_id)
            logger.debug(f"Invalidated cache for {entity_type} {entity_id} on save")


@receiver(post_delete)
def invalidate_cache_on_delete(sender, instance, **kwargs):
    """Invalidate cache when any model is deleted"""
    if hasattr(instance, '_meta'):
        entity_type = instance._meta.model_name
        
        # Skip cache invalidation for certain models that don't need it
        skip_models = ['session', 'logentry', 'contenttype', 'permission']
        if entity_type in skip_models:
            return
            
        # Get the appropriate ID field based on the model
        entity_id = None
        if hasattr(instance, 'id'):
            entity_id = str(instance.id)
        elif hasattr(instance, 'session_key'):  # Django Session model
            entity_id = str(instance.session_key)
        elif hasattr(instance, 'pk'):
            entity_id = str(instance.pk)
        
        if entity_id:
            cache_manager.invalidate_entity_caches(entity_type, entity_id)
            logger.debug(f"Invalidated cache for {entity_type} {entity_id} on delete")


# Specific signals for core models
@receiver(post_save, sender='core.CustomField')
def invalidate_custom_field_cache(sender, instance, **kwargs):
    """Invalidate custom field caches when CustomField is saved"""
    cache_manager.delete_pattern("custom_fields:*")
    cache_manager.delete_pattern("*_custom_fields:*")
    logger.debug("Invalidated custom field caches")


@receiver(post_save, sender='core.CustomFieldValue')
def invalidate_custom_field_value_cache(sender, instance, **kwargs):
    """Invalidate custom field value caches when CustomFieldValue is saved"""
    if instance.content_object:
        entity_type = instance.content_object._meta.model_name
        
        # Get the appropriate ID field based on the content object
        entity_id = None
        if hasattr(instance.content_object, 'id'):
            entity_id = str(instance.content_object.id)
        elif hasattr(instance.content_object, 'session_key'):  # Django Session model
            entity_id = str(instance.content_object.session_key)
        elif hasattr(instance.content_object, 'pk'):
            entity_id = str(instance.content_object.pk)
        
        if entity_id:
            cache_manager.invalidate_entity_caches(entity_type, entity_id)
            logger.debug(f"Invalidated custom field value cache for {entity_type} {entity_id}")


@receiver(post_save, sender='core.Document')
def invalidate_document_cache(sender, instance, **kwargs):
    """Invalidate document caches when Document is saved"""
    if instance.content_object:
        entity_type = instance.content_object._meta.model_name
        
        # Get the appropriate ID field based on the content object
        entity_id = None
        if hasattr(instance.content_object, 'id'):
            entity_id = str(instance.content_object.id)
        elif hasattr(instance.content_object, 'session_key'):  # Django Session model
            entity_id = str(instance.content_object.session_key)
        elif hasattr(instance.content_object, 'pk'):
            entity_id = str(instance.content_object.pk)
        
        if entity_id:
            cache_manager.invalidate_entity_caches(entity_type, entity_id)
            logger.debug(f"Invalidated document cache for {entity_type} {entity_id}")


@receiver(post_save, sender='core.Contact')
def invalidate_contact_cache(sender, instance, **kwargs):
    """Invalidate contact caches when Contact is saved"""
    if instance.content_object:
        entity_type = instance.content_object._meta.model_name
        
        # Get the appropriate ID field based on the content object
        entity_id = None
        if hasattr(instance.content_object, 'id'):
            entity_id = str(instance.content_object.id)
        elif hasattr(instance.content_object, 'session_key'):  # Django Session model
            entity_id = str(instance.content_object.session_key)
        elif hasattr(instance.content_object, 'pk'):
            entity_id = str(instance.content_object.pk)
        
        if entity_id:
            cache_manager.invalidate_entity_caches(entity_type, entity_id)
            logger.debug(f"Invalidated contact cache for {entity_type} {entity_id}")
