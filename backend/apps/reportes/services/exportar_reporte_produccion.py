"""
Exportación CSV y PDF del reporte de producción (CU22).

Las columnas del detalle de jornadas se pueden elegir, igual que en CU21.
"""
import csv
import io
from decimal import Decimal

from django.utils import timezone

from apps.productos_inventario.produccion.models import JornadaProduccion
from apps.reportes.formatos.csv_reporte import dinero_local
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible


def _dinero(valor) -> str:
    return f'{Decimal(valor):.2f}'


def _etiqueta_jornada(jornada) -> str:
    if not jornada:
        return 'Todas las jornadas'
    etiquetas = dict(JornadaProduccion.choices)
    return etiquetas.get(jornada, str(jornada))


def _columnas_lotes():
    return [
        ('lote', 'Nº Lote', lambda fila: f"#{fila['id_produccion']}"),
        ('fecha', 'Fecha', lambda fila: fecha_visible(fila.get('fecha', ''))),
        ('jornada', 'Jornada', lambda fila: fila.get('jornada', '')),
        ('responsable', 'Responsable', lambda fila: fila.get('responsable', 'Sistema')),
        ('unidades', 'Unidades', lambda fila: fila.get('unidades', 0)),
        ('costo', 'Costo (Bs)', lambda fila: dinero_local(fila['costo'])),
    ]


