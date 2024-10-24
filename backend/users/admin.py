from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import Subscriptions, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Настройка модели User в админке"""
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'subscribers_count',
        'recipes_count',
    )
    list_display_links = ('username',)
    search_fields = ('email', 'username')

    @admin.display(description='Подписчиков')
    def subscribers_count(self, obj):
        """Возвращает количество подписчиков у пользователя."""
        return obj.subscribers.count()

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        """Возвращает количество рецептов, созданных пользователем."""
        return obj.recipes.count()


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    """Настройка модели Subscriptions в админке"""
    list_display = (
        'id',
        'user',
        'author'
    )
    list_display_links = ('user',)
    search_fields = ('user__email',)


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
