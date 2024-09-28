from django.contrib import admin

from .models import Tag, Recipe, Ingredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка модуля Тэг в админке"""

    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка модели Игредиентов в админке"""

    list_display = ('name', 'unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка модели Рецептов в админке"""

    list_display = ('author', 'title')
    search_fields = ('author', 'title')
    list_filter = ('tags',)
    # общее число добавлений в избранное
