from django.apps import AppConfig


class FacultyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'faculty'
    verbose_name = 'Faculty Management'
    
    def ready(self):
        """Import signals when the app is ready"""
        import faculty.signals
