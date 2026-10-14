"""
Cobro con tarjeta vía Stripe (CU13).

El efectivo no pasa por aquí. El id que devuelve Stripe se guarda en
venta.id_transaccion_stripe.
"""
import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def _cliente():
    clave = (getattr(settings, 'STRIPE_SECRET_KEY', '') or '').strip().strip("'\"")
    if not clave:
        raise ValidationError({
            'id_transaccion_stripe': (
                'Stripe no está configurado. Agrega STRIPE_SECRET_KEY en el entorno.'
            )
        })
    stripe.api_key = clave
    return stripe


def moneda() -> str:
    return (getattr(settings, 'STRIPE_CURRENCY', 'bob') or 'bob').strip().lower()


def centavos(monto: Decimal) -> int:
    return int((Decimal(monto) * Decimal('100')).quantize(Decimal('1')))


def crear_intencion(*, monto: Decimal) -> dict:
    """Crea el cobro en Stripe. Todavía no existe la venta ni se tocó el stock."""
    cliente = _cliente()
    try:
        intento = cliente.PaymentIntent.create(
            amount=centavos(monto),
            currency=moneda(),
            automatic_payment_methods={'enabled': True},
            metadata={'origen': 'cu13-mostrador'},
        )
    except stripe.error.InvalidRequestError as exc:
        msg = str(exc)
        if 'at least 50 cents' in msg or 'Amount must convert' in msg:
            raise ValidationError({
                'detalles': (
                    f'El monto total (Bs {Decimal(monto):.2f}) es inferior al mínimo admitido por '
                    'la pasarela Stripe (equivalente a $0.50 USD, aprox. Bs 6.00). '
                    'Para compras menores, utiliza el pago en efectivo o añade más unidades.'
                )
            }) from exc
        raise ValidationError({
            'detalles': f'Error en pasarela Stripe: {getattr(exc, "user_message", None) or str(exc)}'
        }) from exc
    except stripe.error.StripeError as exc:
        raise ValidationError({
            'detalles': f'Error en pasarela Stripe: {getattr(exc, "user_message", None) or str(exc)}'
        }) from exc

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
    try:
        intento = cliente.PaymentIntent.retrieve(referencia)
    except stripe.error.StripeError as exc:
        raise ValidationError({
            'id_transaccion_stripe': (
                f'Error al verificar la transacción en Stripe: {getattr(exc, "user_message", None) or str(exc)}'
            )
        }) from exc

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
    referencia = (id_transaccion_stripe or '').strip()
    if not referencia:
        return
    cliente = _cliente()
    try:
        cliente.Refund.create(payment_intent=referencia)
    except stripe.error.StripeError as exc:
        logger.warning(
            'No se pudo anular en Stripe el cobro %s: %s',
            referencia,
            exc,
        )


def cobrar_con_tarjeta_manual(*, monto: Decimal, datos_tarjeta: dict) -> str:
    """
    Procesa un cobro con tarjeta directamente contra la pasarela Stripe (modo pruebas)
    utilizando los datos ingresados manualmente en el modal.
    Devuelve el id del PaymentIntent confirmado (pi_...).
    """
    numero = ''.join(c for c in str(datos_tarjeta.get('numero', '')) if c.isdigit())
    if len(numero) < 13 or len(numero) > 19:
        raise ValidationError({'tarjeta': 'El número de tarjeta debe contener 16 dígitos.'})

    try:
        exp_mes = int(datos_tarjeta.get('exp_mes', 0))
        exp_anio = int(datos_tarjeta.get('exp_anio', 0))
    except (ValueError, TypeError):
        raise ValidationError({'tarjeta': 'La fecha de vencimiento es inválida (MM/AA).'})

    if exp_mes < 1 or exp_mes > 12:
        raise ValidationError({'tarjeta': 'El mes de vencimiento debe estar entre 01 y 12.'})

    # Si el año viene en 2 dígitos (ej: 28), convertir a 2028
    if exp_anio < 100:
        exp_anio += 2000

    cvc = str(datos_tarjeta.get('cvc', '')).strip()
    if len(cvc) < 3 or len(cvc) > 4 or not cvc.isdigit():
        raise ValidationError({'tarjeta': 'El código de seguridad (CVC) debe tener 3 dígitos.'})

    titular = (datos_tarjeta.get('titular', '') or 'Cliente Mostrador').strip()

    # Mapeo a métodos de tarjeta de prueba de Stripe según el número ingresado
    if numero.endswith('0002'):
        metodo_tarjeta = 'pm_card_chargeDeclined'
    elif numero.endswith('9995'):
        metodo_tarjeta = 'pm_card_chargeDeclinedInsufficientFunds'
    else:
        metodo_tarjeta = 'pm_card_visa'

    cliente = _cliente()
    try:
        intento = cliente.PaymentIntent.create(
            amount=centavos(monto),
            currency=moneda(),
            payment_method=metodo_tarjeta,
            confirm=True,
            automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'},
            metadata={'origen': 'cu13-mostrador', 'titular': titular},
        )
    except stripe.error.CardError as exc:
        raise ValidationError({'tarjeta': exc.user_message or 'La tarjeta fue declinada por el banco emisor.'}) from exc
    except stripe.error.InvalidRequestError as exc:
        msg = str(exc)
        if 'at least 50 cents' in msg or 'Amount must convert' in msg:
            raise ValidationError({
                'detalles': (
                    f'El monto total (Bs {Decimal(monto):.2f}) es inferior al mínimo admitido por '
                    'la pasarela Stripe (equivalente a $0.50 USD, aprox. Bs 6.00).'
                )
            }) from exc
        raise ValidationError({'tarjeta': f'Error en Stripe: {exc.user_message or str(exc)}'}) from exc
    except stripe.error.StripeError as exc:
        raise ValidationError({'tarjeta': f'Error en pasarela Stripe: {exc.user_message or str(exc)}'}) from exc

    if intento.status != 'succeeded':
        raise ValidationError({'tarjeta': f'El cobro en Stripe no se completó (estado: {intento.status}).'})

    return intento.id
