from django.apps import AppConfig


class MembershipsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "memberships"

    def ready(self):
        # Import signals to register them
        import memberships.signals  # noqa
