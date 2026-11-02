"""Lectura de los filtros del listado de compras (CU7).

La tabla de la pantalla y la descarga usan esta misma lectura, así el
archivo responde al mismo proveedor, al mismo texto y al mismo período.
"""
from datetime import date

from django.db.models import Count, Q

from .models import Compra


def leer_filtros_compra(params):
    """Devuelve (filtros, error). `error` es un dict listo para HTTP 400."""
    fecha_desde = params.get('fecha_desde') or None
    fecha_hasta = params.get('fecha_hasta') or None
    id_proveedor = params.get('id_proveedor') or None
    search = (params.get('search') or params.get('q') or '').strip() or None

    if fecha_desde:
        try:
            date.fromisoformat(fecha_desde)
        except ValueError:
            return None, {'fecha_desde': 'Formato de fecha_desde inválido. Use AAAA-MM-DD.'}

    if fecha_hasta:
        try:
            date.fromisoformat(fecha_hasta)
        except ValueError:
            return None, {'fecha_hasta': 'Formato de fecha_hasta inválido. Use AAAA-MM-DD.'}

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        return None, {'fecha_desde': 'La fecha inicial no puede ser mayor que la fecha final.'}

    if id_proveedor:
        try:
            id_proveedor = int(id_proveedor)
        except (TypeError, ValueError):
            return None, {'id_proveedor': 'El identificador de proveedor debe ser un número entero válido.'}

    return {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'id_proveedor': id_proveedor,
        'search': search,
    }, None


def compras_filtradas(filtros):
    """Listado de cabeceras, de la más reciente a la más antigua."""
    queryset = (
        Compra.objects.select_related('id_proveedor', 'id_usuario')
        .annotate(cantidad_lineas=Count('detalles'))
        .order_by('-fecha_hora', '-id_compra')
    )

    if filtros.get('id_proveedor'):
        queryset = queryset.filter(id_proveedor_id=filtros['id_proveedor'])
    if filtros.get('fecha_desde'):
        queryset = queryset.filter(fecha_hora__date__gte=filtros['fecha_desde'])
    if filtros.get('fecha_hasta'):
        queryset = queryset.filter(fecha_hora__date__lte=filtros['fecha_hasta'])

    search = filtros.get('search')
    if search:
        if search.isdigit():
            queryset = queryset.filter(
                Q(id_compra=int(search)) | Q(id_proveedor__nombre__icontains=search)
            )
        else:
            queryset = queryset.filter(id_proveedor__nombre__icontains=search)

    return queryset
