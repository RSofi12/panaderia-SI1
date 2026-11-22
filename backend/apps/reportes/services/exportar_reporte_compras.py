"""
Archivos exportables del CU24 (Reporte de compras y gastos).

El CSV y el PDF dinámico se generan con el reporte en vivo.
El PDF de cierre se genera con el snapshot ya guardado.
"""
import csv
import io
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible


def _dinero(valor) -> str:
    return f'{Decimal(valor):.2f}'


def _cantidad(valor) -> str:
    return f'{Decimal(valor):.3f}'


def _periodo(periodo: str) -> str:
    return {'dia': 'Día', 'semana': 'Semana', 'mes': 'Mes'}.get(periodo, periodo)


def csv_reporte_compras(reporte: dict, proveedor_nombre: str = None) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['tipo', 'dinamico_compras'])
    writer.writerow(['desde', reporte['desde'].isoformat()])
    writer.writerow(['hasta', reporte['hasta'].isoformat()])
    writer.writerow(['proveedor', proveedor_nombre or 'Todos los proveedores'])
    writer.writerow(['compras', reporte['cantidad']])
    writer.writerow(['total_gastado', _dinero(reporte['total'])])
    writer.writerow([])
    writer.writerow(['--- DETALLE POR MATERIA PRIMA ---'])
    writer.writerow(['materia_prima', 'unidad_medida', 'cantidad_adquirida', 'subtotal'])
    for insumo in reporte['insumos']:
        writer.writerow([
            insumo['nombre'],
            insumo['unidad_medida'],
            _cantidad(insumo['cantidad']),
            _dinero(insumo['subtotal']),
        ])
    writer.writerow([])
    writer.writerow(['--- DETALLE POR PROVEEDOR ---'])
    writer.writerow(['proveedor', 'cantidad_compras', 'total'])
    for prov in reporte['proveedores']:
        writer.writerow([
            prov['nombre'],
            prov['cantidad_compras'],
            _dinero(prov['total']),
        ])
    return buffer.getvalue().encode('utf-8-sig')


def pdf_reporte_compras(reporte: dict, proveedor_nombre: str = None) -> bytes:
    """PDF formal del reporte dinámico (mismo recálculo que el CSV)."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Período: del {fecha_visible(reporte["desde"])} al {fecha_visible(reporte["hasta"])}   ·   '
        f'Proveedor: {proveedor_nombre or "Todos los proveedores"}\n'
        f'Generado el {generado}'
    )
    hoja = HojaReporte('Reporte de Compras y Gastos')
    hoja.abrir('Reporte de Compras y Gastos', detalle)
    hoja.tarjetas(
        [
            ('Compras', str(reporte['cantidad'])),
            ('Total', f'Bs {_dinero(reporte["total"])}'),
            ('Proveedores', str(len(reporte.get('proveedores') or []))),
            ('Insumos', str(len(reporte.get('insumos') or []))),
        ]
    )

    anchos_insumo = anchos_de(40, 16, 22, 22)
    hoja.seccion('Detalle por materia prima')

    def encabezado_insumos():
        hoja.fila(
            [
                ('Materia prima', 'izq'),
                ('Unidad', 'izq'),
                ('Cantidad', 'der'),
                ('Subtotal (Bs)', 'der'),
            ],
            anchos_insumo,
            encabezado=True,
        )

    encabezado_insumos()
    insumos = reporte.get('insumos') or []
    for indice, insumo in enumerate(insumos):
        hoja.fila(
            [
                (insumo['nombre'], 'izq'),
                (insumo['unidad_medida'], 'izq'),
                (_cantidad(insumo['cantidad']), 'der'),
                (f'Bs {_dinero(insumo["subtotal"])}', 'der'),
            ],
            anchos_insumo,
            cebra=indice % 2 == 1,
            al_continuar=encabezado_insumos,
        )
    if not insumos:
        hoja.nota('Este período no tiene compras de materias primas.')

    anchos_prov = anchos_de(50, 20, 30)
    hoja.seccion('Detalle por proveedor')

    def encabezado_proveedores():
        hoja.fila(
            [
                ('Proveedor', 'izq'),
                ('Compras', 'der'),
                ('Total (Bs)', 'der'),
            ],
            anchos_prov,
            encabezado=True,
        )

    encabezado_proveedores()
    proveedores = reporte.get('proveedores') or []
    for indice, prov in enumerate(proveedores):
        hoja.fila(
            [
                (prov['nombre'], 'izq'),
                (str(prov['cantidad_compras']), 'der'),
                (f'Bs {_dinero(prov["total"])}', 'der'),
            ],
            anchos_prov,
            cebra=indice % 2 == 1,
            al_continuar=encabezado_proveedores,
        )
    if not proveedores:
        hoja.nota('Este período no tiene compras a proveedores.')
    return hoja.cerrar()


def pdf_cierre_compras(cierre: dict) -> bytes:
    buffer = io.BytesIO()
    hoja = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    hoja.setTitle(f'Cierre de compras {cierre["id_cierre"]}')
    y = 800

    def linea(texto, tamano=11, negrita=False):
        nonlocal y
        hoja.setFont('Helvetica-Bold' if negrita else 'Helvetica', tamano)
        hoja.drawString(48, y, str(texto))
        y -= tamano + 8

    cuando = timezone.localtime(cierre['fecha_generacion']).strftime('%d/%m/%Y %H:%M')
    linea('Panadería Santiago', 16, True)
    linea('Cierre estático de compras y gastos', 13, True)
    linea(f'{_periodo(cierre["periodo"])} del {cierre["desde"].isoformat()} al {cierre["hasta"].isoformat()}')
    linea(f'Proveedor: {cierre["proveedor"] or "Todos los proveedores"}')
    linea(f'Congelado el {cuando} por {cierre["generado_por"]}')
    y -= 8
    linea(f'Total compras: {cierre["cantidad"]}', 12, True)
    linea(f'Total gastado: Bs {_dinero(cierre["total"])}', 12, True)
    y -= 8
    linea('Materia prima / Insumos adquiridos', 11, True)
    for insumo in cierre['insumos']:
        linea(f'{insumo["nombre"]}  ·  {_cantidad(insumo["cantidad"])} {insumo["unidad_medida"]}  ·  Bs {_dinero(insumo["subtotal"])}')
    if not cierre['insumos']:
        linea('Este periodo no tiene compras registradas.')
    y -= 12
    linea('Estos números quedaron guardados y no se vuelven a calcular.')
    hoja.showPage()
    hoja.save()
    return buffer.getvalue()
