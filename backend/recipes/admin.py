from django.contrib import admin

from .models import (
    FavoritesRecipe, Ingredient, Recipe, RecipeIngredients, ShoppingCart, Tag, 
)


class RecipeIngredientsInline(admin.TabularInline):
    """Строчное представление Ингредиента в Рецепте"""

    model = RecipeIngredients
    min_num = 1


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

    list_display = ('name', 'author', 'in_favourites')
    list_display_links = ('name',)
    search_fields = ('author', 'name')
    list_filter = ('tags',)
    inlines = [RecipeIngredientsInline]

    @admin.display(description='В избранном')
    def in_favourites(self, obj):
        """Количество добавлений рецептов в избранном"""
        return obj.favorites.count()


@admin.register(FavoritesRecipe)
class FavouritesRecipeAdmin(admin.ModelAdmin):
    """Настройка модели Избранного в админке"""


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка модели Список покупок в админке"""


