from django.conf import settings
from django.db import models


class AuthorModel(models.Model):
    """Модель для поля Автор."""

    AUTH_USER_MODEL = settings.AUTH_USER_MODEL

    author = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )

    class Meta:
        abstract = True
