"""
Archivos del CU21.

El CSV se arma con el reporte dinámico: cada descarga vuelve a sumar.
El PDF se arma con el cierre ya guardado: no vuelve a leer venta.
"""
import csv
import io
from decimal import Decimal

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.comercializacion.ventas.models import MetodoPago


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
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['tipo', 'dinamico'])
    writer.writerow(['desde', reporte['desde'].isoformat()])
    writer.writerow(['hasta', reporte['hasta'].isoformat()])
    writer.writerow(['metodo', _metodo(metodo_pago)])
    writer.writerow(['ventas', reporte['cantidad']])
    writer.writerow(['total', _dinero(reporte['total'])])
    writer.writerow(['efectivo', _dinero(reporte['efectivo'])])
    writer.writerow(['tarjeta', _dinero(reporte['tarjeta'])])
    writer.writerow([])
    writer.writerow(['producto', 'cantidad', 'subtotal'])
    for producto in reporte['productos']:
        writer.writerow([producto['nombre'], producto['cantidad'], _dinero(producto['subtotal'])])
    return buffer.getvalue().encode('utf-8-sig')


def pdf_cierre(cierre: dict) -> bytes:
    buffer = io.BytesIO()
    hoja = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    hoja.setTitle(f'Cierre de ventas {cierre["id_cierre"]}')
    y = 800

    def linea(texto, tamano=11, negrita=False):
        nonlocal y
        hoja.setFont('Helvetica-Bold' if negrita else 'Helvetica', tamano)
        hoja.drawString(48, y, str(texto))
        y -= tamano + 8

    cuando = timezone.localtime(cierre['fecha_generacion']).strftime('%d/%m/%Y %H:%M')
    linea('Panadería Santiago', 16, True)
    linea('Cierre estático de ventas', 13, True)
    linea(f'{_periodo(cierre["periodo"])} del {cierre["desde"].isoformat()} al {cierre["hasta"].isoformat()}')
    linea(f'Método: {_metodo(cierre["metodo_pago"])}')
    linea(f'Congelado el {cuando} por {cierre["generado_por"]}')
    y -= 8
    linea(f'Ventas: {cierre["cantidad"]}', 12, True)
    linea(f'Total: Bs {_dinero(cierre["total"])}', 12, True)
    linea(f'Efectivo: Bs {_dinero(cierre["efectivo"])}')
    linea(f'Tarjeta: Bs {_dinero(cierre["tarjeta"])}')
    y -= 8
    linea('Producto', 11, True)
    for producto in cierre['productos']:
        linea(f'{producto["nombre"]}  ·  {producto["cantidad"]} u  ·  Bs {_dinero(producto["subtotal"])}')
    if not cierre['productos']:
        linea('Este periodo no tiene ventas.')
    y -= 12
    linea('Estos números quedaron guardados y no se vuelven a calcular.')
    hoja.showPage()
    hoja.save()
    return buffer.getvalue()
