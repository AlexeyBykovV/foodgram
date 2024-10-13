from rest_framework.pagination import PageNumberPagination

from .constants import PAGE_SIZE_MAX


class RecipePagination(PageNumberPagination):
    """Пагинация для проекта"""

    page_size = PAGE_SIZE_MAX
    page_size_query_param = 'limit'
