from django.urls import include, path
from rest_framework import routers

from users.views import UserViewSet
from .views import TagViewSet, RecipeViewSet, IngredientViewSet

app_name = 'api'

api_router_v1 = routers.DefaultRouter()
api_router_v1.register('tags', TagViewSet, basename='tag')
api_router_v1.register('recipes', RecipeViewSet, basename='recipe')
api_router_v1.register(
    'ingredients', IngredientViewSet, basename='ingredient'
)

user_router_v1 = routers.DefaultRouter()
user_router_v1.register('users', UserViewSet, basename='users')


urlpatterns = [
    path('', include(api_router_v1.urls)),
    path('', include(user_router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
