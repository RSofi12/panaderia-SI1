"""
Modelos para la sub-app de Gastos e Inversiones (CU20).
Paquete: apps.compras.gastos
Ciclo: 4 (Gastos y Balance Económico)

Cumple con la tabla 'movimiento_economico' de Database_Panaderia_Santiago.sql.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class TipoMovimientoEconomico(models.TextChoices):
    GASTO = 'gasto', 'Gasto operativo'
    INVERSION = 'inversion', 'Inversión'


class CategoriaMovimientoEconomico(models.TextChoices):
    """Agrupa los egresos para los reportes económicos (CU24 y CU25)."""
    ALQUILER = 'alquiler', 'Alquiler'
    SERVICIOS = 'servicios', 'Servicios básicos'
    MANTENIMIENTO = 'mantenimiento', 'Mantenimiento'
    EQUIPOS = 'equipos', 'Equipos y herramientas'
    OTROS = 'otros', 'Otros'


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
    categoria = models.CharField(
        max_length=20,
        choices=CategoriaMovimientoEconomico.choices,
        default=CategoriaMovimientoEconomico.OTROS,
        verbose_name='Categoría',
        help_text='Agrupa el egreso en los reportes: alquiler, servicios, mantenimiento, equipos u otros.',
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
        verbose_name='Monto (Bs)',
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y hora',
    )
    anulado = models.BooleanField(
        default=False,
        verbose_name='Anulado',
        help_text='Un movimiento anulado se conserva por auditoría pero no cuenta en los reportes.',
    )

    class Meta:
        db_table = 'movimiento_economico'
        verbose_name = 'Movimiento económico'
        verbose_name_plural = 'Movimientos económicos'
        ordering = ['-fecha_hora', '-id_movimiento']
        indexes = [
            models.Index(fields=['fecha_hora'], name='mov_economico_fecha_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(monto__gt=0),
                name='mov_economico_monto_positivo',
            ),
            models.CheckConstraint(
                condition=models.Q(tipo__in=TipoMovimientoEconomico.values),
                name='mov_economico_tipo_valido',
            ),
            models.CheckConstraint(
                condition=models.Q(categoria__in=CategoriaMovimientoEconomico.values),
                name='mov_economico_categoria_valida',
            ),
        ]

    def __str__(self):
        return f'{self.tipo.upper()}: {self.concepto} — Bs {self.monto}'
