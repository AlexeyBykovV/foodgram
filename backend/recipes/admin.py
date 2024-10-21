from django.contrib import admin

from .models import FavoritesRecipe, Ingredient, Recipe, ShoppingCart, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка модуля Тэг в админке"""

    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка модели Игредиентов в админке"""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка модели Рецептов в админке"""

    list_display = ('author', 'name', 'ingredients', 'tags', 'in_favourites')
    search_fields = ('author', 'name')
    list_filter = ('tags',)

    def in_favourites(self, obj):
        """Количество добавлений рецептов в избранном"""
        # return FavoritesRecipe.objects.filter(recipe=obj).count()
        return obj.favorites.count()

    # В админке должна быть возможность создать полноценный рецепт.


@admin.register(FavoritesRecipe)
class FavouritesRecipeAdmin(admin.ModelAdmin):
    """Настройка модели Избранного в админке"""


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка модели Список покупок в админке"""
