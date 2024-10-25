import uuid

import pdfkit
from django.db.models import Exists, OuterRef, Prefetch, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.constants import SHORT_LINK_SIZE
from core.paginations import RecipePagination
from recipes.models import (FavoritesRecipe, Ingredient, Recipe,
                            RecipeIngredients, ShoppingCart, Tag)
from users.models import Subscriptions
from .filters import IngredientFilter, RecipesFilter
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoritesSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          ShoppingCartSerializer, TagSerializer)


class TagViewSet(ReadOnlyModelViewSet):
    """Класс для обработки запросов к модели Tag.

    :param queryset (QuerySet): Получение всех объектов модели Tag.
    :param serializer_class (TagSerializer): Сериализатор, используемый
    для преобразования данных модели Tag в формат JSON.
    :param permission_classes (AllowAny): Разрешения, разрешающие доступ
    к этому представлению любому пользователю, аутентифицированному или нет.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Класс для обработки запросов к модели Ingredient.

    :param queryset (QuerySet): Получение всех объектов модели Ingredient.
    :param serializer_class (IngredientSerializer): Сериализатор, используемый
    для преобразования данных модели Ingredient в формат JSON.
    :param permission_classes (AllowAny): Разрешения, разрешающие доступ
    к этому представлению любому пользователю, аутентифицированному или нет.
    :param filter_backends (DjangoFilterBackend): Позволяет использовать
    фильтрацию в представлении, чтобы ограничить количество объектов в ответе.
    :param filterset_class (IngredientFilter): Фильтрация по полю 'name'
    модели Ingredient.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Класс для обработки запросов к модели Recipe.

    :param queryset (QuerySet): Получение всех объектов модели Recipe.
    :param serializer_class (dict): Словарь сериализаторов, используемых
    для различных действий.
    :param permission_classes (IsOwnerOrReadOnly): Разрешения, ограничивающие
    доступ к этому представлению для владельца или для чтения.
    :param filter_backends (DjangoFilterBackend): Позволяет использовать
    фильтрацию в представлении, чтобы ограничить количество объектов в ответе.
    :param filterset_class (RecipesFilter): Фильтрация по полям модели Recipe.
    """

    http_method_names = ('get', 'post', 'patch', 'delete')
    pagination_class = RecipePagination
    permission_classes = (IsOwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipesFilter
    serializer_action_classes = {
        'list': RecipeSerializer,
        'retrieve': RecipeSerializer,
        'favorite': FavoritesSerializer,
        'shopping_cart': ShoppingCartSerializer,
    }

    def get_serializer_class(self):
        """Получает сериализатор в зависимости от применяемого действия.

        :return: Сериализатор, соответствующий текущему действию.
        """
        return self.serializer_action_classes.get(
            self.action, RecipeCreateSerializer
        )

    def get_queryset(self):
        """Возвращает набор запросов рецептов с учетом пользователя и действия.

        Если действие 'list' или 'retrieve', добавляет аннотации
        для избранных рецептов и рецептов в корзине покупок.
        Предварительно выбирает связанные объекты для оптимизации запросов.

        :return: Отсортированный набор запросов рецептов.
        """
        user = self.request.user
        recipes = Recipe.objects.select_related('author').prefetch_related(
            Prefetch(
                'recipe_ingredients',
                queryset=RecipeIngredients.objects.select_related('ingredient')
            ),
            'tags',
            Subscriptions.get_prefetch('author__subscribers', user)
        )

        if self.action in ['list', 'retrieve']:
            recipes = recipes.annotate(
                is_favorited=Exists(
                    FavoritesRecipe.objects.filter(
                        author_id=user.id, recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        author_id=user.id, recipe=OuterRef('pk')
                    )
                ),
            ).all()

        return recipes.order_by('-pub_date').all()

    @action(
        methods=['post'],
        detail=True,
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное.

        :param request: HTTP-запрос.
        :param pk: Первичный ключ рецепта.
        :return: HTTP-ответ с данными сериализатора и статусом 201 Created.
        """
        return self.add_recipe(request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного.

        :param request: HTTP-запрос.
        :param pk: Первичный ключ рецепта.
        :return: HTTP-ответ с соответствующим статусом.
        """
        return self.delete_recipe(request, pk, FavoritesRecipe)

    @action(
        methods=['post'],
        detail=True,
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок.

        :param request: HTTP-запрос.
        :param pk: Первичный ключ рецепта.
        :return: HTTP-ответ с данными сериализатора и статусом 201 Created.
        """
        return self.add_recipe(request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалаяет рецепт из списка покупок.

        :param request: HTTP-запрос.
        :param pk: Первичный ключ рецепта.
        :return: HTTP-ответ с соответствующим статусом.
        """
        return self.delete_recipe(request, pk, ShoppingCart)

    @action(methods=['get'], detail=False, url_name='download',)
    def download_shopping_cart(self, request):
        """Подготавливает и возвращает файл со списком покупок.

        :param request: HTTP-запрос.
        :return: HTTP-ответ с PDF-файлом списка покупок.
        """
        user = self.request.user
        ingredients = (
            RecipeIngredients.objects.filter(recipe__shoppingcart__author=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )

        if not ingredients:
            return HttpResponse(
                'Ваш список покупок пуст.', content_type='text/plain'
            )

        template = get_template('shopping_cart.html')
        context = {'ingredients': ingredients}
        html = template.render(context)

        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None
        }

        pdf = pdfkit.from_string(html, False, options=options)

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.pdf"'
        )
        return response

    @action(
        methods=['get'], detail=True, url_path='get-link', url_name='get_link'
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт.

        :param request: HTTP-запрос.
        :param pk: Первичный ключ рецепта.
        :return: HTTP-ответ с короткой ссылкой на рецепт.
        """
        recipe = self.get_object()
        if not recipe.short_link:
            while True:
                short_link = str(uuid.uuid4())[:SHORT_LINK_SIZE]
                if not Recipe.objects.filter(short_link=short_link).exists():
                    recipe.short_link = short_link
                    recipe.save()
                    break
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    f'/s/{recipe.short_link}'
                )
            },
            status=status.HTTP_200_OK
        )

    # @action(
    #     methods=['get'],
    #     detail=False,
    #     url_path='s/(?P<short_link>[^/.]+)',
    #     url_name='recipe_by_short_link'
    # )
    def retrieve_by_short_link(self, request, short_link=None):
        """Получение рецепта по короткой ссылке.

        :param request: HTTP-запрос.
        :param short_link: Короткая ссылка на рецепт.
        :return: HTTP-ответ с данными рецепта.
        """
        recipe = get_object_or_404(Recipe, short_link=short_link)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

    def add_recipe(self, request, pk):
        """Добавляет рецепт к автору.

        :param request: HTTP-запрос
        :param pk: Первичный ключ рецепта
        :return: HTTP-ответ с данными сериализатора и статусом 201 Created
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        data = {'recipe': recipe.id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, request, pk, model):
        """Удаляет рецепт, связанный с автором.

        :param request: HTTP-запрос
        :param pk: Первичный ключ рецепта
        :param model: Модель, с которой связаны рецепты и авторы
        :return: HTTP-ответ с соответствующим статусом
        """
        recipe = get_object_or_404(Recipe, pk=pk)

        deleted_count, _ = model.objects.filter(
            author=self.request.user,
            recipe=recipe,
        ).delete()

        if not deleted_count:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
