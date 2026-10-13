"""
Cobro con tarjeta vía Stripe (CU13).

El efectivo no pasa por aquí. El id que devuelve Stripe se guarda en
venta.id_transaccion_stripe.
"""
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError


def _cliente():
    clave = getattr(settings, 'STRIPE_SECRET_KEY', '') or ''
    if not clave:
        raise ValidationError({
            'id_transaccion_stripe': (
                'Stripe no está configurado. Agrega STRIPE_SECRET_KEY en el entorno.'
            )
        })
    stripe.api_key = clave
    return stripe


def moneda() -> str:
    return getattr(settings, 'STRIPE_CURRENCY', 'bob') or 'bob'


def centavos(monto: Decimal) -> int:
    return int((Decimal(monto) * Decimal('100')).quantize(Decimal('1')))


def crear_intencion(*, monto: Decimal) -> dict:
    """Crea el cobro en Stripe. Todavía no existe la venta ni se tocó el stock."""
    cliente = _cliente()
    intento = cliente.PaymentIntent.create(
        amount=centavos(monto),
        currency=moneda(),
        automatic_payment_methods={'enabled': True},
        metadata={'origen': 'cu13-mostrador'},
    )
    return {
        'id_transaccion_stripe': intento.id,
        'client_secret': intento.client_secret,
        'monto': f'{Decimal(monto):.2f}',
        'moneda': moneda(),
    }


def confirmar_cobro_tarjeta(*, id_transaccion_stripe: str, monto: Decimal) -> str:
    """
    La venta con Stripe solo continúa si el cobro ya está succeeded
    y el monto coincide con el total calculado en el servidor.
    """
    referencia = (id_transaccion_stripe or '').strip()
    if not referencia:
        raise ValidationError({
            'id_transaccion_stripe': 'La venta con Stripe requiere el id de la transacción.'
        })

    cliente = _cliente()
    intento = cliente.PaymentIntent.retrieve(referencia)
    if intento.status != 'succeeded':
        raise ValidationError({
            'id_transaccion_stripe': 'Stripe todavía no confirmó el cobro.'
        })
    if intento.currency != moneda() or intento.amount != centavos(monto):
        if intento.status == 'succeeded':
            anular_cobro_tarjeta(referencia)
        raise ValidationError({
            'id_transaccion_stripe': 'El monto cobrado en Stripe no coincide con el total de la venta.'
        })
    return intento.id


def anular_cobro_tarjeta(id_transaccion_stripe: str) -> None:
    """Si el pan ya no alcanza después del cobro, se devuelve el dinero."""
    cliente = _cliente()
    cliente.Refund.create(payment_intent=id_transaccion_stripe)
