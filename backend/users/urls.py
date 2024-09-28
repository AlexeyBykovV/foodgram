from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet


user_router_v1 = routers.DefaultRouter()
user_router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/', include(user_router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
