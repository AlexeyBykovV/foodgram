from django.db import transaction
from django.core.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    PrimaryKeyRelatedField,
)

from users.serializers import UserSerializer
from recipes.models import (
    FavoritesRecipe,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Tag,
)


class TagSerializer(ModelSerializer):
    """Сериализатор преобразует данные модели Tag в формат JSON."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(ModelSerializer):
    """Сериализатор преобразует данные модели Ingredient в формат JSON."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeSerializer(ModelSerializer):
    """Сериализатор преобразует данные модели Recipe в формат JSON."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = SerializerMethodField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'ingredients',
            'cooking_time',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_ingredients(self, obj):
        """Получение ингредиентов для рецепта."""
        ingredients = obj.recipe_ingredients.all()
        return [
            {
                'id': ingredient.ingredient.id,
                'name': ingredient.ingredient.name,
                'measurement_unit': ingredient.ingredient.measurement_unit,
                'amount': ingredient.amount
            }
            for ingredient in ingredients
        ]

    def get_is_favorited(self, obj):
        """Проверка наличия рецепта в избранном."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        # return Recipe.objects.filter(
        #     recipefavorites__author=user, id=obj.id
        # ).exists()
        return obj.favorites.filter(author=user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в списке покупок."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        # return Recipe.objects.filter(
        #     shoppingcart__author=user, id=obj.id
        # ).exists()
        return obj.shoppingcart.filter(author=user).exists()


class RecipeIngredientSerializer(ModelSerializer):
    """Сериалайзер представления ингредиента для RecipeCreateSerializer."""

    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeCreateSerializer(ModelSerializer):
    """Сериалайзер создания Рецептов"""

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
        """Валидация изображения рецепта перед созданием рецепта."""
        if image_data is None:
            raise ValidationError(
                'У рецепта обязательно должно быть изображение.'
            )
        return image_data

    def validate(self, data):
        """Валидация ингредиентов и тэга перед созданием рецепта."""
        tags = data.get('tags', [])
        if not tags:
            raise ValidationError('В рецепте не выбран тэг.')

        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise ValidationError('В рецепте не выбраны ингредиенты')

        # ingredients_result = []
        # for ingredient in ingredients:

        #     id_ingredients = {
        #         ingredient['ingredient'] for ingredient in ingredients
        #     }

        #     if any(
        #         item['ingredient'] == id_ingredients for item in ingredients_result
        #     ):
        id_ingredients = {
            ingredient['ingredient'] for ingredient in ingredients
        }
        if len(ingredients) != len(id_ingredients):
            raise ValidationError('В рецепт уже добавлен ингредиент.')

            # amount = ingredient['amount']
            # if not (isinstance(amount, int) or amount.isdigit()):
            #     raise ValidationError('Неправильное количество ингридиента.')

            # ingredients_result.append(
            #     {'ingredients': ingredient, 'amount': amount}
            # )

        # data['ingredients'] = ingredients_result
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
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
        """Обновление рецепта."""
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
        """Добавление или обновление Ингредиентов в рецепте."""
        RecipeIngredients.objects.bulk_create(
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def to_representation(self, instance):
        """Возвращает представление данных рецепта."""
        return RecipeSerializer(instance, context=self.context).data


class FavoritesShoppingCartSerializer(ModelSerializer):
    """Родительсский сериалайзер для добавления в Избранное/Спискок покупок."""

    class Meta:
        model = None
        fields = ('author', 'recipe')
        read_only_fields = ('author',)

    def get_recipe_added_to(self):
        """Возвращает название коллекции, куда добавляется рецепт."""
        if self.Meta.model is None:
            raise NotImplementedError('Не указана модель в подклассе.')
        return self.Meta.model._meta.verbose_name

    def validate(self, data):
        """Валидация данных перед добавление в избранное/список покупок."""
        recipe = data['recipe']
        user = self.context['request'].user
        if self.Meta.model.objects.filter(author=user, recipe=recipe).exists():
            raise ValidationError(
                f'Рецепт уже находится в {self.get_recipe_added_to()}'
            )
        return data

    def to_representation(self, instance):
        """Возвращает представление данных рецепта."""
        recipe = instance.recipe
        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': recipe.image.url if recipe.image else None,
            'cooking_time': recipe.cooking_time
        }


class FavoritesSerializer(FavoritesShoppingCartSerializer):
    """Сериалайзер для добавления в избранное."""

    class Meta(FavoritesShoppingCartSerializer.Meta):
        model = FavoritesRecipe


class ShoppingCartSerializer(FavoritesShoppingCartSerializer):
    """Сериалайзер для добавления в список покупок."""

    class Meta(FavoritesShoppingCartSerializer.Meta):
        model = ShoppingCart
