"""
Servicios de dominio para Producción Diaria (CU10).

Responsabilidades:
  - simular_consumo_produccion: Explosión de materiales (BOM) y balance en tiempo real.
  - calcular_costo_unitario_producto: Cálculo dinámico de costo basado en insumos e historial de precios.
  - registrar_produccion_diaria: Transacción atómica de registro con select_for_update,
    descuento de insumos, incremento de producto terminado, kardex y bitácora.
"""
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.productos_inventario.materia_prima.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
    MovimientoMateriaPrima,
    TipoMovimientoMateriaPrima,
)
from apps.productos_inventario.productos.models import Producto, ProductoMateriaPrima
from apps.productos_inventario.productos_terminados.models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    TipoMovimientoProductoTerminado,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from .models import DetalleProduccion, JornadaProduccion, Produccion


def normalizar_jornada(valor: str) -> str:
    """Normaliza variantes del texto de jornada a las opciones permitidas por el modelo."""
    if not valor:
        return JornadaProduccion.MANANA

    val = str(valor).strip().lower()
    if val in ('mañana', 'manana'):
        return JornadaProduccion.MANANA
    if val == 'tarde':
        return JornadaProduccion.TARDE
    if val == 'noche':
        return JornadaProduccion.NOCHE
    if val in ('unica', 'jornada única', 'jornada unica'):
        return JornadaProduccion.UNICA
    return valor


def calcular_costo_unitario_producto(producto: Producto) -> Decimal:
    """
    Calcula el costo unitario de elaboración de un producto:
    sum(cantidad_requerida * precio_actual_insumo).
    Si no hay recetas o precios registrados, retrocede al costo_produccion base del producto.
    """
    recetas = list(producto.receta_detalles.select_related('id_materia_prima').all())
    if not recetas:
        return Decimal(producto.costo_produccion).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    costo_acumulado = Decimal('0.00')
    for r in recetas:
        ultimo_precio = (
            HistorialPrecioMateriaPrima.objects
            .filter(id_materia_prima=r.id_materia_prima)
            .order_by('-fecha_inicio', '-id_historial')
            .first()
        )
        precio_insumo = ultimo_precio.precio if ultimo_precio else Decimal('0.00')
        costo_acumulado += Decimal(r.cantidad_requerida) * precio_insumo

    if costo_acumulado > Decimal('0.00'):
        return costo_acumulado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return Decimal(producto.costo_produccion).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def consolidar_renglones_produccion(detalles_input: list) -> list:
    """
    Filtra cantidades positivas y consolida posibles renglones duplicados del mismo producto.
    Retorna lista de tuplas (id_producto, cantidad_producida).
    """
    cantidades_por_producto = defaultdict(int)
    for d in detalles_input:
        id_prod = d.get('id_producto')
        cant = int(d.get('cantidad_producida', 0))
        if id_prod and cant > 0:
            cantidades_por_producto[int(id_prod)] += cant

    return list(cantidades_por_producto.items())


