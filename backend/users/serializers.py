from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    IntegerField,
    SlugRelatedField,
    CurrentUserDefault,
    ValidationError
)
from rest_framework.validators import UniqueTogetherValidator

from .models import Subscriptions
from recipes.models import Recipe


User = get_user_model()


class UserSerializer(ModelSerializer):
    """Сериализатор для получения списка пользователей."""

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Получение подписок пользователя."""
        request = self.context.get('request')

        if request is None:
            return False

        current_user = request.user

        if hasattr(obj, 'subscribed'):
            return bool(obj.subscribed and obj.subscribed[0].is_subscribed)

        return (
            current_user.is_authenticated
            and current_user != obj
            and obj.subscribers.filter(user=current_user).exists()
        )


class UserAvatarSerializer(ModelSerializer):
    """Сериализатор для Аватара."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserRecipeSerializer(UserSerializer):
    """Сериализатор представления рецептов пользователя."""

    recipes = SerializerMethodField()
    recipes_count = IntegerField(
        read_only=True, source='recipes.count'
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, obj):
        """Получение рецептов автора."""

        from api.serializers import RecipeSerializer

        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj)

        if limit:
            queryset = queryset[:int(limit)]

        return RecipeSerializer(queryset, many=True).data


class UserSubscriptionsSerializer(ModelSerializer):
    """Сериализатор представления подписок пользователя."""

    user = SlugRelatedField(
        read_only=True,
        slug_field='email',
        default=CurrentUserDefault(),
    )
    author = SlugRelatedField(
        slug_field='email',
        queryset=User.objects.all(),
    )

    class Meta:
        model = Subscriptions
        fields = ('author', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('author', 'user'),
                message='Вы уже подписаны на этого пользователя.',
            )
        ]

    def validate_author(self, author):
        """Валидация подписки на самого себя."""
        if self.context['request'].user == author:
            raise ValidationError(
                'Вы пытаетесь подписаться на самого себя.'
            )
        return author

    def to_representation(self, instance):
        """Преобразует объект instance в представление UserRecipeSerializer."""
        try:
            if not hasattr(instance, 'author'):
                raise AttributeError('У данного экземпляра нет author.')

            serializer = UserRecipeSerializer(
                instance.author, context=self.context
            )
            return serializer.data

        except AttributeError as e:
            raise e

    def get_is_subscriber(self, obj):
        """Проверка подписки пользователя на автора."""
        return Subscriptions.objects.filter(
            user=obj.user, author=obj.author
        ).exists()

    def get_recipes_count(self, obj):
        """Получение общего количества рецептов автора."""
        return Recipe.objects.filter(author=obj.author).count()
