from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Определяет права доступа к объектам.

    Данный класс разрешает всем пользователям
    выполнять операции чтения (GET, HEAD, OPTIONS) на объектах,
    в то время как только автор объекта имеет
    право редактировать (PUT, PATCH, DELETE) его.

    Права доступа:
    - Чтение: доступно всем пользователям.
    - Запись: доступно только автору объекта.
    """

    def has_object_permission(self, request, view, obj):
        """Проверяет, имеет ли пользователь разрешение на доступ к объекту.

        :param request: Объект запроса, содержащий информацию
        о текущем пользователе и методе.
        :param view: Представление, обрабатывающее запрос.
        :param obj: Объект, к которому проверяются права доступа.
        :return: True, если доступ разрешен, иначе False.
        """
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