def simular_consumo_produccion(detalles_input: list) -> dict:
    """
    Simulación y explosión de materiales en tiempo real (MRP) para CU10.
    Calcula el consumo proyectado de cada insumo y evalúa si el inventario actual es suficiente.
    """
    renglones = consolidar_renglones_produccion(detalles_input)
    if not renglones:
        return {
            'es_viable': True,
            'total_panes_unidades': 0,
            'costo_estimado_total': '0.00',
            'insumos': [],
        }

    ids_productos = [item[0] for item in renglones]
    productos = {
        p.id_producto: p
        for p in Producto.objects.filter(id_producto__in=ids_productos).prefetch_related('receta_detalles__id_materia_prima')
    }

    consumo_por_insumo = defaultdict(Decimal)
    materias_map = {}
    total_unidades = 0
    costo_estimado = Decimal('0.00')

    for id_prod, cant in renglones:
        prod = productos.get(id_prod)
        if not prod:
            continue
        total_unidades += cant
        costo_unit = calcular_costo_unitario_producto(prod)
        costo_estimado += costo_unit * Decimal(cant)

        for receta in prod.receta_detalles.all():
            mp = receta.id_materia_prima
            materias_map[mp.id_materia_prima] = mp
            consumo_por_insumo[mp.id_materia_prima] += Decimal(receta.cantidad_requerida) * Decimal(cant)

    # Consultar existencias actuales de cada insumo requerido
    inventarios = {
        inv.id_materia_prima_id: inv.stock_actual
        for inv in InventarioMateriaPrima.objects.filter(id_materia_prima_id__in=consumo_por_insumo.keys())
    }

    es_viable = True
    insumos_calculados = []

    for id_mp, cantidad_req in consumo_por_insumo.items():
        mp = materias_map[id_mp]
        stock_disp = inventarios.get(id_mp, Decimal('0.000'))
        cantidad_req = cantidad_req.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        suficiente = stock_disp >= cantidad_req
        if not suficiente:
            es_viable = False

        diferencia = Decimal('0.000') if suficiente else (cantidad_req - stock_disp).quantize(Decimal('0.001'))

        insumos_calculados.append({
            'id_materia_prima': id_mp,
            'nombre_insumo': mp.nombre,
            'unidad_medida': mp.unidad_medida,
            'cantidad_requerida': float(cantidad_req),
            'stock_disponible': float(stock_disp),
            'suficiente': suficiente,
            'diferencia_faltante': float(diferencia),
        })

    # Ordenar insumos por nombre
    insumos_calculados.sort(key=lambda x: x['nombre_insumo'])

    return {
        'es_viable': es_viable,
        'total_panes_unidades': total_unidades,
        'costo_estimado_total': str(costo_estimado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        'insumos': insumos_calculados,
    }


def registrar_produccion_diaria(
    *,
    usuario,
    fecha,
    jornada: str,
    detalles_input: list,
    agente_usuario: str = None
) -> Produccion:
    """
    Registra una jornada de producción de pan de forma atómica (CU10).

    Operaciones ejecutadas dentro de transaction.atomic():
      1. Consolida productos y valida cantidades > 0.
      2. Bloqueo pesimista con select_for_update() de InventarioMateriaPrima.
      3. Verificación estricta de stock disponible frente al consumo calculado.
      4. Alta de cabecera Produccion y renglones DetalleProduccion con costo unitario.
      5. Descuento de insumos y generación de MovimientoMateriaPrima ('salida').
      6. Alta/actualización en InventarioProductoTerminado y MovimientoProductoTerminado ('entrada').
      7. Auditoría en Bitacora (CU26).
    """
    renglones = consolidar_renglones_produccion(detalles_input)
    if not renglones:
        raise ValidationError('Debe incluir al menos un producto con cantidad producida mayor a 0.')

    ids_productos = [item[0] for item in renglones]
    productos = {
        p.id_producto: p
        for p in Producto.objects.filter(id_producto__in=ids_productos, activo=True).prefetch_related('receta_detalles__id_materia_prima')
    }

    if len(productos) != len(ids_productos):
        raise ValidationError('Uno o más productos seleccionados no existen o están inactivos.')

    # Calcular explosión de insumos
    consumo_por_insumo = defaultdict(Decimal)
    materias_map = {}
    items_procesados = []

    for id_prod, cant in renglones:
        prod = productos[id_prod]
        recetas = list(prod.receta_detalles.all())
        if not recetas:
            raise ValidationError(f'El producto "{prod.nombre}" no tiene una receta registrada (BOM).')

        costo_unit = calcular_costo_unitario_producto(prod)
        items_procesados.append({
            'producto': prod,
            'cantidad': cant,
            'costo_unitario': costo_unit,
        })

        for r in recetas:
            mp = r.id_materia_prima
            materias_map[mp.id_materia_prima] = mp
            consumo_por_insumo[mp.id_materia_prima] += Decimal(r.cantidad_requerida) * Decimal(cant)

    jornada_normalizada = normalizar_jornada(jornada)

    with transaction.atomic():
        # 1. Bloqueo pesimista de materias primas involucradas
        ids_mp_ordenados = sorted(consumo_por_insumo.keys())
        inventarios_mp = {
            inv.id_materia_prima_id: inv
            for inv in InventarioMateriaPrima.objects.select_for_update().filter(id_materia_prima_id__in=ids_mp_ordenados)
        }

        # 2. Validación de disponibilidad suficiente
        faltantes = []
        for id_mp in ids_mp_ordenados:
            cant_req = consumo_por_insumo[id_mp].quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            inv = inventarios_mp.get(id_mp)
            stock_disp = inv.stock_actual if inv else Decimal('0.000')

            if stock_disp < cant_req:
                mp = materias_map[id_mp]
                faltante = (cant_req - stock_disp).quantize(Decimal('0.001'))
                faltantes.append(f'{mp.nombre} (faltan {faltante} {mp.unidad_medida})')

        if faltantes:
            raise ValidationError(
                f"No hay suficiente materia prima para registrar esta producción: {', '.join(faltantes)}."
            )

        # 3. Crear cabecera Produccion
        produccion = Produccion.objects.create(
            id_usuario=usuario,
            fecha=fecha,
            jornada=jornada_normalizada,
        )

        # 4. Crear renglones DetalleProduccion
        detalles_objs = [
            DetalleProduccion(
                id_produccion=produccion,
                id_producto=item['producto'],
                cantidad_producida=item['cantidad'],
                costo_unitario=item['costo_unitario'],
            )
            for item in items_procesados
        ]
        DetalleProduccion.objects.bulk_create(detalles_objs)

        # 5. Descontar stock de insumos y registrar kardex de salida
        movimientos_mp = []
        for id_mp in ids_mp_ordenados:
            cant_req = consumo_por_insumo[id_mp].quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            inv = inventarios_mp[id_mp]
            inv.stock_actual = (inv.stock_actual - cant_req).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
            inv.save(update_fields=['stock_actual'])

            movimientos_mp.append(MovimientoMateriaPrima(
                id_inventario=inv,
                id_produccion=produccion,
                tipo=TipoMovimientoMateriaPrima.SALIDA,
                cantidad=cant_req,
            ))
        MovimientoMateriaPrima.objects.bulk_create(movimientos_mp)

        # 6. Incrementar stock de productos terminados y registrar kardex de entrada
        movimientos_pt = []
        for item in items_procesados:
            prod = item['producto']
            cant = item['cantidad']

            inv_pt, _ = InventarioProductoTerminado.objects.select_for_update().get_or_create(
                id_producto=prod,
                defaults={'stock_actual': 0}
            )
            inv_pt.stock_actual += cant
            inv_pt.save(update_fields=['stock_actual'])

            movimientos_pt.append(MovimientoProductoTerminado(
                id_inventario=inv_pt,
                id_produccion=produccion,
                tipo=TipoMovimientoProductoTerminado.ENTRADA,
                cantidad=cant,
            ))
        MovimientoProductoTerminado.objects.bulk_create(movimientos_pt)

        # 7. Registrar en bitácora (CU26)
        total_panes = sum(item['cantidad'] for item in items_procesados)
        Bitacora.registrar(
            usuario=usuario,
            accion=AccionBitacora.REGISTRO_PRODUCCION,
            tabla_afectada='produccion',
            descripcion=(
                f'Registro de producción #{produccion.id_produccion} — {produccion.fecha} ({produccion.jornada}): '
                f'{total_panes} unidades en {len(detalles_objs)} variedades elaboradas.'
            ),
            agente_usuario=agente_usuario,
        )

    return produccion
