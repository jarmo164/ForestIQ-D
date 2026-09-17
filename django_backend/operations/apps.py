from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "operations"

    def ready(self):
        # P1 models live in a separate module to keep the legacy operations model file stable.
        from . import p1_models  # noqa: F401
        from . import p1_signals  # noqa: F401
