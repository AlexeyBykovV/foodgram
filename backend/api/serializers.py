from django.core.exceptions import ValidationError
from django.db import transaction

from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField)

from recipes.models import (FavoritesRecipe, Ingredient, Recipe,
                            RecipeIngredients, ShoppingCart, Tag)
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


class RecipeSerializer(ModelSerializer):
    """Сериализатор преобразования данных модели Recipe в формат JSON."""

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
        """Получение списка ингредиентов для рецепта.

        :param obj: Экземпляр модели Recipe.
        :return: Список ингредиентов с их идентификаторами, названиями,
        единицами измерения и количеством.
        """
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
        """Проверка наличия рецепта в избранном.

        :param obj: Экземпляр модели Recipe.
        :return: True, если рецепт в избранном, иначе False.
        """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.favorites.filter(author=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка наличия рецепта в списке покупок.

        :param obj: Экземпляр модели Recipe.
        :return: True, если рецепт в списке покупок, иначе False.
        """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.shoppingcart.filter(author=request.user).exists()


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

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise ValidationError('Теги не должны повторяться.')

        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise ValidationError('В рецепте не выбраны ингредиенты.')

        ingredient_ids = []
        for ingredient in ingredients:
            ingredient_id = ingredient['ingredient'].id
            if ingredient_id in ingredient_ids:
                raise ValidationError(
                    f'{ingredient["ingredient"].name} уже добавлен в рецепт.'
                )
            ingredient_ids.append(ingredient_id)

            amount = ingredient.get('amount')
            if amount is None or amount <= 0:
                raise ValidationError(
                    f'Неправильное количество {ingredient["ingredient"].name}.'
                    ' Количество должно быть больше нуля.'
                )

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
            for ingredient in ingredients
        )

    def to_representation(self, instance):
        """Возвращает представление данных рецепта.

        :param instance: Экземпляр модели Recipe.
        :return: Данные рецепта в формате JSON.
        """
        return RecipeSerializer(instance, context=self.context).data


class FavoritesShoppingCartSerializer(ModelSerializer):
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
        recipe = instance.recipe
        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': recipe.image.url if recipe.image else None,
            'cooking_time': recipe.cooking_time
        }


class FavoritesSerializer(FavoritesShoppingCartSerializer):
    """Сериализатор добавления рецептов в избранное."""

    class Meta(FavoritesShoppingCartSerializer.Meta):
        model = FavoritesRecipe


class ShoppingCartSerializer(FavoritesShoppingCartSerializer):
    """Сериализатор добавления рецептов в список покупок."""

    class Meta(FavoritesShoppingCartSerializer.Meta):
        model = ShoppingCart
