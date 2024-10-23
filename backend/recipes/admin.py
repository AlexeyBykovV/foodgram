from django.contrib import admin

from .models import (FavoritesRecipe, Ingredient, Recipe,
                     RecipeIngredients, ShoppingCart, Tag)


class RecipeIngredientsInline(admin.TabularInline):
    """Строчное представление Ингредиента в Рецепте"""

    model = RecipeIngredients
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка модели Тэг в админке"""

    list_display = ('name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка модели Игредиентов в админке"""

    list_display = ('name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка модели Рецептов в админке"""

    list_display = ('name', 'author', 'in_favourites')
    list_display_links = ('name',)
    search_fields = ('name', 'author')
    list_filter = ('tags',)
    inlines = [RecipeIngredientsInline]

    @admin.display(description='В избранном')
    def in_favourites(self, obj):
        """Количество добавлений рецептов в избранное."""
        return obj.favorites.count()


@admin.register(FavoritesRecipe, ShoppingCart)
class FavouritesRecipeAdmin(admin.ModelAdmin):
    """Настройка модели Избранного/Списка покупок в админке"""

    list_display = ('id', 'recipe', '__str__')
    list_display_links = ('id', 'recipe')
