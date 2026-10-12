"""
Registro de compras de materia prima (CU7).

Valida, persiste Compra + DetalleCompra, actualiza inventario e historial de
precio, registra movimientos de entrada y deja traza en bitácora (CU26).
"""
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.compras.proveedores.models import Proveedor
from apps.compras.compra_materia_prima.models import Compra, DetalleCompra
from apps.productos_inventario.models import (
    HistorialPrecioMateriaPrima,
    InventarioMateriaPrima,
    MateriaPrima,
    MovimientoMateriaPrima,
    TipoMovimientoMateriaPrima,
)
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora


def _como_decimal(valor, nombre_campo: str) -> Decimal:
    try:
        d = Decimal(valor)
    except Exception as exc:
        raise ValidationError({nombre_campo: f'{nombre_campo} debe ser un número válido.'}) from exc
    return d


def _validar_lineas(lineas) -> list[dict]:
    if not lineas:
        raise ValidationError('La compra debe incluir al menos un detalle.')

    normalizadas: list[dict] = []
    vistos: set[int] = set()

    for indice, raw in enumerate(lineas, start=1):
        if not isinstance(raw, dict):
            raise ValidationError(f'El detalle #{indice} no tiene formato válido.')

        try:
            id_mp = int(raw['id_materia_prima'])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(
                {f'detalle_{indice}': 'Cada línea debe indicar id_materia_prima.'}
            ) from exc

        if id_mp in vistos:
            raise ValidationError(
                'No se puede repetir la misma materia prima en una sola compra.'
            )
        vistos.add(id_mp)

        cantidad = _como_decimal(raw.get('cantidad'), 'cantidad')
        precio_unitario = _como_decimal(raw.get('precio_unitario'), 'precio_unitario')

        if cantidad <= 0:
            raise ValidationError({f'detalle_{indice}': 'La cantidad debe ser mayor a cero.'})
        if precio_unitario <= 0:
            raise ValidationError(
                {f'detalle_{indice}': 'El precio unitario debe ser mayor a cero.'}
            )

        normalizadas.append(
            {
                'id_materia_prima': id_mp,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
            }
        )

    return normalizadas


def _inventarios_bloqueados(ids_materia: list[int]) -> dict[int, InventarioMateriaPrima]:
    """Candado de fila sobre inventario para evitar condiciones de carrera."""
    inventarios = {
        inv.id_materia_prima_id: inv
        for inv in InventarioMateriaPrima.objects.select_for_update().filter(
            id_materia_prima_id__in=ids_materia
        )
    }
    if len(inventarios) != len(ids_materia):
        faltantes = set(ids_materia) - set(inventarios.keys())
        raise ValidationError(
            {
                'lineas': (
                    'Falta registro de inventario para materia(s) prima: '
                    f'{sorted(faltantes)}. Ejecute seed_materias_primas.'
                )
            }
        )
    return inventarios


@transaction.atomic
def registrar_compra(*, usuario, id_proveedor, lineas, agente_usuario=None):
    """
    Registra una compra completa: cabecera, detalle, stock, precio y auditoría.

    Parámetros
    ----------
    usuario : Usuario autenticado que registra la operación.
    id_proveedor : PK del proveedor.
    lineas : lista de dicts con id_materia_prima, cantidad, precio_unitario.
    agente_usuario : User-Agent HTTP para bitácora (opcional).

    Retorna
    -------
    Compra con detalles persistidos y total actualizado.
    """
    lineas_norm = _validar_lineas(lineas)

    try:
        proveedor = Proveedor.objects.get(pk=id_proveedor)
    except Proveedor.DoesNotExist as exc:
        raise ValidationError({'id_proveedor': 'El proveedor indicado no existe.'}) from exc

    if not proveedor.activo:
        raise ValidationError({'id_proveedor': 'El proveedor está inactivo.'})

    ids_mp = [l['id_materia_prima'] for l in lineas_norm]
    materias = MateriaPrima.objects.in_bulk(ids_mp)
    if len(materias) != len(ids_mp):
        faltantes = set(ids_mp) - set(materias.keys())
        raise ValidationError(
            {'lineas': f'Materia(s) prima no encontrada(s): {sorted(faltantes)}.'}
        )

    for materia in materias.values():
        if not materia.activo:
            raise ValidationError(
                {'lineas': f'La materia prima «{materia.nombre}» está inactiva.'}
            )

    inventarios = _inventarios_bloqueados(ids_mp)

    compra = Compra.objects.create(
        id_proveedor=proveedor,
        id_usuario=usuario,
        total=Decimal('0'),
    )

    total = Decimal('0')
    for linea in lineas_norm:
        materia = materias[linea['id_materia_prima']]
        inventario = inventarios[materia.id_materia_prima]
        cantidad = linea['cantidad']
        precio_unitario = linea['precio_unitario']

        subtotal = (cantidad * precio_unitario).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )
        DetalleCompra.objects.create(
            id_compra=compra,
            id_materia_prima=materia,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            subtotal=subtotal,
        )
        total += subtotal

        inventario.stock_actual += cantidad
        inventario.save(update_fields=['stock_actual'])

        HistorialPrecioMateriaPrima.objects.create(
            id_materia_prima=materia,
            precio=precio_unitario,
        )

        MovimientoMateriaPrima.objects.create(
            id_inventario=inventario,
            id_compra=compra,
            tipo=TipoMovimientoMateriaPrima.ENTRADA,
            cantidad=cantidad,
        )

    compra.total = total
    compra.save(update_fields=['total'])

    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.ALTA_COMPRA,
        tabla_afectada='compra',
        descripcion=(
            f'Compra #{compra.id_compra} — proveedor {proveedor.nombre} — '
            f'total Bs {compra.total}'
        ),
        agente_usuario=agente_usuario,
    )

    return compra
