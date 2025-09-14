from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'campshub360'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        try:
            import django_prometheus  # noqa: F401
        except Exception:
            pass


