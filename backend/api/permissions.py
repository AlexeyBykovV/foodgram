from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Определяет права доступа к объектам.

    Этот класс разрешает всем пользователям выполнять операции
    чтения (GET, HEAD, OPTIONS) на объектах. Однако только автор
    объекта имеет право редактировать (PUT, PATCH, DELETE) его.

    Права доступа:
    - Чтение: доступно всем пользователям.
    - Запись: доступно только автору объекта.

    Методы:
    - has_permission: Проверяет, имеет ли пользователь разрешение
    на выполнение действия (например, создание, редактирование, удаление).
    - has_object_permission: Проверяет, имеет ли пользователь
    разрешение на доступ к конкретному объекту.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет, имеет ли пользователь разрешение на доступ к объекту.

        :param request: Объект запроса, содержащий информацию
        о текущем пользователе и методе.
        :param view: Представление, обрабатывающее запрос.
        :param obj: Объект, к которому проверяются права доступа.
        :return: True, если доступ разрешен, иначе False.
        """
        return request.method in SAFE_METHODS or obj.author == request.user

    def has_permission(self, request, view):
        """Проверяет, имеет ли пользователь разрешение на выполнение действия.

        :param request: Объект запроса.
        :param view: Представление, обрабатывающее запрос.
        :return: True, если доступ разрешен, иначе False.
        """

        if request.method not in SAFE_METHODS:
            return request.user.is_authenticated
        return True
