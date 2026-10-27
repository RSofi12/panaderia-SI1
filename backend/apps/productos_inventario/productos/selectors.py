from datetime import datetime, time

from django.utils import timezone

from apps.productos_inventario.productos.models import HistorialPrecioProducto


def obtener_historial_precios_productos(
    *, id_producto=None, fecha_desde=None, fecha_hasta=None
):
    """CU19: devuelve cambios registrados, incluidos los de productos inactivos."""
    historial = HistorialPrecioProducto.objects.select_related('id_producto')

    if id_producto is not None:
        historial = historial.filter(id_producto_id=id_producto)

    # Los filtros representan días completos de la zona del negocio
    # (TIME_ZONE=America/La_Paz), independientemente de la zona activa.
    zona_horaria = timezone.get_default_timezone()
    if fecha_desde is not None:
        inicio = timezone.make_aware(
            datetime.combine(fecha_desde, time.min), zona_horaria
        )
        historial = historial.filter(fecha_inicio__gte=inicio)
    if fecha_hasta is not None:
        fin = timezone.make_aware(
            datetime.combine(fecha_hasta, time.max), zona_horaria
        )
        historial = historial.filter(fecha_inicio__lte=fin)

    return historial.order_by('-fecha_inicio', '-id_historial')