def csv_reporte_produccion(reporte: dict, jornada=None, columnas: list[str] | None = None) -> bytes:
    """CSV con punto y coma y decimales locales para Excel."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    lotes = reporte.get('lotes', [])
    productos = reporte.get('productos', [])
    cols_def = _columnas_lotes()
    if columnas:
        cols_activas = [col for col in cols_def if col[0] in columnas] or cols_def
    else:
        cols_activas = cols_def

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Panadería Santiago'])
    writer.writerow(['Reporte de producción'])
    for etiqueta, valor in [
        ('Desde', fecha_visible(reporte['desde'])),
        ('Hasta', fecha_visible(reporte['hasta'])),
        ('Jornada', _etiqueta_jornada(jornada)),
        ('Generado el', generado),
    ]:
        writer.writerow([etiqueta, valor])
    writer.writerow([])
    writer.writerow(['Resumen'])
    for etiqueta, valor in [
        ('Jornadas', reporte['cantidad']),
        ('Unidades producidas', reporte['unidades']),
        ('Unidades vendidas', reporte['unidades_vendidas']),
        ('Unidades mermadas (CU18)', reporte.get('unidades_mermadas', 0)),
        ('Costo de mermas (Bs)', dinero_local(reporte.get('costo_mermas', 0))),
        ('Diferencia neta (prod. − ventas − mermas)', reporte['diferencia']),
        ('Costo de insumos (Bs)', dinero_local(reporte['costo'])),
    ]:
        writer.writerow([etiqueta, valor])
    writer.writerow([])
    writer.writerow(['Detalle de jornadas'])
    writer.writerow([col[1] for col in cols_activas])
    if lotes:
        for lote in lotes:
            writer.writerow([col[2](lote) for col in cols_activas])
    else:
        writer.writerow(['Este periodo no tiene jornadas de producción registradas.'])
    writer.writerow([])
    writer.writerow(['Producción vs ventas por producto'])
    writer.writerow(['Producto', 'Producidas', 'Vendidas', 'Mermadas', 'Diferencia', 'Costo (Bs)'])
    if productos:
        for producto in productos:
            writer.writerow(
                [
                    producto['nombre'],
                    producto['cantidad'],
                    producto['vendidas'],
                    producto.get('mermadas', 0),
                    producto['diferencia'],
                    dinero_local(producto['costo']),
                ]
            )
    else:
        writer.writerow(['Este periodo no tiene productos producidos ni vendidos.'])

    mermas = reporte.get('mermas', [])
    if mermas:
        writer.writerow([])
        writer.writerow(['Detalle de mermas y pérdidas de producto (CU18)'])
        writer.writerow(
            ['Fecha', 'Producto', 'Cantidad', 'Costo Unitario (Bs)', 'Costo Total (Bs)', 'Motivo', 'Observaciones', 'Responsable']
        )
        for m in mermas:
            writer.writerow(
                [
                    fecha_visible(m.get('fecha', '')),
                    m.get('producto', ''),
                    m.get('cantidad', 0),
                    dinero_local(m.get('costo_unitario', 0)),
                    dinero_local(m.get('costo_total', 0)),
                    m.get('motivo', 'Sobrante al cierre'),
                    m.get('observaciones', ''),
                    m.get('responsable', 'Sistema'),
                ]
            )
    writer.writerow([])
    writer.writerow(
        [
            'Las ventas se comparan por el mismo rango de fechas; la jornada filtra solo la producción.',
        ]
    )
    return buffer.getvalue().encode('utf-8-sig')


def pdf_reporte_produccion(reporte: dict, jornada=None, columnas: list[str] | None = None) -> bytes:
    """PDF formal con membrete, KPIs, jornadas y comparativa por producto."""
    cuando = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Período: del {fecha_visible(reporte["desde"])} al {fecha_visible(reporte["hasta"])}   ·   '
        f'Jornada: {_etiqueta_jornada(jornada)}\n'
        f'Generado el {cuando}'
    )

    hoja = HojaReporte('Reporte de Producción')
    hoja.abrir('Reporte de Producción', detalle)
    hoja.tarjetas(
        [
            ('Jornadas', str(reporte['cantidad'])),
            ('Producidas', str(reporte['unidades'])),
            ('Vendidas', str(reporte['unidades_vendidas'])),
            ('Mermas (CU18)', f"{reporte.get('unidades_mermadas', 0)} un."),
            ('Costo Prod.', f'Bs {_dinero(reporte["costo"])}'),
        ]
    )

    col_map = {
        'lote': {
            'titulo': 'Nº Lote',
            'alineacion': 'izq',
            'ancho': 14,
            'valor': lambda fila: f"#{fila['id_produccion']}",
        },
        'fecha': {
            'titulo': 'Fecha',
            'alineacion': 'izq',
            'ancho': 18,
            'valor': lambda fila: fecha_visible(fila.get('fecha', '')),
        },
        'jornada': {
            'titulo': 'Jornada',
            'alineacion': 'izq',
            'ancho': 16,
            'valor': lambda fila: fila.get('jornada', ''),
        },
        'responsable': {
            'titulo': 'Responsable',
            'alineacion': 'izq',
            'ancho': 24,
            'valor': lambda fila: fila.get('responsable', 'Sistema'),
        },
        'unidades': {
            'titulo': 'Unid.',
            'alineacion': 'der',
            'ancho': 12,
            'valor': lambda fila: str(fila.get('unidades', 0)),
        },
        'costo': {
            'titulo': 'Costo (Bs)',
            'alineacion': 'der',
            'ancho': 16,
            'valor': lambda fila: f"Bs {_dinero(fila['costo'])}",
        },
    }

    if columnas:
        claves = [clave for clave in columnas if clave in col_map] or list(col_map)
    else:
        claves = list(col_map)

    anchos = anchos_de(*[col_map[clave]['ancho'] for clave in claves])
    lotes = reporte.get('lotes', [])
    hoja.seccion('Detalle de jornadas del período')

    def encabezado_lotes():
        hoja.fila(
            [(col_map[clave]['titulo'], col_map[clave]['alineacion']) for clave in claves],
            anchos,
            encabezado=True,
        )

    encabezado_lotes()
    for indice, lote in enumerate(lotes):
        hoja.fila(
            [(col_map[clave]['valor'](lote), col_map[clave]['alineacion']) for clave in claves],
            anchos,
            cebra=indice % 2 == 1,
            al_continuar=encabezado_lotes,
        )
    if not lotes:
        hoja.nota('Este período no tiene jornadas de producción registradas.')

    productos = reporte.get('productos', [])
    hoja.seccion('Producción vs ventas por producto')
    anchos_prod = anchos_de(30, 14, 14, 14, 14, 14)

    def encabezado_productos():
        hoja.fila(
            [
                ('Producto', 'izq'),
                ('Producidas', 'der'),
                ('Vendidas', 'der'),
                ('Mermas', 'der'),
                ('Diferencia', 'der'),
                ('Costo (Bs)', 'der'),
            ],
            anchos_prod,
            encabezado=True,
        )

    encabezado_productos()
    for indice, producto in enumerate(productos):
        hoja.fila(
            [
                (producto['nombre'], 'izq'),
                (str(producto['cantidad']), 'der'),
                (str(producto['vendidas']), 'der'),
                (str(producto.get('mermadas', 0)), 'der'),
                (str(producto['diferencia']), 'der'),
                (f"Bs {_dinero(producto['costo'])}", 'der'),
            ],
            anchos_prod,
            cebra=indice % 2 == 1,
            al_continuar=encabezado_productos,
        )
    if not productos:
        hoja.nota('Este período no tiene productos producidos ni vendidos.')

    mermas = reporte.get('mermas', [])
    if mermas or int(reporte.get('unidades_mermadas', 0) or 0) > 0:
        hoja.seccion('Detalle de mermas y pérdidas de producto (CU18)')
        anchos_mermas = anchos_de(16, 22, 12, 26, 12, 12)

        def encabezado_mermas():
            hoja.fila(
                [
                    ('Fecha', 'izq'),
                    ('Producto', 'izq'),
                    ('Cant.', 'der'),
                    ('Motivo', 'izq'),
                    ('Costo (Bs)', 'der'),
                    ('Responsable', 'izq'),
                ],
                anchos_mermas,
                encabezado=True,
            )

        encabezado_mermas()
        for indice, merma in enumerate(mermas):
            hoja.fila(
                [
                    (fecha_visible(merma.get('fecha', '')), 'izq'),
                    (str(merma.get('producto', ''))[:24], 'izq'),
                    (f"-{merma.get('cantidad', 0)} u.", 'der'),
                    (str(merma.get('motivo', 'Sobrante al cierre'))[:28], 'izq'),
                    (f"Bs {_dinero(merma.get('costo_total', 0))}", 'der'),
                    (str(merma.get('responsable', 'Sistema'))[:14], 'izq'),
                ],
                anchos_mermas,
                cebra=indice % 2 == 1,
                al_continuar=encabezado_mermas,
            )
        if not mermas:
            hoja.nota('No hay registros de mermas disponibles para este período.')

    hoja.nota(
        'Las ventas y mermas se comparan por el mismo rango de fechas. La jornada filtra solo la producción.'
    )
    return hoja.cerrar()
