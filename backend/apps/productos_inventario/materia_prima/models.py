from decimal import Decimal

from django.db import models
from django.utils import timezone


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
        'compra_materia_prima.Compra',
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
