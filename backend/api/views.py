import pdfkit
import uuid

from django.db.models import Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.template.loader import get_template
from django.http import HttpResponse
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from fpdf import FPDF
# from shortuuid import uuid

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

    @action(methods=['get'], detail=False, url_name='download',)
    def download_shopping_cart(self, request):
        """Подготавливает и возвращает файл со списком покупок"""
        user = self.request.user
        shopping_cart = ShoppingCart.objects.filter(author=user)
        recipes = Recipe.objects.filter(shoppingcart__in=shopping_cart)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', size=15)
        pdf.cell(200, 10, txt='Список покупок', ln=True, align='C')

        ingredients = {}
        for recipe in recipes:
            for ingredient in recipe.recipe_ingredients.all():
                name = ingredient.ingredient.name
                amount = ingredient.amount
                measurement_unit = ingredient.ingredient.measurement_unit
                if name in ingredients:
                    ingredients[name]['amount'] += amount
                else:
                    ingredients[name] = {
                        'amount': amount, 'measurement_unit': measurement_unit
                    }

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
        """Получение короткой ссылки на рецепт"""
        recipe = self.get_object()
        if not recipe.short_link:
            while True:
                short_link = str(uuid.uuid4())[:8]
                if not Recipe.objects.filter(short_link=short_link).exists():
                    recipe.short_link = short_link
                    recipe.save()
                    break
        return Response(
            {'short_link': request.build_absolute_uri(
                    f'/recipes/short/{recipe.short_link}'
                )},
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='short/(?P<short_link>[^/.]+)', url_name='recipe_by_short_link')
    def retrieve_by_short_link(self, request, short_link=None):
        """Получение рецепта по короткой ссылке"""
        recipe = get_object_or_404(Recipe, short_link=short_link)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

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
