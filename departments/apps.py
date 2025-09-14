from django.apps import AppConfig


class DepartmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'departments'
    verbose_name = 'Department Management'
    
    def ready(self):
        """Import signals when app is ready"""
        import departments.signals
