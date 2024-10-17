from django.contrib import admin

from .models import Subscriptions, User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name', 'email')
    search_fields = ('email', 'username')


admin.register(Subscriptions)
