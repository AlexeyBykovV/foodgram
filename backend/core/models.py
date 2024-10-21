from django.conf import settings
from django.db import models

User = get_user_model()


class AuthorModel(models.Model):
    """Абстрактная модель, добавляющая поле автора для других моделей.

    Эта модель используется как базовая для других моделей,
    которые требуют указания автора (пользователя), создающего запись.
    Она содержит поле `author`, которое устанавливает связь
    с моделью пользователя.

    :param author (ForeignKey): Ссылка на пользователя,
    который является автором записи.
    Удаление пользователя приведет к удалению всех связанных записей.
    """

    # AUTH_USER_MODEL = settings.AUTH_USER_MODEL

    author = models.ForeignKey(
        # AUTH_USER_MODEL,
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )

    class Meta:
        """Метакласс для модели AuthorModel, определяющий параметры модели."""
        abstract = True
