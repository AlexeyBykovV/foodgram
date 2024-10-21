from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Настройка приложения api."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Рецепты'
