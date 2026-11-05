"""
Modelos para la sub-app de Gastos e Inversiones (CU20).
Paquete: apps.compras.gastos
Ciclo: 4 (Gastos y Balance Económico)

Cumple con la tabla 'movimiento_economico' de Database_Panaderia_Santiago.sql.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class TipoMovimientoEconomico(models.TextChoices):
    GASTO = 'gasto', 'Gasto operativo'
    INVERSION = 'inversion', 'Inversión'


class MovimientoEconomico(models.Model):
    """
    Registro de gastos operativos e inversiones de la panadería (CU20).
    Permite relacionar egresos no asociados a materia prima (alquiler, luz, agua,
    mantenimiento de hornos, equipos) para los reportes de resultados económicos (CU25).
    """
    id_movimiento = models.BigAutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='movimientos_economicos',
        verbose_name='Registrado por',
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoMovimientoEconomico.choices,
        verbose_name='Tipo de movimiento',
    )
    concepto = models.CharField(
        max_length=100,
        verbose_name='Concepto',
        help_text='Ej: Alquiler de local, Energía eléctrica, Mantenimiento de amasadora',
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción / Observaciones',
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Monto (Bs)',
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y hora',
    )

    class Meta:
        db_table = 'movimiento_economico'
        verbose_name = 'Movimiento económico'
        verbose_name_plural = 'Movimientos económicos'
        ordering = ['-fecha_hora', '-id_movimiento']

    def __str__(self):
        return f'{self.tipo.upper()}: {self.concepto} — Bs {self.monto}'
