from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.constants import (
    TITLE_MAX_LENGTH,
    NAME_MAX_LENGTH,
    SLUG_MAX_LENGTH,
    UNIT_MAX_LENGTH,
    COOKING_MAX_TIME,
    COOKING_MIN_TIME,
)
from core.models import AuthorModel


User = get_user_model()


class Tag(models.Model):
    """Модель описывающая поля Тэг.

    Атрибуты модели:
    name: Название тега, уникальное для каждого тега.
    slug: Уникальный слаг, автоматически генерируемый на основе названия тега.
    """

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель описывающая поля Ингридиента.

    Атрибуты модели:
    name: Название ингредиента, уникальное для каждого ингредиента.
    measurement_unit: Единица измерения для ингредиента.
    """

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(AuthorModel):
    """Модель описывающая поля Рецепты. Наследуется от модели AuthorModel.

    name: Название рецепта.
    image: Поле для загрузки изображения рецепта.
    text: Текстовое описание рецепта.
    ingredients: Связь многие-ко-многим с моделью Ingredient через
    промежуточную модель RecipeIngredients.
    tags: Связь многие-ко-многим с моделью Tag, позволяющая устанавливать
    несколько тегов для одного рецепта.
    cooking_time: Время приготовления в минутах.
    """

    name = models.CharField(
        max_length=TITLE_MAX_LENGTH,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение рецепта',
    )
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        verbose_name='Ингредиенты рецепта',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тэги')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MaxValueValidator(
                COOKING_MAX_TIME,
                'Время готовки не может быть больше суток.',
            ),
            MinValueValidator(
                COOKING_MIN_TIME,
                f'Время готовки не может быть меньше {COOKING_MIN_TIME} мин.',
            ),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата добавления',
    )

    class Meta:
        ordering = ['-pub_date']
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """Промежуточная модель для связи между рецептами и ингредиентами.

    Хранит количество и единицу измерения для каждого ингредиента
    в конкретном рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.IntegerField(verbose_name='Количество ингредиента')
    measurement_unit = models.CharField(
        max_length=UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return (
            f'{self.recipe.name} : '
            f'{self.ingredient.name} - {self.amount} {self.measurement_unit}'
        )


class FavoritesRecipe(AuthorModel):
    """Модель описывающая Избранное."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_recipe_favorite'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe.name} добавлен в избранное.'


class ShoppingCart(AuthorModel):
    """Модель описывающая Список покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        default_related_name = 'shoppingcart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_recipe_shopping_cart'
            )
        ]

    def __str__(self):
        return f'Рецепт {self.recipe.name} добавлен в список покупок.'
