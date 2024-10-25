from django.core.exceptions import ValidationError
from django.db import transaction

from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (BooleanField, CharField,
                                        IntegerField, ModelSerializer,
                                        PrimaryKeyRelatedField)
from rest_framework.reverse import reverse

from recipes.models import (FavoritesRecipe, Ingredient, Recipe,
                            RecipeShortLink, RecipeIngredients,
                            ShoppingCart, Tag)
from users.serializers import UserSerializer


class TagSerializer(ModelSerializer):
    """Сериализатор преобразования данных модели Tag в формат JSON."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(ModelSerializer):
    """Сериализатор преобразования данных модели Ingredient в формат JSON."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientGetSerializer(ModelSerializer):
    """Сериалайзер представления ингредиента для рецепта"""

    id = IntegerField(source='ingredient.id')
    name = CharField(source='ingredient.name')
    measurement_unit = CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeSerializer(ModelSerializer):
    """Сериализатор преобразования данных модели Recipe в формат JSON."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientGetSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = BooleanField(default=False, read_only=True)
    is_in_shopping_cart = BooleanField(default=False, read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeGetSerializer(ModelSerializer):
    """Сериализатор для представления данных о рецепте."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeIngredientSerializer(ModelSerializer):
    """Сериализатор представления ингредиента в RecipeCreateSerializer."""

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeCreateSerializer(ModelSerializer):
    """Сериализатор для создания рецептов."""

    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
        )

    def validate_image(self, image_data):
        """Валидация изображения рецепта перед созданием.

        :param image_data: Данные изображения.
        :raises ValidationError: Если изображение отсутствует.
        :return: Данные изображения, если они валидны.
        """
        if image_data is None:
            raise ValidationError(
                'У рецепта обязательно должно быть изображение.'
            )
        return image_data

    def validate(self, data):
        """Валидация ингредиентов и тегов перед созданием рецепта.

        :param data: Данные, переданные для создания рецепта.
        :raises ValidationError: Если не выбраны теги или ингредиенты,
        или если количество ингредиента неверно.
        :return: Валидированные данные.
        """
        tags = data.get('tags', [])
        if not tags:
            raise ValidationError('В рецепте не выбран тэг.')

        if len(tags) != len(set(tags)):
            raise ValidationError('Теги не должны повторяться.')

        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise ValidationError('В рецепте не выбраны ингредиенты.')

        ingredient_ids = {
            ingredient['ingredient'].id for ingredient in ingredients
        }
        if len(ingredient_ids) != len(ingredients):
            raise ValidationError('Ингредиенты не должны повторяться.')

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта.

        :param validated_data: Валидированные данные для создания рецепта.
        :return: Созданный экземпляр рецепта.
        """
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data
        )
        recipe.tags.set(tags)
        self.add_ingredients_to_recipe(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление существующего рецепта.

        :param instance: Экземпляр рецепта для обновления.
        :param validated_data: Валидированные данные для обновления рецепта.
        :return: Обновленный экземпляр рецепта.
        """
        ingredients = validated_data.pop('recipe_ingredients')
        instance.ingredients.clear()
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)
        self.add_ingredients_to_recipe(instance, ingredients)
        super().update(instance, validated_data)
        return instance

    @staticmethod
    def add_ingredients_to_recipe(recipe, ingredients):
        """Добавление или обновление ингредиентов в рецепте.

        :param recipe: Экземпляр рецепта, в который добавляются ингредиенты.
        :param ingredients: Список ингредиентов для добавления.
        """
        RecipeIngredients.objects.bulk_create(
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in sorted(
                ingredients, key=lambda x: x['ingredient'].name
            )
        )

    def to_representation(self, instance):
        """Возвращает представление данных рецепта.

        :param instance: Экземпляр модели Recipe.
        :return: Данные рецепта в формате JSON.
        """
        return RecipeSerializer(instance, context=self.context).data


class ShortLinkSerializer(ModelSerializer):
    """Сериализатор коротких ссылок"""

    class Meta:
        model = RecipeShortLink
        fields = ('original_url',)
        write_only_fields = ('original_url',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse('shortener:load_url', args=[obj.short_link])
        )

    def create(self, validated_data):
        # instance, _ = RecipeShortLink.objects.get_or_create(**validated_data)
        instance = RecipeShortLink(**validated_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        return {'short-link': self.get_short_link(instance)}


class BaseRecipeCollectionSerializer(ModelSerializer):
    """Родительский сериализатор добавления в Избранное/Список покупок."""

    class Meta:
        model = None
        fields = ('author', 'recipe')
        read_only_fields = ('author',)

    def get_recipe_added_to(self):
        """Возвращает название коллекции, куда добавляется рецепт.

        :raises NotImplementedError: Если модель не указана в подклассе.
        :return: Название коллекции.
        """
        if self.Meta.model is None:
            raise NotImplementedError('Не указана модель в подклассе.')
        return self.Meta.model._meta.verbose_name

    def validate(self, data):
        """Валидация данных перед добавлением в избранное/список покупок.

        :param data: Данные для валидации.
        :raises ValidationError: Если рецепт уже добавлен в коллекцию.
        :return: Валидированные данные.
        """
        recipe = data['recipe']
        user = self.context['request'].user
        if self.Meta.model.objects.filter(author=user, recipe=recipe).exists():
            raise ValidationError(
                f'Рецепт уже находится в {self.get_recipe_added_to()}'
            )
        return data

    def to_representation(self, instance):
        """Возвращает представление данных рецепта.

        :param instance: Экземпляр модели, связанный
        с избранным или списком покупок.
        :return: Данные рецепта в формате JSON.
        """
        return RecipeGetSerializer(instance.recipe).data


class FavoritesSerializer(BaseRecipeCollectionSerializer):
    """Сериализатор добавления рецептов в избранное."""

    class Meta(BaseRecipeCollectionSerializer.Meta):
        model = FavoritesRecipe


class ShoppingCartSerializer(BaseRecipeCollectionSerializer):
    """Сериализатор добавления рецептов в список покупок."""

    class Meta(BaseRecipeCollectionSerializer.Meta):
        model = ShoppingCart
