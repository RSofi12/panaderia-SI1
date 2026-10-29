from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.comercializacion.ventas.models import MetodoPago


class EstadoPedido(models.TextChoices):
    """CU14: el pedido nace pendiente y solo al entregarse se vincula con una venta."""
    PENDIENTE = 'pendiente', 'Pendiente'
    EN_PREPARACION = 'en_preparacion', 'En preparación'
    LISTO = 'listo', 'Listo'
    ENTREGADO = 'entregado', 'Entregado'
    CANCELADO = 'cancelado', 'Cancelado'


class Cliente(models.Model):
    """
    Quien pide pan. No tiene usuario ni login.
    Tabla 'cliente' del DDL.
    """
    id_cliente = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150, verbose_name='Nombre')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    direccion = models.CharField(max_length=200, blank=True, null=True, verbose_name='Dirección')

    class Meta:
        db_table = 'cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre', 'id_cliente']

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    """
    Solicitud anticipada (CU14).
    La venta 0..1 no vive aquí: venta.id_pedido se agrega al entregar.
    """
    id_pedido = models.BigAutoField(primary_key=True)
    id_cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        db_column='id_cliente',
        related_name='pedidos',
        verbose_name='Cliente',
    )
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='pedidos_registrados',
        verbose_name='Registrado por',
    )
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    fecha_entrega = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de entrega prevista',
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoPedido.choices,
        default=EstadoPedido.PENDIENTE,
        verbose_name='Estado',
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        blank=True,
        null=True,
        verbose_name='Método de pago previsto',
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Total (Bs)',
    )

    class Meta:
        db_table = 'pedido'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_registro', '-id_pedido']
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=[
                    EstadoPedido.PENDIENTE,
                    EstadoPedido.EN_PREPARACION,
                    EstadoPedido.LISTO,
                    EstadoPedido.ENTREGADO,
                    EstadoPedido.CANCELADO,
                ]),
                name='pedido_estado_valido',
            ),
            models.CheckConstraint(
                condition=Q(metodo_pago__isnull=True) | Q(metodo_pago__in=[
                    MetodoPago.EFECTIVO,
                    MetodoPago.STRIPE,
                ]),
                name='pedido_metodo_pago_valido',
            ),
        ]

    def __str__(self):
        return f'Pedido {self.id_pedido} — {self.estado}'


class DetallePedido(models.Model):
    """Línea del pedido. El precio queda congelado al registrarlo."""
    id_detalle_pedido = models.BigAutoField(primary_key=True)
    id_pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        db_column='id_pedido',
        related_name='detalles',
        verbose_name='Pedido',
    )
    id_producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto',
        related_name='detalles_pedido',
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
        db_table = 'detalle_pedido'
        verbose_name = 'Detalle de pedido'
        verbose_name_plural = 'Detalles de pedido'
        ordering = ['id_detalle_pedido']

    def __str__(self):
        return f'{self.id_producto_id}: {self.cantidad} × Bs {self.precio_unitario}'
