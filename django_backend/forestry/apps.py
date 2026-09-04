from django.apps import AppConfig


class ForestryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'forestry'

    def ready(self):
        import forestry.signals  # noqa: F401
        import forestry.portfolio_tasks  # noqa: F401
