from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.utils import timezone


class CategoriaProducto(models.Model):
    """Categoría del catálogo de panes (tabla 'categoria_producto')."""
    id_categoria = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50, verbose_name='Nombre de la categoría')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'categoria_producto'
        verbose_name = 'Categoría de producto'
        verbose_name_plural = 'Categorías de producto'
        ordering = ['id_categoria']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Producto terminado del catálogo (CU5).
    Cumple con la tabla 'producto' de Database_Panaderia_Santiago.sql.
    """
    id_producto = models.BigAutoField(primary_key=True)
    id_categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='id_categoria',
        related_name='productos',
        verbose_name='Categoría'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre del producto')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    costo_produccion = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Costo de producción (Bs)'
    )
    porcentaje_ganancia = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Porcentaje de ganancia'
    )
    precio_sugerido = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Precio sugerido (Bs)'
    )
    precio_venta = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='Precio de venta (Bs)'
    )
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    activo = models.BooleanField(default=True, verbose_name='Producto activo')

    class Meta:
        db_table = 'producto'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['id_producto']

    def __str__(self):
        return self.nombre

    def calcular_precio_sugerido(self):
        """precio_sugerido = costo_produccion x (1 + porcentaje_ganancia / 100)"""
        factor = Decimal('1') + (Decimal(self.porcentaje_ganancia) / Decimal('100'))
        return (Decimal(self.costo_produccion) * factor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.precio_sugerido = self.calcular_precio_sugerido()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'precio_sugerido' not in update_fields:
            kwargs['update_fields'] = list(update_fields) + ['precio_sugerido']
        super().save(*args, **kwargs)


class HistorialPrecioProducto(models.Model):
    """Registro de cada precio de venta vigente de un producto (tabla 'historial_precio_producto')."""
    id_historial = models.BigAutoField(primary_key=True)
    id_producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        db_column='id_producto',
        related_name='historial_precios',
        verbose_name='Producto'
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio (Bs)')
    fecha_inicio = models.DateTimeField(default=timezone.now, verbose_name='Vigente desde')

    class Meta:
        db_table = 'historial_precio_producto'
        verbose_name = 'Historial de precio'
        verbose_name_plural = 'Historial de precios'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.id_producto.nombre}: Bs {self.precio} ({self.fecha_inicio:%Y-%m-%d})'


class MateriaPrima(models.Model):
    """
    Insumo del inventario (harina, azúcar, etc.) — tabla 'materia_prima'.
    CU7: catálogo para registrar compras. Ver Database_Panaderia_Santiago.sql.
    """
    id_materia_prima = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    unidad_medida = models.CharField(max_length=20, verbose_name='Unidad de medida')
    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0'),
        verbose_name='Stock mínimo',
    )
    fecha_registro = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de registro',
    )
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        db_table = 'materia_prima'
        verbose_name = 'Materia prima'
        verbose_name_plural = 'Materias primas'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.unidad_medida})'


class InventarioMateriaPrima(models.Model):
    """Stock actual de un insumo (tabla 'inventario_materia_prima')."""
    id_inventario = models.BigAutoField(primary_key=True)
    id_materia_prima = models.OneToOneField(
        MateriaPrima,
        on_delete=models.PROTECT,
        db_column='id_materia_prima',
        related_name='inventario',
        verbose_name='Materia prima',
    )
    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('0'),
        verbose_name='Stock actual',
    )

    class Meta:
        db_table = 'inventario_materia_prima'
        verbose_name = 'Inventario de materia prima'
        verbose_name_plural = 'Inventarios de materia prima'

    def __str__(self):
        mp = self.id_materia_prima
        return f'{mp.nombre}: {self.stock_actual} {mp.unidad_medida}'


class HistorialPrecioMateriaPrima(models.Model):
    """Registro de cada precio de compra vigente de un insumo (tabla 'historial_precio_materia_prima')."""
    id_historial = models.BigAutoField(primary_key=True)
    id_materia_prima = models.ForeignKey(
        MateriaPrima,
        on_delete=models.PROTECT,
        db_column='id_materia_prima',
        related_name='historial_precios',
        verbose_name='Materia prima',
    )
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio (Bs)')
    fecha_inicio = models.DateTimeField(default=timezone.now, verbose_name='Vigente desde')

    class Meta:
        db_table = 'historial_precio_materia_prima'
        verbose_name = 'Historial de precio (materia prima)'
        verbose_name_plural = 'Historial de precios (materia prima)'
        ordering = ['-fecha_inicio', '-id_historial']

    def __str__(self):
        return f'{self.id_materia_prima.nombre}: Bs {self.precio} ({self.fecha_inicio:%Y-%m-%d})'


class TipoMovimientoMateriaPrima(models.TextChoices):
    ENTRADA = 'entrada', 'Entrada'
    SALIDA = 'salida', 'Salida'


class MovimientoMateriaPrima(models.Model):
    """Trazabilidad de entradas/salidas de insumos (tabla movimiento_materia_prima)."""
    id_movimiento = models.BigAutoField(primary_key=True)
    id_inventario = models.ForeignKey(
        InventarioMateriaPrima,
        on_delete=models.PROTECT,
        db_column='id_inventario',
        related_name='movimientos',
        verbose_name='Inventario',
    )
    id_compra = models.ForeignKey(
        'compras.Compra',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='id_compra',
        related_name='movimientos_materia',
        verbose_name='Compra',
    )
    fecha_hora = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora')
    tipo = models.CharField(
        max_length=10,
        choices=TipoMovimientoMateriaPrima.choices,
        verbose_name='Tipo de movimiento',
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Cantidad')

    class Meta:
        db_table = 'movimiento_materia_prima'
        verbose_name = 'Movimiento de materia prima'
        verbose_name_plural = 'Movimientos de materia prima'
        ordering = ['-fecha_hora', '-id_movimiento']

    def __str__(self):
        inv = self.id_inventario
        return f'{self.tipo} {self.cantidad} — {inv.id_materia_prima.nombre}'