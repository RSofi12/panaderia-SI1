from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.comercializacion.ventas.models import MetodoPago


class PeriodoReporte(models.TextChoices):
    """El periodo solo etiqueta el cierre. El cálculo siempre usa desde y hasta."""

    DIA = 'dia', 'Día'
    SEMANA = 'semana', 'Semana'
    MES = 'mes', 'Mes'


class CierreReporteVentas(models.Model):
    """
    CU21 estático. Copia de los totales en el momento del cierre.

    El reporte dinámico no usa esta tabla: vuelve a leer venta.
    Esta fila no se actualiza si después entra otra venta.
    """

    id_cierre = models.BigAutoField(primary_key=True)
    desde = models.DateField(verbose_name='Desde')
    hasta = models.DateField(verbose_name='Hasta')
    periodo = models.CharField(max_length=10, choices=PeriodoReporte.choices, verbose_name='Periodo')
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        blank=True,
        null=True,
        verbose_name='Método de pago',
        help_text='Vacío cuando el cierre incluye efectivo y tarjeta.',
    )
    cantidad = models.PositiveIntegerField(verbose_name='Cantidad de ventas')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total (Bs)')
    efectivo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Efectivo (Bs)')
    tarjeta = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Tarjeta (Bs)')
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        related_name='cierres_reporte_ventas',
        verbose_name='Generado por',
    )
    fecha_generacion = models.DateTimeField(default=timezone.now, verbose_name='Fecha del cierre')

    class Meta:
        db_table = 'cierre_reporte_ventas'
        verbose_name = 'Cierre de reporte de ventas'
        verbose_name_plural = 'Cierres de reporte de ventas'
        ordering = ['-fecha_generacion', '-id_cierre']
        constraints = [
            models.CheckConstraint(
                condition=Q(desde__lte=models.F('hasta')),
                name='cierre_reporte_desde_antes_de_hasta',
            ),
            models.CheckConstraint(
                condition=Q(periodo__in=[PeriodoReporte.DIA, PeriodoReporte.SEMANA, PeriodoReporte.MES]),
                name='cierre_reporte_periodo_valido',
            ),
            models.CheckConstraint(
                condition=Q(metodo_pago__isnull=True) | Q(metodo_pago__in=[MetodoPago.EFECTIVO, MetodoPago.STRIPE]),
                name='cierre_reporte_metodo_pago_valido',
            ),
        ]

    def __str__(self):
        return f'Cierre {self.desde} a {self.hasta} — Bs {self.total}'


class LineaCierreReporteVentas(models.Model):
    """Producto vendido tal como se llamaba al guardar el cierre."""

    id_linea = models.BigAutoField(primary_key=True)
    id_cierre = models.ForeignKey(
        CierreReporteVentas,
        on_delete=models.CASCADE,
        db_column='id_cierre',
        related_name='lineas',
        verbose_name='Cierre',
    )
    nombre_producto = models.CharField(max_length=100, verbose_name='Producto')
    cantidad = models.PositiveIntegerField(verbose_name='Unidades')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal (Bs)')

    class Meta:
        db_table = 'linea_cierre_reporte_ventas'
        verbose_name = 'Línea de cierre de ventas'
        verbose_name_plural = 'Líneas de cierre de ventas'
        ordering = ['-subtotal', 'nombre_producto']

    def __str__(self):
        return f'{self.nombre_producto}: {self.cantidad}'
