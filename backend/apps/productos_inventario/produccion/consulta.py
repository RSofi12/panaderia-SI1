"""Lectura de los filtros del historial de producción (CU11).

La lista de la pantalla y la descarga usan esta misma lectura, así el
archivo responde al mismo período y a la misma jornada.
"""
from datetime import date


def leer_filtros_historial(params):
    """Devuelve (filtros, error). `error` es un dict listo para HTTP 400."""
    fecha_desde = params.get('fecha_desde') or None
    fecha_hasta = params.get('fecha_hasta') or None
    jornada = params.get('jornada') or None
    id_producto = params.get('id_producto') or None

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

    if id_producto:
        try:
            int(id_producto)
        except (ValueError, TypeError):
            return None, {'id_producto': 'El identificador de producto debe ser un número entero válido.'}

    return {
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'jornada': jornada,
        'id_producto': id_producto,
    }, None
