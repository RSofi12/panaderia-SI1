"""
Modelos para el Módulo de Producción e Inventario de Productos Terminados.

Casos de Uso abordados:
  - CU10: Registrar producción diaria
  - CU11: Consultar historial de producción
  - CU12: Consultar existencias de productos terminados
  - CU18: Registrar baja de productos terminados (mermas)

Cumple con el esquema relacional de Database_Panaderia_Santiago.sql.
"""
from decimal import Decimal

from django.db import models
from django.utils import timezone


class JornadaProduccion(models.TextChoices):
    MANANA = 'Mañana', 'Mañana'
    TARDE = 'Tarde', 'Tarde'
    NOCHE = 'Noche', 'Noche'


class Produccion(models.Model):
    """
    Cabecera de la jornada / lote de producción de pan (tabla 'produccion').
    CU10, CU11.
    """
    id_produccion = models.BigAutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='producciones',
        verbose_name='Responsable de producción',
    )
    fecha = models.DateField(default=timezone.now, verbose_name='Fecha de producción')
    jornada = models.CharField(
        max_length=20,
        choices=JornadaProduccion.choices,
        default=JornadaProduccion.MANANA,
        verbose_name='Jornada',
    )

    class Meta:
        db_table = 'produccion'
        verbose_name = 'Producción'
        verbose_name_plural = 'Producciones'
        ordering = ['-fecha', '-id_produccion']

    def __str__(self):
        return f'Producción #{self.id_produccion} — {self.fecha} ({self.jornada})'


class DetalleProduccion(models.Model):
    """
    Línea de producción por tipo de producto (tabla 'detalle_produccion').
    CU10, CU11.
    """
    id_detalle_produccion = models.BigAutoField(primary_key=True)
    id_produccion = models.ForeignKey(
        Produccion,
        on_delete=models.CASCADE,
        db_column='id_produccion',
        related_name='detalles',
        verbose_name='Producción',
    )
    id_producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto',
        related_name='detalles_produccion',
        verbose_name='Producto elaborado',
    )
    cantidad_producida = models.PositiveIntegerField(verbose_name='Cantidad producida (unidades)')
    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Costo unitario (Bs)',
    )

    class Meta:
        db_table = 'detalle_produccion'
        verbose_name = 'Detalle de producción'
        verbose_name_plural = 'Detalles de producción'

    def __str__(self):
        return f'{self.id_producto.nombre}: {self.cantidad_producida} un.'


class InventarioProductoTerminado(models.Model):
    """
    Stock actual de producto terminado listo para la venta (tabla 'inventario_producto_terminado').
    CU12.
    """
    id_inventario = models.BigAutoField(primary_key=True)
    id_producto = models.OneToOneField(
        'productos.Producto',
        on_delete=models.PROTECT,
        db_column='id_producto',
        related_name='inventario_terminado',
        verbose_name='Producto',
    )
    stock_actual = models.IntegerField(default=0, verbose_name='Stock actual (unidades)')

    class Meta:
        db_table = 'inventario_producto_terminado'
        verbose_name = 'Inventario de producto terminado'
        verbose_name_plural = 'Inventarios de productos terminados'

    def __str__(self):
        return f'{self.id_producto.nombre}: {self.stock_actual} unidades'


class TipoMovimientoProductoTerminado(models.TextChoices):
    ENTRADA = 'entrada', 'Entrada'
    SALIDA = 'salida', 'Salida'


class MovimientoProductoTerminado(models.Model):
    """
    Kardex / trazabilidad de entradas y salidas de pan terminado (tabla 'movimiento_producto_terminado').
    """
    id_movimiento = models.BigAutoField(primary_key=True)
    id_inventario = models.ForeignKey(
        InventarioProductoTerminado,
        on_delete=models.PROTECT,
        db_column='id_inventario',
        related_name='movimientos',
        verbose_name='Inventario',
    )
    id_produccion = models.ForeignKey(
        Produccion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='id_produccion',
        related_name='movimientos_producto',
        verbose_name='Producción de origen',
    )
    id_nota_perdida = models.ForeignKey(
        'NotaPerdidaProducto',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='id_nota_perdida',
        related_name='movimientos_producto',
        verbose_name='Nota de pérdida',
    )
    fecha_hora = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora')
    tipo = models.CharField(
        max_length=10,
        choices=TipoMovimientoProductoTerminado.choices,
        verbose_name='Tipo de movimiento',
    )
    cantidad = models.IntegerField(verbose_name='Cantidad')

    class Meta:
        db_table = 'movimiento_producto_terminado'
        verbose_name = 'Movimiento de producto terminado'
        verbose_name_plural = 'Movimientos de productos terminados'
        ordering = ['-fecha_hora', '-id_movimiento']

    def __str__(self):
        return f'{self.tipo} {self.cantidad} — {self.id_inventario.id_producto.nombre}'


class NotaPerdidaProducto(models.Model):
    """
    Registro de mermas o pérdidas de pan terminado no vendido (tabla 'nota_perdida_producto').
    CU18.
    """
    id_nota_perdida = models.BigAutoField(primary_key=True)
    id_detalle_produccion = models.ForeignKey(
        DetalleProduccion,
        on_delete=models.PROTECT,
        db_column='id_detalle_produccion',
        related_name='notas_perdida',
        verbose_name='Detalle de producción de origen',
    )
    id_usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='notas_perdida',
        verbose_name='Registrado por',
    )
    cantidad = models.PositiveIntegerField(verbose_name='Cantidad de merma')
    costo_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Costo unitario (Bs)',
    )
    fecha_salida = models.DateTimeField(default=timezone.now, verbose_name='Fecha de salida')

    class Meta:
        db_table = 'nota_perdida_producto'
        verbose_name = 'Nota de pérdida de producto'
        verbose_name_plural = 'Notas de pérdida de producto'
        ordering = ['-fecha_salida', '-id_nota_perdida']

    def __str__(self):
        return f'Pérdida #{self.id_nota_perdida}: {self.cantidad} un. ({self.id_detalle_produccion.id_producto.nombre})'
