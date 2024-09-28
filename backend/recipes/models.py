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
    """Модель описывающая поля Ингридиенты.
    Атрибуты модели:
    name: Название ингредиента, уникальное для каждого ингредиента.
    unit: Единица измерения для ингредиента (например, "г", "кг", "шт").
    """
    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Название',
    )
    unit = models.CharField(
        max_length=UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(AuthorModel):
    """Модель описывающая поля Рецепты. Наследуется от модели AuthorModel.
    title: Название рецепта.
    image: Поле для загрузки изображения рецепта.
    description: Текстовое описание рецепта.
    ingredients: Связь многие-ко-многим с моделью Ingredient через
    промежуточную модель RecipeIngredient.
    tags: Связь многие-ко-многим с моделью Tag, позволяющая устанавливать
    несколько тегов для одного рецепта.
    cooking_time: Время приготовления в минутах.
    """

    title = models.CharField(
        max_length=TITLE_MAX_LENGTH,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение',
    )
    description = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Тэги')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MaxValueValidator(
                COOKING_MAX_TIME, 'Время готовки не может быть больше суток.',
            ),
            MinValueValidator(
                COOKING_MIN_TIME,
                f'Время готовки не может быть меньше {COOKING_MIN_TIME} мин.',
            ),
        ],
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
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
        verbose_name='Ингредиенты',
    )
    quantity = models.FloatField(verbose_name='Количество')
    unit = models.CharField(
        max_length=UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return (
            f'{self.quantity} {self.unit} {self.ingredient.name}'
            f'для {self.recipe.title}'
        )
