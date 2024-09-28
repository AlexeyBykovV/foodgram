from rest_framework import viewsets

from recipes.models import Tag, Ingredient, Recipe


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет Тегов"""

    queryset = Tag.objects.all()


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет Ингредиентов"""

    queryset = Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет Рецептов"""

    pass
