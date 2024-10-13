from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser import views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscriptions
from .serializers import UserAvatarSerializer, UserSubscriptionsSerializer
from core.paginations import RecipePagination

User = get_user_model()


class UserViewSet(views.UserViewSet):
    """Класс определяющий работу моделей User и Subscriptions."""

    pagination_class = RecipePagination

    def get_queryset(self):
        """Получение данных пользователя и подписки пользователя."""
        user = self.request.user
        user_prefetch = Subscriptions.get_prefetch('subscribers', user)

        if self.action in ('list', 'retrieve'):
            return (
                User.objects.prefetch_related(user_prefetch)
                .order_by('id')
                .all()
            )

        elif self.action in ('subscriptions',):
            author_prefetch = Subscriptions.get_prefetch(
                'author__subscribers', user
            )
            return (
                Subscriptions.objects.filter(user=user)
                .prefetch_related(author_prefetch, 'author__recipes')
                .order_by('id')
                .all()
            )

        elif self.action in ('change_subscribe',):
            return User.objects.prefetch_related(user_prefetch).all()

        return User.objects.all()

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        """Данные о себе"""
        return super().me(request, *args, **kwargs)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
        url_name='avatar',
    )
    def avatar(self, request):
        """Метод для работы с аватаром."""
        serializer = self.change_avatar(request.data)
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Метод для удаления автара."""
        serializer = self.change_avatar({'avatar': None})
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def change_avatar(self, data):
        """Метод для изменения аватара."""
        instance = self.get_instance()
        serializer = UserAvatarSerializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
        url_name='subscriptions',
    )
    def get_subscriptons(self, request):
        """Метод для получения подписки."""
        queryset = Subscriptions.objects.filter(user=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscriptionsSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscriptionsSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Метод для добавления подписки пользователя."""
        author = get_object_or_404(User, id=id)
        serializer = UserSubscriptionsSerializer(
            data={'author': author},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def undo_subcribe(self, request, id):
        """Метод для удаления подписки пользователя."""
        author = get_object_or_404(User, id=id)
        subscription_deleted, _ = Subscriptions.objects.filter(
            author=author, user=request.user
        ).delete()

        if subscription_deleted == 0:
            return Response(
                {'detail': 'Subscription not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
