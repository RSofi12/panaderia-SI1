from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class MetodoPago(models.TextChoices):
    """CU13: el mostrador cobra en efectivo o con Stripe."""
    EFECTIVO = 'efectivo', 'Efectivo'
    STRIPE = 'stripe', 'Stripe'


class Venta(models.Model):
    """
    Venta de mostrador (CU13) o de un pedido entregado (CU14).
    id_pedido queda vacío en el mostrador. Al entregar, una venta apunta a un solo pedido.
    """
    id_venta = models.BigAutoField(primary_key=True)
    id_pedido = models.OneToOneField(
        'pedidos.Pedido',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='id_pedido',
        related_name='venta',
        verbose_name='Pedido de origen',
    )
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='ventas_registradas',
        verbose_name='Cajero',
    )
    numero_comprobante = models.PositiveBigIntegerField(
        unique=True,
        verbose_name='Número de comprobante',
    )
    fecha_hora = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora')
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        verbose_name='Método de pago',
    )
    id_transaccion_stripe = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Id de transacción Stripe',
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Total (Bs)',
    )

    class Meta:
        db_table = 'venta'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha_hora', '-id_venta']
        constraints = [
            models.CheckConstraint(
                condition=Q(metodo_pago__in=[MetodoPago.EFECTIVO, MetodoPago.STRIPE]),
                name='venta_metodo_pago_valido',
            ),
            models.CheckConstraint(
                condition=(
                    Q(metodo_pago=MetodoPago.EFECTIVO, id_transaccion_stripe__isnull=True)
                    | Q(metodo_pago=MetodoPago.STRIPE, id_transaccion_stripe__isnull=False)
                ),
                name='venta_stripe_coherente',
            ),
            models.UniqueConstraint(
                fields=['id_transaccion_stripe'],
                condition=Q(id_transaccion_stripe__isnull=False),
                name='venta_id_transaccion_stripe_unica',
            ),
        ]

    def __str__(self):
        return f'Comprobante {self.numero_comprobante} — Bs {self.total}'


class DetalleVenta(models.Model):
    """Línea de la venta. El precio queda congelado al momento del cobro."""
    id_detalle_venta = models.BigAutoField(primary_key=True)
    id_venta = models.ForeignKey(
        Venta,
        on_delete=models.PROTECT,
        db_column='id_venta',
        related_name='detalles',
        verbose_name='Venta',
    )
    id_producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto',
        related_name='detalles_venta',
        verbose_name='Producto',
    )
    cantidad = models.PositiveIntegerField(verbose_name='Cantidad (unidades)')
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario (Bs)',
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Subtotal (Bs)',
    )

    class Meta:
        db_table = 'detalle_venta'
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'
        ordering = ['id_detalle_venta']

    def __str__(self):
        return f'{self.id_producto.nombre}: {self.cantidad} × Bs {self.precio_unitario}'
