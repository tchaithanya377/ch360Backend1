from django.apps import AppConfig


class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'students'

    def ready(self) -> None:
        # Import signals
        from . import signals  # noqa: F401
        return super().ready()