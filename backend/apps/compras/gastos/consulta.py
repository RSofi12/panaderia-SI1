"""Lectura de los filtros del listado de movimientos económicos (CU20).

La tabla de la pantalla y los reportes usan esta misma lectura: mismo tipo,
misma categoría, mismo texto y mismo período. Por defecto el listado muestra
solo los movimientos vigentes; `?anulado=todos` incluye también los anulados.
"""
from datetime import date

from django.db.models import Q

from .models import (
    CategoriaMovimientoEconomico,
    MovimientoEconomico,
    TipoMovimientoEconomico,
)


def leer_filtros_gasto(params):
    """Devuelve (filtros, error). `error` es un dict listo para HTTP 400."""
    tipo = (params.get('tipo') or '').strip() or None
    categoria = (params.get('categoria') or '').strip() or None
    fecha_desde = params.get('fecha_desde') or None
    fecha_hasta = params.get('fecha_hasta') or None
    search = (params.get('search') or params.get('q') or '').strip() or None
    anulado_raw = (params.get('anulado') or '').strip().lower()

    if tipo and tipo not in TipoMovimientoEconomico.values:
        return None, {'tipo': f'Tipo inválido. Use {", ".join(TipoMovimientoEconomico.values)}.'}

    if categoria and categoria not in CategoriaMovimientoEconomico.values:
        return None, {
            'categoria': f'Categoría inválida. Use {", ".join(CategoriaMovimientoEconomico.values)}.'
        }

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

    if anulado_raw in ('', 'false', '0'):
        anulado = False
    elif anulado_raw in ('true', '1'):
        anulado = True
    elif anulado_raw in ('todos', 'all'):
        anulado = None
    else:
        return None, {'anulado': 'Valor inválido. Use true, false o todos.'}

    return {
        'tipo': tipo,
        'categoria': categoria,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'search': search,
        'anulado': anulado,
    }, None


def gastos_filtrados(filtros):
    """Listado de movimientos económicos, del más reciente al más antiguo."""
    queryset = MovimientoEconomico.objects.select_related('id_usuario')

    if filtros.get('tipo'):
        queryset = queryset.filter(tipo=filtros['tipo'])
    if filtros.get('categoria'):
        queryset = queryset.filter(categoria=filtros['categoria'])
    if filtros.get('anulado') is not None:
        queryset = queryset.filter(anulado=filtros['anulado'])
    if filtros.get('fecha_desde'):
        queryset = queryset.filter(fecha_hora__date__gte=filtros['fecha_desde'])
    if filtros.get('fecha_hasta'):
        queryset = queryset.filter(fecha_hora__date__lte=filtros['fecha_hasta'])

    search = filtros.get('search')
    if search:
        if search.isdigit():
            queryset = queryset.filter(
                Q(id_movimiento=int(search))
                | Q(concepto__icontains=search)
                | Q(descripcion__icontains=search)
            )
        else:
            queryset = queryset.filter(
                Q(concepto__icontains=search) | Q(descripcion__icontains=search)
            )

    return queryset.order_by('-fecha_hora', '-id_movimiento')
