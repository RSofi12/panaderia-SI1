"""
Archivos del CU21.

El CSV se arma con el reporte dinámico: cada descarga vuelve a sumar.
El PDF se arma con el cierre ya guardado: no vuelve a leer venta.
"""
from decimal import Decimal

from django.utils import timezone

from apps.comercializacion.ventas.models import MetodoPago
from apps.comun.csv_reporte import archivo_csv, dinero_local
from apps.comun.pdf_reporte import HojaReporte, anchos_de, fecha_visible


def _dinero(valor) -> str:
    return f'{Decimal(valor):.2f}'


def _metodo(metodo_pago) -> str:
    if metodo_pago == MetodoPago.EFECTIVO:
        return 'Efectivo'
    if metodo_pago == MetodoPago.STRIPE:
        return 'Tarjeta'
    return 'Efectivo y tarjeta'


def _periodo(periodo: str) -> str:
    return {'dia': 'Día', 'semana': 'Semana', 'mes': 'Mes'}.get(periodo, periodo)


def csv_reporte(reporte: dict, metodo_pago=None) -> bytes:
    """Ventas del periodo, vueltas a sumar. No es el cierre congelado."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    return archivo_csv(
        'Reporte de ventas',
        [
            ('Desde', fecha_visible(reporte['desde'])),
            ('Hasta', fecha_visible(reporte['hasta'])),
            ('Método', _metodo(metodo_pago)),
            ('Generado el', generado),
        ],
        [
            ('Ventas', reporte['cantidad']),
            ('Total (Bs)', dinero_local(reporte['total'])),
            ('Efectivo (Bs)', dinero_local(reporte['efectivo'])),
            ('Tarjeta (Bs)', dinero_local(reporte['tarjeta'])),
        ],
        'Productos vendidos',
        ['Producto', 'Cantidad', 'Subtotal (Bs)'],
        [
            [producto['nombre'], producto['cantidad'], dinero_local(producto['subtotal'])]
            for producto in reporte['productos']
        ],
        'Este archivo vuelve a sumar las ventas del periodo. No es el cierre guardado.',
        vacio='Este periodo no tiene ventas.',
    )


def pdf_cierre(cierre: dict) -> bytes:
    """PDF del cierre ya guardado. No vuelve a sumar las ventas."""
    cuando = timezone.localtime(cierre['fecha_generacion']).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'{_periodo(cierre["periodo"])} del {fecha_visible(cierre["desde"])} '
        f'al {fecha_visible(cierre["hasta"])}   ·   '
        f'Método: {_metodo(cierre["metodo_pago"])}\n'
        f'Congelado el {cuando} por {cierre["generado_por"]}'
    )
    columnas = anchos_de(58, 18, 24)
    reporte = HojaReporte(f'Reporte de cierre de ventas {cierre["id_cierre"]}')
    reporte.abrir('Reporte de cierre de ventas', detalle)
    reporte.tarjetas([
        ('Ventas', str(cierre['cantidad'])),
        ('Total', f'Bs {_dinero(cierre["total"])}'),
        ('Efectivo', f'Bs {_dinero(cierre["efectivo"])}'),
        ('Tarjeta', f'Bs {_dinero(cierre["tarjeta"])}'),
    ])
    reporte.seccion('Productos vendidos')

    def encabezado():
        reporte.fila(
            [('Producto', 'izq'), ('Cantidad', 'der'), ('Subtotal', 'der')],
            columnas,
            encabezado=True,
        )

    encabezado()
    for indice, producto in enumerate(cierre['productos']):
        reporte.fila(
            [
                (producto['nombre'], 'izq'),
                (str(producto['cantidad']), 'der'),
                (f'Bs {_dinero(producto["subtotal"])}', 'der'),
            ],
            columnas,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )
    if not cierre['productos']:
        reporte.nota('Este periodo no tiene ventas.')
    reporte.nota('Estos números quedaron guardados y no se vuelven a calcular.')
    return reporte.cerrar()
