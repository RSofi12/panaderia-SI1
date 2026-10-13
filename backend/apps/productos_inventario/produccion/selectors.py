"""Consultas de solo lectura para el historial de producción."""

from .models import Produccion


def get_historial_produccion(fecha_desde=None, fecha_hasta=None, jornada=None, id_producto=None):
    """Devuelve el historial de producciones con filtros opcionales."""
    queryset = Produccion.objects.select_related('id_usuario').prefetch_related(
        'detalles__id_producto'
    )

    if fecha_desde:
        queryset = queryset.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha__lte=fecha_hasta)
    if jornada:
        queryset = queryset.filter(jornada=jornada)
    if id_producto:
        queryset = queryset.filter(detalles__id_producto=id_producto).distinct()

    return queryset.order_by('-fecha', '-id_produccion')
