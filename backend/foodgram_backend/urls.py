from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:short_link>/',
        RecipeViewSet.as_view({'get': 'retrieve_by_short_link'}),
        name='recipe_by_short_link'
    ),
]
