"""
Registro y anulación de gastos operativos e inversiones (CU20).

Persiste el movimiento económico y deja traza en bitácora (CU26) dentro de una
sola transacción: si falla la auditoría, el cambio tampoco queda guardado.
El usuario responsable nunca se recibe del cliente; lo aporta la vista desde
`request.user`.
"""
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora

from ..models import (
    CategoriaMovimientoEconomico,
    MovimientoEconomico,
    TipoMovimientoEconomico,
)


def _como_decimal(valor) -> Decimal:
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({'monto': 'El monto debe ser un número válido.'}) from exc

    if not monto.is_finite():
        raise ValidationError({'monto': 'El monto debe ser un número válido.'})
    return monto


def _validar_fecha_no_futura(fecha_hora):
    if fecha_hora is None:
        return None
    if timezone.is_naive(fecha_hora):
        fecha_hora = timezone.make_aware(fecha_hora)
    if fecha_hora > timezone.now():
        raise ValidationError({'fecha_hora': 'La fecha no puede ser futura.'})
    return fecha_hora


@transaction.atomic
def registrar_movimiento(*, usuario, tipo, concepto, monto, categoria=None,
                         descripcion=None, fecha_hora=None, agente_usuario=None):
    concepto = (concepto or '').strip()
    if not concepto:
        raise ValidationError({'concepto': 'El concepto es obligatorio.'})

    if tipo not in TipoMovimientoEconomico.values:
        raise ValidationError(
            {'tipo': f'Tipo inválido. Use {", ".join(TipoMovimientoEconomico.values)}.'}
        )

    categoria = categoria or CategoriaMovimientoEconomico.OTROS
    if categoria not in CategoriaMovimientoEconomico.values:
        raise ValidationError(
            {'categoria': f'Categoría inválida. Use {", ".join(CategoriaMovimientoEconomico.values)}.'}
        )

    monto = _como_decimal(monto)
    if monto <= 0:
        raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})

    descripcion = (descripcion or '').strip() or None
    fecha_hora = _validar_fecha_no_futura(fecha_hora)

    datos = dict(
        id_usuario=usuario,
        tipo=tipo,
        categoria=categoria,
        concepto=concepto,
        descripcion=descripcion,
        monto=monto,
    )
    if fecha_hora is not None:
        datos['fecha_hora'] = fecha_hora

    movimiento = MovimientoEconomico.objects.create(**datos)

    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.ALTA_MOVIMIENTO_ECONOMICO,
        tabla_afectada='movimiento_economico',
        descripcion=(
            f'Movimiento #{movimiento.id_movimiento} — '
            f'{movimiento.get_tipo_display()} / {movimiento.get_categoria_display()}: '
            f'{concepto} — Bs {monto}'
        ),
        agente_usuario=agente_usuario,
    )

    return movimiento


@transaction.atomic
def anular_movimiento(*, usuario, id_movimiento, motivo=None, agente_usuario=None):
    """
    Anula un movimiento sin borrarlo: conserva la fila y la auditoría.

    Se bloquea la fila para que dos anulaciones simultáneas no generen dos
    registros de bitácora del mismo hecho.
    """
    movimiento = (
        MovimientoEconomico.objects.select_for_update()
        .select_related('id_usuario')
        .get(pk=id_movimiento)
    )
    if movimiento.anulado:
        raise ValidationError({'detail': 'El movimiento ya está anulado.'})

    movimiento.anulado = True
    movimiento.save(update_fields=['anulado'])

    motivo_limpio = (motivo or '').strip()
    motivo_texto = f' — Motivo: {motivo_limpio}' if motivo_limpio else ''

    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.ANULACION_MOVIMIENTO_ECONOMICO,
        tabla_afectada='movimiento_economico',
        descripcion=(
            f'Anulación del movimiento #{movimiento.id_movimiento} — '
            f'{movimiento.get_tipo_display()}: {movimiento.concepto} — Bs {movimiento.monto}'
            f'{motivo_texto}'
        ),
        agente_usuario=agente_usuario,
    )

    return movimiento
