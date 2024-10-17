from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser import views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.paginations import RecipePagination

from .models import Subscriptions
from .serializers import UserAvatarSerializer, UserSubscriptionsSerializer

User = get_user_model()


class UserViewSet(views.UserViewSet):
    """ViewSet для работы с пользователями и подписками."""

    pagination_class = RecipePagination

    def get_queryset(self):
        """Возвращает queryset пользователей в зависимости от действия.

        :return: QuerySet: Список пользователей или подписок
        в зависимости от действия.
        """
        user = self.request.user
        user_prefetch = Subscriptions.get_prefetch('subscribers', user)
        base_queryset = User.objects.prefetch_related(
            user_prefetch
        ).order_by('id')

        action_queryset_map = {
            'list': lambda: base_queryset,
            'retrieve': lambda: base_queryset,
            'subscriptions': lambda: self.get_subscriptions_queryset(user),
            'change_subscribe': lambda: base_queryset,
        }

        return action_queryset_map.get(
            self.action, lambda: User.objects.all()
        )()

    def get_subscriptions_queryset(self, user):
        """Возвращает queryset для подписок указанного пользователя.

        :param user: Пользователь, для которого нужно получить подписки.
        :return QuerySet: Список подписок пользователя.
        """
        author_prefetch = Subscriptions.get_prefetch(
            'author__subscribers', user
        )

        return (Subscriptions.objects.filter(user=user)
                .prefetch_related(author_prefetch, 'author__recipes')
                .order_by('id'))

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        """Возвращает данные о текущем пользователе.

        :param request: HTTP-запрос.
        :return Response: Данные о текущем пользователе.
        """
        return super().me(request, *args, **kwargs)

    @action(
        methods=['put'],
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
        url_name='me/avatar',
    )
    def update_avatar(self, request):
        """Обновляет аватар текущего пользователя.

        :param request: HTTP-запрос с данными аватара.
        :return Response: Данные обновленного аватара.
        """
        serializer = self.change_avatar(request.data)
        return Response(serializer.data)

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаляет аватар текущего пользователя.

        :param request: HTTP-запрос.
        :return Response: Статус удаления аватара.
        """
        serializer = self.change_avatar({'avatar': None})
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def change_avatar(self, data):
        """Изменяет аватар пользователя.

        :param data: Данные для обновления аватара.
        :return UserAvatarSerializer: Сериализованные данные пользователя
        с обновленным аватаром.
        """
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
    def get_subscriptions(self, request):
        """Возвращает список подписок текущего пользователя.

        :param request: HTTP-запрос.
        :return Response: Список подписок с пагинацией.
        """
        queryset = Subscriptions.objects.filter(user=request.user)

        return self.paginate_and_serialize(
            queryset, UserSubscriptionsSerializer, request
        )

    def paginate_and_serialize(self, queryset, serializer_class, request):
        """Пагинирует и сериализует queryset.

        :param queryset: Данные для пагинации и сериализации.
        :param serializer_class: Класс сериализатора для данных.
        :param request: HTTP-запрос.
        :return Response: Сериализованные данные с пагинацией.
        """
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = serializer_class(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(
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
    def add_subscribe(self, request, id):
        """Добавляет подписку на пользователя.

        :param request: HTTP-запрос с данными подписки.
        :param id (int): ID пользователя, на которого подписываются.
        :return Response: Данные о созданной подписке.
        """
        author = get_object_or_404(User, id=id)
        serializer = UserSubscriptionsSerializer(
            data={'author': author},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_subscribe.mapping.delete
    def unsubcribe(self, request, id):
        """Удаляет подписку на пользователя.

        :param request: HTTP-запрос.
        :param id (int): ID пользователя, подписка на которого удаляется.
        :return Response: Статус удаления подписки или сообщение об ошибке.
        """
        author = get_object_or_404(User, id=id)
        subscription_deleted, _ = Subscriptions.objects.filter(
            author=author, user=request.user
        ).delete()

        if subscription_deleted == 0:
            return Response(
                {'detail': 'Подписка не найдена.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
