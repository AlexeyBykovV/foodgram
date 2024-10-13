from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Класс определяющий права доступа.

    Любой пользователь может читать объекты (GET, HEAD, OPTIONS).
    Только пользователь может редактировать объекты (PUT, PATCH, DELETE).
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user and request.user.is_staff
        )


class IsOwnerOrReadOnly(BasePermission):
    """Класс определяющий права доступа.

    Любой пользователь может читать объекты (GET, HEAD, OPTIONS).
    Только автор может редактировать объекты (PUT, PATCH, DELETE).
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
