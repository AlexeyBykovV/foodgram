from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """Настройка приложения recipes."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'Рецепты'
