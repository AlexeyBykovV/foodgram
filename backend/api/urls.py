from django.urls import include, path
from rest_framework import routers

from .views import TagViewSet, RecipeViewSet, IngredientViewSet


api_router_v1 = routers.DefaultRouter()
api_router_v1.register('tags', TagViewSet, basename='tag')
api_router_v1.register('recipes', RecipeViewSet, basename='recipe')
api_router_v1.register(
    'ingredients', IngredientViewSet, basename='ingredient'
)

urlpatterns = [
    path('v1/', include(api_router_v1.urls)),
]
