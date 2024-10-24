from django.contrib.auth import get_user_model

from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (CurrentUserDefault, IntegerField,
                                        ModelSerializer, SerializerMethodField,
                                        SlugRelatedField, ValidationError)
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Recipe
from .models import Subscriptions

User = get_user_model()


class UserSerializer(ModelSerializer):
    """Сериализатор для представления пользователей
    с информацией о подписках.
    """
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
        """Определяет, подписан ли текущий пользователь
        на данного пользователя.

        :param obj: Объект пользователя, информацию
        о подписке которого проверяем.
        :return bool: True, если текущий пользователь подписан
        на данного пользователя, иначе False.
        """
        request = self.context.get('request')
        current_user = request.user if request else None

        if (
            current_user
            and current_user.is_authenticated
            and current_user != obj
        ):
            return obj.subscribers.filter(user=current_user).exists()

        return False


class UserAvatarSerializer(ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class UserRecipeSerializer(UserSerializer):
    """Сериализатор для представления рецептов пользователя."""

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
        """Получение рецептов автора.

        :param obj: Объект пользователя, чьи рецепты мы хотим получить.
        :return list: Список сериализованных рецептов автора.
        """
        from api.serializers import RecipeGetSerializer

        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj)

        if limit:
            queryset = queryset[:int(limit)]

        return RecipeGetSerializer(queryset, many=True).data


class UserSubscriptionsSerializer(ModelSerializer):
    """Сериализатор для представления подписок пользователя."""

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
        validators = (
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('author', 'user'),
                message='Вы уже подписаны на этого пользователя.',
            ),
        )

    def validate_author(self, author):
        """Проверка, что пользователь не пытается подписаться на себя.

        :param author: Пользователь, на которого пытаются подписаться.
        :return User: Проверенный объект автора.
        :raises ValidationError: Если пользователь пытается подписаться
        на себя.
        """
        if self.context['request'].user == author:
            raise ValidationError(
                'Вы пытаетесь подписаться на самого себя.'
            )
        return author

    def to_representation(self, instance):
        """Преобразует объект подписки в представление пользователя
        с рецептами.

        :param instance: Объект подписки для преобразования.
        :return dict: Сериализованные данные автора подписки.
        """
        if not isinstance(instance, Subscriptions):
            raise TypeError('Ожидается объект Subscriptions.')

        serializer = UserRecipeSerializer(
            instance.author, context=self.context
        )
        return serializer.data

    def get_is_subscriber(self, obj):
        """Проверка подписки пользователя на автора.

        :param obj (Subscriptions): Объект подписки.
        :return bool: True, если пользователь подписан на автора, иначе False.
        """
        return Subscriptions.objects.filter(
            user=obj.user, author=obj.author
        ).exists()

    def get_recipes_count(self, obj):
        """Получение общего количества рецептов автора.

        :param obj (Subscriptions): Объект подписки.
        :return: Количество рецептов автора.
        """
        return Recipe.objects.filter(author=obj.author).count()
