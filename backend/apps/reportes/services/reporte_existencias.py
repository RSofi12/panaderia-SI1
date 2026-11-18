"""CU23: reporte de existencias de ambos catálogos, exclusivamente de lectura."""

from decimal import Decimal

from apps.productos_inventario.materia_prima.models import MateriaPrima
from apps.productos_inventario.productos.models import Producto


# Referencia provisional exclusiva de CU23: no altera el inventario ni CU12.
UMBRAL_PRODUCTOS_TERMINADOS = Decimal('20.000')


def _fila_existencia(
    *, id, nombre, tipo, stock_actual, stock_minimo, origen_minimo,
    unidad_medida, activo,
):
    """Conserva la ausencia de inventario y compara cantidades sin usar float."""
    stock = Decimal(stock_actual) if stock_actual is not None else None
    minimo = Decimal(stock_minimo)
    if stock is None:
        estado = 'sin_inventario'
    elif stock < minimo:
        estado = 'bajo_stock'
    else:
        estado = 'normal'

    return {
        'id': id,
        'nombre': nombre,
        'tipo': tipo,
        'stock_actual': stock,
        'stock_minimo': minimo,
        'origen_minimo': origen_minimo,
        'unidad_medida': unidad_medida,
        'estado': estado,
        'activo': activo,
    }


def reporte_existencias(*, tipo='todos', q='', estado='todos') -> dict:
    """Consulta dos catálogos con sus inventarios y resume las filas filtradas.

    Cada ``values`` realiza un LEFT JOIN a la relación uno a uno: incluye
    catálogos sin inventario y evita consultas adicionales por cada fila.
    Los filtros recibidos ya están validados por el serializador de consulta.
    """
    q = q.strip()
    materias_primas = MateriaPrima.objects.all()
    productos = Producto.objects.all()
    if q:
        materias_primas = materias_primas.filter(nombre__icontains=q)
        productos = productos.filter(nombre__icontains=q)

    # Dos SELECT, sin filtrar activo: CU23 también informa catálogos inactivos.
    materias_primas = materias_primas.order_by().values(
        'id_materia_prima', 'nombre', 'stock_minimo', 'unidad_medida',
        'activo', 'inventario__stock_actual',
    )
    productos = productos.order_by().values(
        'id_producto', 'nombre', 'activo', 'inventario_terminado__stock_actual',
    )
    filas = [
        _fila_existencia(
            id=fila['id_materia_prima'],
            nombre=fila['nombre'],
            tipo='materia_prima',
            stock_actual=fila['inventario__stock_actual'],
            stock_minimo=fila['stock_minimo'],
            origen_minimo='catalogo',
            unidad_medida=fila['unidad_medida'],
            activo=fila['activo'],
        )
        for fila in materias_primas
    ]
    filas.extend(
        _fila_existencia(
            id=fila['id_producto'],
            nombre=fila['nombre'],
            tipo='producto_terminado',
            stock_actual=fila['inventario_terminado__stock_actual'],
            stock_minimo=UMBRAL_PRODUCTOS_TERMINADOS,
            origen_minimo='referencial_global',
            unidad_medida='unidades',
            activo=fila['activo'],
        )
        for fila in productos
    )

    resultados = sorted(
        (
            fila for fila in filas
            if (tipo == 'todos' or fila['tipo'] == tipo)
            and (estado == 'todos' or fila['estado'] == estado)
        ),
        key=lambda fila: (fila['tipo'], fila['nombre'], fila['id']),
    )
    return {
        'umbral_productos_terminados': UMBRAL_PRODUCTOS_TERMINADOS,
        'resumen': {
            'total': len(resultados),
            'materias_primas': sum(fila['tipo'] == 'materia_prima' for fila in resultados),
            'productos_terminados': sum(fila['tipo'] == 'producto_terminado' for fila in resultados),
            'bajo_stock': sum(fila['estado'] == 'bajo_stock' for fila in resultados),
            'sin_inventario': sum(fila['estado'] == 'sin_inventario' for fila in resultados),
        },
        'resultados': resultados,
    }
