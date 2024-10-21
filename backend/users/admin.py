from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import Subscriptions, User


@admin.register(User)
# class CustomUserAdmin(admin.ModelAdmin):
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'subscribers_count',
        'recipes_count',
    )
    search_fields = ('email', 'username')

    def subscribers_count(self, obj):
        """Возвращает количество подписчиков у пользователя."""
        return obj.subscribers.count()

    def recipes_count(self, obj):
        """Возвращает количество рецептов, созданных пользователем."""
        return obj.recipes.count()


admin.register(Subscriptions)
admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
