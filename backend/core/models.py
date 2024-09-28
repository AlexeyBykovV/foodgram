from django.db import models


class AuthorModel(models.Model):
    """Модель для поля Автор."""

    AUTH_USER_MODEL = 'users.CustomUser'

    author = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )

    class Meta:
        abstract = True
