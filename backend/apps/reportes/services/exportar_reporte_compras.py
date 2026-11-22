"""
Archivos exportables del CU24 (Reporte de compras y gastos).

El CSV se genera con el reporte dinámico.
El PDF se genera con el cierre estático ya guardado.
"""
import csv
import io
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


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
