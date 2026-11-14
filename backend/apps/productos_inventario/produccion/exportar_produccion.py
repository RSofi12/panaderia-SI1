"""
Archivo de la pantalla Producción diaria.

No es un caso de uso nuevo: vuelve a leer el historial con los mismos
filtros de la lista (jornada y rango de fechas) y lo entrega en CSV o PDF.
"""
from decimal import Decimal

from django.utils import timezone

from apps.reportes.formatos.csv_reporte import archivo_csv, dinero_local
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible


def _dinero(valor) -> str:
    return f'{Decimal(valor):.2f}'


def _nombre_producto(id_producto):
    if not id_producto:
        return None
    from apps.productos_inventario.productos.models import Producto
    return Producto.objects.filter(pk=id_producto).values_list('nombre', flat=True).first()


def resumir_producciones(producciones, filtros):
    """Arma las tres cifras de las tarjetas y las filas de la tabla."""
    filas = []
    unidades = 0
    costo = Decimal('0.00')

    for produccion in producciones:
        detalles = list(produccion.detalles.all())
        panes = sum(detalle.cantidad_producida for detalle in detalles)
        costo_lote = sum(
            (Decimal(detalle.cantidad_producida) * detalle.costo_unitario for detalle in detalles),
            Decimal('0.00'),
        ).quantize(Decimal('0.01'))
        unidades += panes
        costo += costo_lote
        filas.append({
            'lote': produccion.id_produccion,
            'fecha': produccion.fecha.isoformat(),
            'jornada': produccion.get_jornada_display(),
            'responsable': produccion.id_usuario.nombre_usuario,
            'panes': panes,
            'variedades': len(detalles),
            'costo': costo_lote,
        })

    return {
        'fecha_desde': filtros.get('fecha_desde'),
        'fecha_hasta': filtros.get('fecha_hasta'),
        'jornada': filtros.get('jornada'),
        'producto': _nombre_producto(filtros.get('id_producto')),
        'unidades': unidades,
        'jornadas': len(filas),
        'costo': costo.quantize(Decimal('0.01')),
        'filas': filas,
    }


def csv_produccion(resumen: dict) -> bytes:
    """Mismas cifras que el PDF, en un texto que Excel abre por columnas."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    filas = [
        [
            f'#{fila["lote"]}',
            fecha_visible(fila['fecha']),
            fila['jornada'],
            fila['responsable'],
            fila['panes'],
            fila['variedades'],
            dinero_local(fila['costo']),
        ]
        for fila in resumen['filas']
    ]
    return archivo_csv(
        'Reporte de producción diaria',
        [
            ('Jornada', fecha_visible(resumen['jornada'])),
            ('Desde', fecha_visible(resumen['fecha_desde'])),
            ('Hasta', fecha_visible(resumen['fecha_hasta'])),
            ('Producto', fecha_visible(resumen['producto'])),
            ('Generado el', generado),
        ],
        [
            ('Panes producidos', resumen['unidades']),
            ('Jornadas', resumen['jornadas']),
            ('Costo de insumos (Bs)', dinero_local(resumen['costo'])),
        ],
        'Detalle de jornadas',
        ['Lote', 'Fecha', 'Jornada', 'Responsable', 'Panes', 'Variedades', 'Costo (Bs)'],
        filas,
        'Estas cifras usan el mismo filtro de la consulta en pantalla.',
        vacio='No hay jornadas con este filtro.',
    )


def pdf_produccion(resumen: dict) -> bytes:
    """Reporte de las jornadas que ya muestra la pantalla, con el mismo filtro."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Jornada: {fecha_visible(resumen["jornada"])}   ·   '
        f'Desde: {fecha_visible(resumen["fecha_desde"])}   ·   '
        f'Hasta: {fecha_visible(resumen["fecha_hasta"])}   ·   '
        f'Producto: {fecha_visible(resumen["producto"])}\n'
        f'Generado el {generado}'
    )
    columnas = anchos_de(9, 14, 13, 28, 11, 13, 12)
    reporte = HojaReporte('Reporte de producción diaria')
    reporte.abrir('Reporte de producción diaria', detalle)
    reporte.tarjetas([
        ('Panes producidos', str(resumen['unidades'])),
        ('Jornadas', str(resumen['jornadas'])),
        ('Costo de insumos', f'Bs {_dinero(resumen["costo"])}'),
    ])
    reporte.seccion('Detalle de jornadas')

    def encabezado():
        reporte.fila(
            [
                ('Lote', 'izq'),
                ('Fecha', 'izq'),
                ('Jornada', 'izq'),
                ('Responsable', 'izq'),
                ('Panes', 'der'),
                ('Variedades', 'der'),
                ('Costo', 'der'),
            ],
            columnas,
            encabezado=True,
        )

    encabezado()
    for indice, fila in enumerate(resumen['filas']):
        reporte.fila(
            [
                (f'#{fila["lote"]}', 'izq'),
                (fecha_visible(fila['fecha']), 'izq'),
                (fila['jornada'], 'izq'),
                (fila['responsable'], 'izq'),
                (str(fila['panes']), 'der'),
                (str(fila['variedades']), 'der'),
                (f'Bs {_dinero(fila["costo"])}', 'der'),
            ],
            columnas,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )
    if not resumen['filas']:
        reporte.nota('No hay jornadas con este filtro.')
    reporte.nota('Estas cifras usan el mismo filtro de la consulta en pantalla.')
    return reporte.cerrar()


def nombre_archivo(filtros, extension: str) -> str:
    if filtros.get('fecha_desde') or filtros.get('fecha_hasta'):
        periodo = f'{filtros.get("fecha_desde") or "sin-inicio"}_{filtros.get("fecha_hasta") or "sin-fin"}'
    else:
        periodo = 'todas-las-fechas'
    jornada = {
        'Mañana': 'manana',
        'Tarde': 'tarde',
        'Noche': 'noche',
        'unica': 'unica',
    }.get(filtros.get('jornada') or '', 'todas-las-jornadas')
    producto = f'_producto-{filtros["id_producto"]}' if filtros.get('id_producto') else ''
    return f'produccion-diaria_{periodo}_{jornada}{producto}.{extension}'
