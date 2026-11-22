"""CSV y PDF del CU23 (existencias actuales, solo lectura)."""

import csv
import io
from decimal import Decimal

from django.utils import timezone

from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de


ETIQUETA_TIPO = {
    'materia_prima': 'Materia prima',
    'producto_terminado': 'Producto terminado',
}
ETIQUETA_ESTADO = {
    'normal': 'Disponible',
    'bajo_stock': 'Stock bajo',
    'sin_inventario': 'Sin registro',
}
ETIQUETA_FILTRO_TIPO = {
    'todos': 'Todos',
    'materia_prima': 'Materias primas',
    'producto_terminado': 'Productos terminados',
}
ETIQUETA_FILTRO_ESTADO = {
    'todos': 'Todos',
    'normal': 'Disponible',
    'bajo_stock': 'Stock bajo',
    'sin_inventario': 'Sin registro',
}


def _cantidad(valor) -> str:
    if valor is None:
        return '—'
    return f'{Decimal(valor):.3f}'.replace('.', ',')


def csv_reporte_existencias(reporte: dict, *, tipo='todos', q='', estado='todos') -> bytes:
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Panadería Santiago'])
    writer.writerow(['Reporte de existencias'])
    writer.writerow(['Tipo', ETIQUETA_FILTRO_TIPO.get(tipo, tipo)])
    writer.writerow(['Búsqueda', q or 'Todas'])
    writer.writerow(['Estado', ETIQUETA_FILTRO_ESTADO.get(estado, estado)])
    writer.writerow(['Generado el', generado])
    writer.writerow([])
    writer.writerow(['Resumen'])
    resumen = reporte['resumen']
    writer.writerow(['Productos', resumen['total']])
    writer.writerow(['Materias primas', resumen['materias_primas']])
    writer.writerow(['Productos terminados', resumen['productos_terminados']])
    writer.writerow(['Stock bajo', resumen['bajo_stock']])
    writer.writerow(['Sin registro', resumen['sin_inventario']])
    writer.writerow([])
    writer.writerow(['Inventario actual'])
    writer.writerow(['Nombre', 'Tipo', 'Condición', 'Stock', 'Unidad', 'Mínimo', 'Estado'])
    filas = reporte.get('resultados') or []
    for fila in filas:
        writer.writerow([
            fila['nombre'],
            ETIQUETA_TIPO.get(fila['tipo'], fila['tipo']),
            'Activo' if fila['activo'] else 'Inactivo',
            _cantidad(fila['stock_actual']),
            fila['unidad_medida'],
            _cantidad(fila['stock_minimo']),
            ETIQUETA_ESTADO.get(fila['estado'], fila['estado']),
        ])
    if not filas:
        writer.writerow(['No hay existencias que coincidan con los filtros.'])
    return buffer.getvalue().encode('utf-8-sig')


def pdf_reporte_existencias(reporte: dict, *, tipo='todos', q='', estado='todos') -> bytes:
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Tipo: {ETIQUETA_FILTRO_TIPO.get(tipo, tipo)}   ·   '
        f'Estado: {ETIQUETA_FILTRO_ESTADO.get(estado, estado)}   ·   '
        f'Búsqueda: {q or "Todas"}\n'
        f'Generado el {generado}'
    )
    resumen = reporte['resumen']
    hoja = HojaReporte('Reporte de Existencias')
    hoja.abrir('Reporte de Existencias', detalle)
    hoja.tarjetas(
        [
            ('Productos', str(resumen['total'])),
            ('Stock bajo', str(resumen['bajo_stock'])),
            ('Sin registro', str(resumen['sin_inventario'])),
            ('Terminados', str(resumen['productos_terminados'])),
        ]
    )
    anchos = anchos_de(32, 18, 14, 10, 12, 14)
    hoja.seccion('Inventario de insumos y productos')

    def encabezado():
        hoja.fila(
            [
                ('Producto', 'izq'),
                ('Tipo', 'izq'),
                ('Stock', 'der'),
                ('Unidad', 'izq'),
                ('Mínimo', 'der'),
                ('Estado', 'izq'),
            ],
            anchos,
            encabezado=True,
        )

    encabezado()
    filas = reporte.get('resultados') or []
    for indice, fila in enumerate(filas):
        hoja.fila(
            [
                (fila['nombre'], 'izq'),
                (ETIQUETA_TIPO.get(fila['tipo'], fila['tipo']), 'izq'),
                (_cantidad(fila['stock_actual']), 'der'),
                (fila['unidad_medida'], 'izq'),
                (_cantidad(fila['stock_minimo']), 'der'),
                (ETIQUETA_ESTADO.get(fila['estado'], fila['estado']), 'izq'),
            ],
            anchos,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )
    if not filas:
        hoja.nota('No hay existencias que coincidan con los filtros.')
    hoja.nota('El stock es un snapshot actual: no depende de un rango de fechas.')
    return hoja.cerrar()
