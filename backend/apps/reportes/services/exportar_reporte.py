"""
Exportación de archivos del CU21 (Reporte dinámico de ventas).

El CSV y el PDF se generan en tiempo real sobre las ventas calculadas del periodo.
Permite seleccionar dinámicamente qué columnas incluir en la exportación PDF y CSV.
"""
import csv
import io
from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.comercializacion.ventas.models import MetodoPago
from apps.reportes.formatos.csv_reporte import dinero_local
from apps.reportes.formatos.pdf_analisis_tablas import agregar_tablas_por_contexto
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible
from apps.reportes.formatos.texto_informe import sin_markdown
from apps.reportes.services.analisis_ia import recolectar_contexto_analisis


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


_TITULOS_ANALISIS = {
    'roles': 'Reporte de roles y accesos',
    'ventas': 'Análisis de ventas',
    'produccion': 'Análisis de producción',
    'existencias': 'Análisis de existencias',
    'compras': 'Análisis de compras y gastos',
    'economico': 'Resultados económicos',
    'productos': 'Análisis por productos',
    'general': 'Análisis gerencial',
}


def pdf_reporte_analisis(
    *,
    consulta: str,
    tema: str,
    desde: str,
    hasta: str,
    analisis: str,
    motor: str = 'local',
) -> bytes:
    """PDF con membrete oficial para el texto del asistente por voz."""
    titulo = _TITULOS_ANALISIS.get(tema, 'Análisis gerencial')
    cuando = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    etiqueta_motor = 'Gemini' if motor == 'gemini' else 'Análisis local'
    detalle = (
        f'Consulta: {consulta.strip()}\n'
        f'Período: del {fecha_visible(desde)} al {fecha_visible(hasta)}   ·   '
        f'Motor: {etiqueta_motor}\n'
        f'Generado el {cuando}'
    )

    desde_d = date.fromisoformat(str(desde))
    hasta_d = date.fromisoformat(str(hasta))
    contexto = recolectar_contexto_analisis(tema, desde_d, hasta_d)

    tarjetas = [
        ('Tema', tema.upper().replace('_', ' ')),
        ('Desde', fecha_visible(desde)),
        ('Hasta', fecha_visible(hasta)),
    ]
    if contexto.get('tipo') == 'ventas':
        tarjetas = [
            ('Ventas', str(contexto.get('cantidad', 0))),
            ('Total', f"Bs {_dinero(contexto.get('total', 0))}"),
            ('Efectivo', f"Bs {_dinero(contexto.get('efectivo', 0))}"),
            ('Tarjeta', f"Bs {_dinero(contexto.get('tarjeta', 0))}"),
        ]
    elif contexto.get('tipo') == 'produccion':
        tarjetas = [
            ('Jornadas', str(contexto.get('jornadas') or contexto.get('cantidad', 0))),
            ('Producidas', str(contexto.get('unidades', 0))),
            ('Vendidas', str(contexto.get('unidades_vendidas', 0))),
            ('Costo', f"Bs {_dinero(contexto.get('costo', 0))}"),
        ]
    elif contexto.get('tipo') == 'roles':
        total_usuarios = sum(int(r.get('cantidad_usuarios', 0)) for r in contexto.get('roles') or [])
        tarjetas[0] = ('Roles', str(len(contexto.get('roles') or [])))
        tarjetas[1] = ('Usuarios activos', str(total_usuarios))

    hoja = HojaReporte(titulo)
    hoja.abrir(titulo, detalle)
    hoja.tarjetas(tarjetas)
    hoja.seccion('Resumen ejecutivo')
    hoja.cuerpo(sin_markdown(analisis.strip()) or 'Sin contenido de análisis.')
    agregar_tablas_por_contexto(hoja, contexto)
    hoja.nota('Documento generado desde el asistente de reportes (Panadería Santiago).')
    return hoja.cerrar()


def csv_reporte_analisis(
    *,
    consulta: str,
    tema: str,
    desde: str,
    hasta: str,
    analisis: str,
    motor: str = 'local',
) -> bytes:
    """CSV con BOM UTF-8 (Excel en español) y tablas reales; sin Markdown."""
    titulo = _TITULOS_ANALISIS.get(tema, 'Análisis gerencial')
    cuando = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    etiqueta_motor = 'Gemini' if motor == 'gemini' else 'Análisis local'
    desde_d = date.fromisoformat(str(desde))
    hasta_d = date.fromisoformat(str(hasta))
    contexto = recolectar_contexto_analisis(tema, desde_d, hasta_d)

    from apps.reportes.formatos.csv_analisis_tablas import escribir_tablas_csv

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Panadería Santiago'])
    writer.writerow([titulo])
    writer.writerow(['Consulta', consulta.strip()])
    writer.writerow(['Desde', fecha_visible(desde)])
    writer.writerow(['Hasta', fecha_visible(hasta)])
    writer.writerow(['Motor', etiqueta_motor])
    writer.writerow(['Generado el', cuando])

    if contexto.get('tipo') == 'ventas':
        writer.writerow([])
        writer.writerow(['Resumen del período'])
        writer.writerow(['Ventas', contexto.get('cantidad', 0)])
        writer.writerow(['Total (Bs)', _dinero(contexto.get('total', 0))])
        writer.writerow(['Efectivo (Bs)', _dinero(contexto.get('efectivo', 0))])
        writer.writerow(['Tarjeta (Bs)', _dinero(contexto.get('tarjeta', 0))])

    writer.writerow([])
    writer.writerow(['Resumen ejecutivo'])
    texto_limpio = sin_markdown((analisis or '').strip())
    if texto_limpio:
        for linea in texto_limpio.splitlines():
            limpia = linea.strip()
            if limpia:
                writer.writerow([limpia])
    else:
        writer.writerow(['Sin contenido de análisis.'])

    escribir_tablas_csv(writer, contexto)
    writer.writerow([])
    writer.writerow(['Documento generado desde el asistente de reportes (Panadería Santiago).'])
    return buffer.getvalue().encode('utf-8-sig')
