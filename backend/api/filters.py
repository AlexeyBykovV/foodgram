from django.contrib.auth import get_user_model
from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    ModelChoiceFilter,
    AllValuesMultipleFilter,
)

from recipes.models import Ingredient, Recipe


User = get_user_model()


class IngredientFilter(FilterSet):
    """Фильтр для модели Ingredients по имени."""

    name = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipesFilter(FilterSet):
    """Фильтр для модели Recipe.
    Фильтруем по автору, тэгу, избранному, списку покупок.
    """

    author = ModelChoiceFilter(queryset=User.objects.all())
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__author=self.request.user)
        return queryset.objects.all()

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(shoppingcart__author=self.request.user)
        return queryset.objects.all()