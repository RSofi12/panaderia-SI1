from rest_framework.pagination import PageNumberPagination


class PaginacionHistorialPrecios(PageNumberPagination):
    """Conserva páginas de diez registros en CU19 sin cambiar otros listados."""

    page_size = 10
