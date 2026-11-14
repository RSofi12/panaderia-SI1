"""
CSV para abrir en Excel.

Sigue siendo texto: no puede llevar el logo ni colores. El título, el
resumen y la tabla usan los mismos nombres que la pantalla. El punto y
coma separa columnas, y la coma marca los decimales, que es como Excel
en español reconoce un número.
"""
import csv
import io
from decimal import Decimal


def dinero_local(valor) -> str:
    """1410.5 queda como 1410,50 para que Excel lo sume."""
    return f'{Decimal(valor):.2f}'.replace('.', ',')


def archivo_csv(titulo, datos, resumen, seccion, columnas, filas, aviso, vacio=None) -> bytes:
    """Arma un reporte en tres bloques: datos del filtro, cifras y tabla."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Panadería Santiago'])
    writer.writerow([titulo])
    for etiqueta, valor in datos:
        writer.writerow([etiqueta, valor])
    writer.writerow([])
    writer.writerow(['Resumen'])
    for etiqueta, valor in resumen:
        writer.writerow([etiqueta, valor])
    writer.writerow([])
    writer.writerow([seccion])
    writer.writerow(columnas)
    if filas:
        for fila in filas:
            writer.writerow(fila)
    elif vacio:
        writer.writerow([vacio])
    writer.writerow([])
    writer.writerow([aviso])
    return buffer.getvalue().encode('utf-8-sig')
