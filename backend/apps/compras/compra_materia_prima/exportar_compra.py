"""
Archivo de la pantalla Compras de materia prima (CU7).

No es un caso de uso nuevo: vuelve a leer el listado con los mismos
filtros de la tabla y lo entrega en CSV o PDF.
"""
from decimal import Decimal

from django.utils import timezone

from apps.reportes.formatos.csv_reporte import archivo_csv, dinero_local
from apps.reportes.formatos.pdf_reporte import HojaReporte, anchos_de, fecha_visible

from .consulta import compras_filtradas


def _dinero(valor) -> str:
    return f'{Decimal(valor):.2f}'


def _nombre_proveedor(id_proveedor):
    if not id_proveedor:
        return None
    from apps.compras.proveedores.models import Proveedor
    return Proveedor.objects.filter(pk=id_proveedor).values_list('nombre', flat=True).first()


def resumir_compras(filtros):
    """Arma las cifras de las tarjetas y las filas de la tabla."""
    filas = []
    total = Decimal('0.00')
    acumulado = {}
    orden = []

    for compra in compras_filtradas(filtros):
        monto = Decimal(compra.total).quantize(Decimal('0.01'))
        total += monto
        nombre = compra.id_proveedor.nombre
        if nombre not in acumulado:
            orden.append(nombre)
            acumulado[nombre] = Decimal('0.00')
        acumulado[nombre] += monto
        momento = timezone.localtime(compra.fecha_hora)
        filas.append({
            'numero': compra.id_compra,
            'fecha': momento.strftime('%d/%m/%Y %H:%M'),
            'proveedor': nombre,
            'responsable': compra.id_usuario.nombre_usuario,
            'lineas': compra.cantidad_lineas,
            'total': monto,
        })

    principal = None
    mayor = Decimal('0.00')
    for nombre in orden:
        if acumulado[nombre] > mayor:
            mayor = acumulado[nombre]
            principal = nombre

    return {
        'fecha_desde': filtros.get('fecha_desde'),
        'fecha_hasta': filtros.get('fecha_hasta'),
        'proveedor': _nombre_proveedor(filtros.get('id_proveedor')),
        'busqueda': filtros.get('search'),
        'total': total.quantize(Decimal('0.01')),
        'operaciones': len(filas),
        'principal': principal,
        'filas': filas,
    }


def csv_compras(resumen: dict) -> bytes:
    """Mismas cifras que el PDF, en un texto que Excel abre por columnas."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    filas = [
        [
            f'#{fila["numero"]}',
            fila['fecha'],
            fila['proveedor'],
            fila['responsable'],
            fila['lineas'],
            dinero_local(fila['total']),
        ]
        for fila in resumen['filas']
    ]
    return archivo_csv(
        'Reporte de compras de materia prima',
        [
            ('Proveedor', fecha_visible(resumen['proveedor'])),
            ('Desde', fecha_visible(resumen['fecha_desde'])),
            ('Hasta', fecha_visible(resumen['fecha_hasta'])),
            ('Búsqueda', fecha_visible(resumen['busqueda'])),
            ('Generado el', generado),
        ],
        [
            ('Operaciones', resumen['operaciones']),
            ('Total invertido (Bs)', dinero_local(resumen['total'])),
            ('Proveedor principal', resumen['principal'] or 'Ninguno'),
        ],
        'Detalle de compras',
        ['N.º', 'Fecha', 'Proveedor', 'Registrado por', 'Líneas', 'Total (Bs)'],
        filas,
        'Estas cifras usan el mismo filtro de la consulta en pantalla.',
        vacio='No hay compras con este filtro.',
    )


def pdf_compras(resumen: dict) -> bytes:
    """Reporte de las compras que ya muestra la pantalla, con el mismo filtro."""
    generado = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    detalle = (
        f'Proveedor: {fecha_visible(resumen["proveedor"])}   ·   '
        f'Desde: {fecha_visible(resumen["fecha_desde"])}   ·   '
        f'Hasta: {fecha_visible(resumen["fecha_hasta"])}   ·   '
        f'Búsqueda: {fecha_visible(resumen["busqueda"])}\n'
        f'Generado el {generado}'
    )
    columnas = anchos_de(10, 20, 24, 22, 10, 14)
    reporte = HojaReporte('Reporte de compras de materia prima')
    reporte.abrir('Reporte de compras de materia prima', detalle)
    reporte.tarjetas([
        ('Operaciones', str(resumen['operaciones'])),
        ('Total invertido', f'Bs {_dinero(resumen["total"])}'),
        ('Proveedor principal', resumen['principal'] or 'Ninguno'),
    ])
    reporte.seccion('Detalle de compras')

    def encabezado():
        reporte.fila(
            [
                ('N.º', 'izq'),
                ('Fecha', 'izq'),
                ('Proveedor', 'izq'),
                ('Registrado por', 'izq'),
                ('Líneas', 'der'),
                ('Total', 'der'),
            ],
            columnas,
            encabezado=True,
        )

    encabezado()
    for indice, fila in enumerate(resumen['filas']):
        reporte.fila(
            [
                (f'#{fila["numero"]}', 'izq'),
                (fila['fecha'], 'izq'),
                (fila['proveedor'], 'izq'),
                (fila['responsable'], 'izq'),
                (str(fila['lineas']), 'der'),
                (f'Bs {_dinero(fila["total"])}', 'der'),
            ],
            columnas,
            cebra=indice % 2 == 1,
            al_continuar=encabezado,
        )
    if not resumen['filas']:
        reporte.nota('No hay compras con este filtro.')
    reporte.nota('Estas cifras usan el mismo filtro de la consulta en pantalla.')
    return reporte.cerrar()


def nombre_archivo(filtros, extension: str) -> str:
    if filtros.get('fecha_desde') or filtros.get('fecha_hasta'):
        periodo = f'{filtros.get("fecha_desde") or "sin-inicio"}_{filtros.get("fecha_hasta") or "sin-fin"}'
    else:
        periodo = 'todas-las-fechas'
    proveedor = (
        f'proveedor-{filtros["id_proveedor"]}'
        if filtros.get('id_proveedor')
        else 'todos-los-proveedores'
    )
    return f'compras_{periodo}_{proveedor}.{extension}'
