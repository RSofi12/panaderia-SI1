"""
Modelos para la sub-app de Producción (Elaboración / Fabricación de Pan).

Casos de Uso abordados:
  - CU10: Registrar producción diaria
  - CU11: Consultar historial de producción

Cumple con las tablas 'produccion' y 'detalle_produccion' de Database_Panaderia_Santiago.sql.
"""
from decimal import Decimal

from django.db import models
from django.utils import timezone


class JornadaProduccion(models.TextChoices):
    MANANA = 'Mañana', 'Mañana'
    TARDE = 'Tarde', 'Tarde'
    NOCHE = 'Noche', 'Noche'
    UNICA = 'unica', 'Jornada Única'


class Produccion(models.Model):
    """
    Cabecera de la jornada / lote de producción diaria (tabla 'produccion').
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
    Línea de pan producido por tipo de producto (tabla 'detalle_produccion').
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
