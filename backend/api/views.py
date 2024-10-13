from django.db.models import Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.paginations import RecipePagination
from recipes.models import (
    Ingredient, Tag, Recipe, RecipeIngredients, FavoritesRecipe, ShoppingCart
)
from users.models import Subscriptions
from .filters import IngredientFilter, RecipesFilter
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    FavoritesSerializer,
    ShoppingCartSerializer,
)


class TagViewSet(ReadOnlyModelViewSet):
    """Класс используется для обработки запросов к модели Tag.

    Атрибуты класса:
    - queryset: получение всех объектов модели Tag.
    - serializer_class: TagSerializer - сериализатор, который будет
    использоваться для преобразования данных модели Review в формат JSON.
    - permission_classes: AllowAny, доступ к этому представлению разрешен
    для любого пользователя, аутентифицированного или нет.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Класс используется для обработки запросов к модели Ingredient.

    Атрибуты класса:
    - queryset: получение всех объектов модели Ingredient.
    - serializer_class: TagSerializer - сериализатор, который будет
    использоваться для преобразования данных модели Review в формат JSON.
    - permission_classes: AllowAny, доступ к этому представлению разрешен
    для любого пользователя, аутентифицированного или нет.
    - filter_backends : DjangoFilterBackend, позволяет использовать фильтрацию
    в представлении, чтобы ограничить количество объектов в ответе.
    - filterset_class : IngredientFilter, фильтрация
    по полю 'name' модели Ingredient.
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Класс используется для обработки запросов к модели Recipe.

    Атрибуты класса:
    - queryset: получение всех объектов модели Ingredient.
    - serializer_class: TagSerializer - сериализатор, который будет
    использоваться для преобразования данных модели Review в формат JSON.
    - permission_classes: AllowAny, доступ к этому представлению разрешен
    для любого пользователя, аутентифицированного или нет.
    - filter_backends : DjangoFilterBackend, позволяет использовать фильтрацию
    в представлении, чтобы ограничить количество объектов в ответе.
    - filterset_class : IngredientFilter, фильтрация
    по полю 'name' модели Ingredient.
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
        # 'get_link': ShortUrlSerializer,
    }

    def get_serializer_class(self):
        """Получает сериализатор в зависимости от применяемого действия."""
        return self.serializer_action_classes.get(
            self.action, RecipeCreateSerializer
        )

    def get_queryset(self):
        """Возвращает набор запросов рецептов с учетом пользователя и действия.

        - Если действие 'list' или 'retrieve', добавляет аннотации
        для избранных рецептов и рецептов в корзине покупок.
        - Предварительно выбирает связанные объекты для оптимизации запросов.

        :return: Отсортированный набор запросов рецептов
        """
        user = self.request.user
        recipes = Recipe.objects

        if self.action in ['list', 'retrieve']:
            subscriptions_prefetch = Subscriptions.get_prefetch(
                'author__subscribers', user
            )
            ingredients_related = RecipeIngredients.objects.select_related(
                'ingredient'
            )
            recipes = recipes.select_related('author').prefetch_related(
                Prefetch('recipe_ingredients', queryset=ingredients_related),
                'tags',
                subscriptions_prefetch
            ).annotate(
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

    @action(methods=['post'], detail=True, url_name='favorite',)
    def favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        return self.add_recipe(request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        return self.delete_recipe(request, pk, FavoritesRecipe)

    @action(methods=['post'], detail=True, url_name='shopping_cart',)
    def shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        return self.add_recipe(request, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        """Удалаяет рецепт из списка покупок."""
        return self.delete_recipe(request, pk, ShoppingCart)

    # @action(methods=['get'], detail=False, url_name='download',)
    # def download_shopping_cart(self, request):
    #     """Подготавливает и возвращает файл со списком покупок"""


    # @action(methods=['get'], detail=True, url_name='get_link')
    # def get_link(self, request, pk=None):
    #     """Получение короткой ссылки на рецепт"""

    def add_recipe(self, request, pk):
        """Добавляет рецепт к автору.

        :param request: HTTP-запрос
        :param pk: Первичный ключ рецепта
        :return: HTTP-ответ с данными сериализатора и статусом 201 Created
        """
        data = {'recipe': pk}
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

        if deleted_count == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)
