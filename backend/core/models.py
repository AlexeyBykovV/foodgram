from django.db import models

from recipes.models import Recipe


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

    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )

    class Meta:
        """Метакласс для модели AuthorModel, определяющий параметры модели."""
        abstract = True


class RecipeRelationModel(AuthorModel):
    """Базовая модель для отношений с рецептами."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True

    def __str__(self):
        """Возвращает строковое представление объекта."""
        return f'Рецепт {self.recipe.name}'
