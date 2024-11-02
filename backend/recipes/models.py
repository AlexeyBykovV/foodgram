import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.constants import (AMOUNT_MAX, AMOUNT_MIN, ORIGINAL_URL_SIZE,
                            COOKING_MAX_TIME, COOKING_MIN_TIME,
                            NAME_MAX_LENGTH, SHORT_LINK_SIZE, SLUG_MAX_LENGTH,
                            TITLE_MAX_LENGTH, UNIT_MAX_LENGTH,)
from core.models import AuthorModel

User = get_user_model()


class Tag(models.Model):
    """Модель, описывающая тэги.

    :param name (CharField): Название тега, уникальное для каждого тега.
    :param slug (SlugField): Уникальный слаг, автоматически генерируемый
    на основе названия тега.
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
        """Метакласс для модели Tag, определяющий параметры модели."""
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return self.name


class Ingredient(models.Model):
    """Модель, описывающая ингредиенты.

    :param name (CharField): Название ингредиента, уникальное
    для каждого ингредиента.
    :param measurement_unit (CharField): Единица измерения для ингредиента.
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
        """Метакласс для модели Ingredient, определяющий параметры модели."""
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return self.name


class Recipe(AuthorModel):
    """Модель, описывающая рецепты. Наследуется от модели AuthorModel.

    :param name (CharField): Название рецепта.
    :param image (ImageField): Поле для загрузки изображения рецепта.
    :param text (TextField): Текстовое описание рецепта.
    :param ingredients (ManyToManyField): Связь многие-ко-многим
    с моделью Ingredient через промежуточную модель RecipeIngredients.
    :param tags (ManyToManyField): Связь многие-ко-многим с моделью Tag.
    :param cooking_time (PositiveIntegerField): Время приготовления
    в минутах.
    :param pub_date (DateTimeField): Дата добавления рецепта.
    :param short_link (CharField): Уникальная короткая ссылка на рецепт.
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
    cooking_time = models.PositiveSmallIntegerField(
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
        """Метакласс для модели Recipe, определяющий параметры модели."""
        ordering = ('-pub_date',)
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return self.name


class RecipeShortLink(models.Model):
    """Модель коротких ссылок"""

    short_link = models.CharField(
        max_length=SHORT_LINK_SIZE, unique=True, editable=False
    )
    original_url = models.CharField(max_length=ORIGINAL_URL_SIZE, unique=True)

    class Meta:
        """Метакласс для модели RecipeShortLink,
        определяющий параметры модели.
        """
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return f'{self.original_url} -> {self.short_link}'

    def save(self, *args, **kwargs):
        """Переопределяем метод для генерации short_link перед сохранением."""
        if not self.short_link:
            self.short_link = str(uuid.uuid4())[:SHORT_LINK_SIZE]
        super().save(*args, **kwargs)


class RecipeIngredients(models.Model):
    """Промежуточная модель для связи между рецептами и ингредиентами.

    :param recipe (ForeignKey): Рецепт, к которому относится ингредиент.
    :param ingredient (ForeignKey): Идентификатор ингредиента.
    :param amount (IntegerField): Количество ингредиента в рецепте.
    :param measurement_unit (CharField): Единица измерения
    для количества ингредиента.
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
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[
            MaxValueValidator(
                AMOUNT_MAX,
                f'Количество ингредиента не может быть больше {AMOUNT_MAX}.',
            ),
            MinValueValidator(
                AMOUNT_MIN,
                'Количество ингредиента не может быть меньше '
                f'или равно {AMOUNT_MIN}.',
            ),
        ],
    )
    measurement_unit = models.CharField(
        max_length=UNIT_MAX_LENGTH,
        verbose_name='Единица измерения',
    )

    class Meta:
        """Метакласс для модели RecipeIngredients,
        определяющий параметры модели.
        """
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиент рецепта'

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return (
            f'{self.recipe.name} : '
            f'{self.ingredient.name} - {self.amount} {self.measurement_unit}'
        )


class RecipeRelationModel(AuthorModel):
    """Базовая модель для отношений с рецептами.

    Эта модель наследуется от модели AuthorModel и добавляет поле ForeignKey
    для связи с моделью Recipe. Она также определяет абстрактный метакласс
    и метод __str__, который возвращает строковое представление объекта.

    :param recipe (ForeignKey): Связь многие-ко-одному с моделью Recipe.
    """

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


class FavoritesRecipe(RecipeRelationModel):
    """Модель, описывающая избранные рецепты.

    Эта модель наследуется от модели RecipeRelationModel и добавляет уникальное
    ограничение на поле (author, recipe), чтобы гарантировать, что каждый
    рецепт может быть добавлен в избранное только один раз
    для каждого пользователя.
    """

    class Meta(RecipeRelationModel.Meta):
        """Метакласс для модели FavoritesRecipe,
        определяющий параметры модели.
        """
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_recipe_favorite'
            ),
        )

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return super().__str__() + (
            f' добавлен в избранное пользователю {self.author.username}.'
        )


class ShoppingCart(RecipeRelationModel):
    """Модель, описывающая список покупок.

    Эта модель наследуется от модели RecipeRelationModel и добавляет уникальное
    ограничение на поле (author, recipe), чтобы гарантировать, что каждый
    рецепт может быть добавлен в список покупок только один раз
    для каждого пользователя.
    """

    class Meta(RecipeRelationModel.Meta):
        """Метакласс для модели ShoppingCart, определяющий параметры модели."""
        default_related_name = 'shoppingcart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'recipe'),
                name='unique_recipe_shopping_cart'
            ),
        )

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return super().__str__() + (
            f' добавлен в список покупок пользователю {self.author.username}.'
        )
