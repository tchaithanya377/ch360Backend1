from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academics'
    verbose_name = 'Academic Management'
    
    def ready(self):
        import academics.signals
