"""
Exportación de archivos del CU21 (Reporte dinámico de ventas).

El CSV y el PDF se generan en tiempo real sobre las ventas calculadas del periodo.
Permite seleccionar dinámicamente qué columnas incluir en la exportación PDF y CSV.
"""
import csv
import io
from decimal import Decimal

from django.utils import timezone

from apps.comercializacion.ventas.models import MetodoPago
from apps.reportes.formatos.csv_reporte import dinero_local
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible


def _dinero(valor) -> str:
    return f'{Decimal(valor):.2f}'


def _metodo(metodo_pago) -> str:
    if metodo_pago == MetodoPago.EFECTIVO:
        return 'Efectivo'
    if metodo_pago == MetodoPago.STRIPE:
        return 'Tarjeta'
    return 'Efectivo y tarjeta'


def csv_reporte(reporte: dict, metodo_pago=None, columnas: list[str] | None = None) -> bytes:
    """Genera archivo CSV estructurado con las ventas y productos calculados en tiempo real."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    ventas = reporte.get('ventas', [])
    productos = reporte.get('productos', [])

    cols_def = [
        ('comprobante', 'Nº Comprobante', lambda v: f"#{v['numero_comprobante']}"),
        ('fecha', 'Fecha y Hora', lambda v: v.get('fecha_hora', v.get('fecha', ''))),
        ('metodo', 'Método de Pago', lambda v: _metodo(v['metodo_pago'])),
        ('cajero', 'Cajero', lambda v: v.get('cajero', 'Sistema')),
        ('total', 'Total (Bs)', lambda v: dinero_local(v['total'])),
    ]

    if columnas:
        cols_activas = [c for c in cols_def if c[0] in columnas]
        if not cols_activas:
            cols_activas = cols_def
    else:
        cols_activas = cols_def

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Panadería Santiago'])
    writer.writerow(['Reporte de ventas'])
    for etiqueta, valor in [
        ('Desde', fecha_visible(reporte['desde'])),
        ('Hasta', fecha_visible(reporte['hasta'])),
        ('Método', _metodo(metodo_pago)),
        ('Generado el', generado),
    ]:
        writer.writerow([etiqueta, valor])
    writer.writerow([])
    writer.writerow(['Resumen'])
    for etiqueta, valor in [
        ('Ventas', reporte['cantidad']),
        ('Total (Bs)', dinero_local(reporte['total'])),
        ('Efectivo (Bs)', dinero_local(reporte['efectivo'])),
        ('Tarjeta (Bs)', dinero_local(reporte['tarjeta'])),
    ]:
        writer.writerow([etiqueta, valor])
    writer.writerow([])
    writer.writerow(['Detalle de Ventas Registradas'])
    writer.writerow([c[1] for c in cols_activas])
    if ventas:
        for v in ventas:
            writer.writerow([c[2](v) for c in cols_activas])
    else:
        writer.writerow(['Este periodo no tiene transacciones registradas.'])
    writer.writerow([])
    writer.writerow(['Productos vendidos'])
    writer.writerow(['Producto', 'Cantidad', 'Subtotal (Bs)'])
    if productos:
        for p in productos:
            writer.writerow([p['nombre'], p['cantidad'], dinero_local(p['subtotal'])])
    else:
        writer.writerow(['Este periodo no tiene productos vendidos.'])
    writer.writerow([])
    writer.writerow(['Este archivo refleja las ventas registradas del periodo en tiempo real.'])
    return buffer.getvalue().encode('utf-8-sig')


def pdf_reporte_ventas(reporte: dict, metodo_pago=None, columnas: list[str] | None = None) -> bytes:
    """
    Genera documento PDF formal del reporte de ventas con tabla de columnas dinámicas.
    Permite elegir qué columnas se incluyen (comprobante, fecha, metodo, cajero, total).
    """
    cuando = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Período: del {fecha_visible(reporte["desde"])} al {fecha_visible(reporte["hasta"])}   ·   '
        f'Método: {_metodo(metodo_pago)}\n'
        f'Generado el {cuando}'
    )

    hoja = HojaReporte('Reporte de Ventas')
    hoja.abrir('Reporte de Ventas', detalle)
    hoja.tarjetas([
        ('Ventas', str(reporte['cantidad'])),
        ('Total', f'Bs {_dinero(reporte["total"])}'),
        ('Efectivo', f'Bs {_dinero(reporte["efectivo"])}'),
        ('Tarjeta', f'Bs {_dinero(reporte["tarjeta"])}'),
    ])

    ventas = reporte.get('ventas', [])

    col_map = {
        'comprobante': {
            'titulo': 'Nº Comp.',
            'alineacion': 'izq',
            'ancho': 18,
            'valor': lambda v: f"#{v['numero_comprobante']}",
        },
        'fecha': {
            'titulo': 'Fecha y Hora',
            'alineacion': 'izq',
            'ancho': 27,
            'valor': lambda v: v.get('fecha_hora', v.get('fecha', '')),
        },
        'metodo': {
            'titulo': 'Método',
            'alineacion': 'izq',
            'ancho': 20,
            'valor': lambda v: _metodo(v['metodo_pago']),
        },
        'cajero': {
            'titulo': 'Cajero',
            'alineacion': 'izq',
            'ancho': 20,
            'valor': lambda v: v.get('cajero', 'Sistema'),
        },
        'total': {
            'titulo': 'Total (Bs)',
            'alineacion': 'der',
            'ancho': 15,
            'valor': lambda v: f"Bs {_dinero(v['total'])}",
        },
    }

    if columnas:
        claves = [c for c in columnas if c in col_map]
        if not claves:
            claves = list(col_map.keys())
    else:
        claves = list(col_map.keys())

    anchos = anchos_de(*[col_map[k]['ancho'] for k in claves])

    hoja.seccion('Detalle de Ventas del Período')

    def encabezado():
        hoja.fila(
            [(col_map[k]['titulo'], col_map[k]['alineacion']) for k in claves],
            anchos,
            encabezado=True,
        )

    encabezado()
    for indice, venta in enumerate(ventas):
        hoja.fila(
            [
                (col_map[k]['valor'](venta), col_map[k]['alineacion'])
                for k in claves
            ],
            anchos,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )

    if not ventas:
        hoja.nota('Este período no tiene transacciones registradas.')

    hoja.nota('Reporte generado automáticamente desde el Sistema Panadería Santiago.')
    return hoja.cerrar()
