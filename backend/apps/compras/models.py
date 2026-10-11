from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Proveedor(models.Model):
    """
    Maestro de proveedores de materias primas e insumos (CU6).
    Cumple con la tabla 'proveedor' de Database_Panaderia_Santiago.sql.
    No se borra: la baja es activo=False (soft delete).
    """
    id_proveedor = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150, verbose_name='Nombre del proveedor')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    direccion = models.CharField(max_length=200, blank=True, null=True, verbose_name='Dirección')
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    activo = models.BooleanField(default=True, verbose_name='Proveedor activo')

    class Meta:
        db_table = 'proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                Lower('nombre'),
                name='proveedor_nombre_unico_ci',
            ),
        ]

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    """
    Cabecera de compra de materias primas (CU7).
    Cumple con la tabla 'compra' de Database_Panaderia_Santiago.sql.
    """
    id_compra = models.BigAutoField(primary_key=True)
    id_proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        db_column='id_proveedor',
        related_name='compras',
        verbose_name='Proveedor',
    )
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='compras_registradas',
        verbose_name='Usuario que registró',
    )
    fecha_hora = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora')
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Total (Bs)',
    )

    class Meta:
        db_table = 'compra'
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha_hora', '-id_compra']

    def __str__(self):
        return f'Compra #{self.id_compra} — {self.id_proveedor.nombre} (Bs {self.total})'


class DetalleCompra(models.Model):
    """
    Línea de detalle de una compra (CU7).
    Cumple con la tabla 'detalle_compra' de Database_Panaderia_Santiago.sql.
    """
    id_detalle_compra = models.BigAutoField(primary_key=True)
    id_compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        db_column='id_compra',
        related_name='detalles',
        verbose_name='Compra',
    )
    id_materia_prima = models.ForeignKey(
        'productos_inventario.MateriaPrima',
        on_delete=models.PROTECT,
        db_column='id_materia_prima',
        related_name='detalles_compra',
        verbose_name='Materia prima',
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Cantidad')
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Precio unitario (Bs)',
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal (Bs)')

    class Meta:
        db_table = 'detalle_compra'
        verbose_name = 'Detalle de compra'
        verbose_name_plural = 'Detalles de compra'
        ordering = ['id_detalle_compra']

    def __str__(self):
        mp = self.id_materia_prima
        return (
            f'{mp.nombre}: {self.cantidad} {mp.unidad_medida} '
            f'× Bs {self.precio_unitario} = Bs {self.subtotal}'
        )

