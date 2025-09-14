from django.apps import AppConfig


class FeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fees'
    verbose_name = 'Fee Management'

    def ready(self):
        # Import signals if needed
        # from . import signals  # noqa: F401
        return super().ready()
