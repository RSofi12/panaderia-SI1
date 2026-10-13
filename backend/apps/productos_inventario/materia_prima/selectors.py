
from decimal import Decimal

from django.db.models import DecimalField, F, Value
from django.db.models.functions import Coalesce

from apps.productos_inventario.materia_prima.models import MateriaPrima


def obtener_materias_primas_bajo_stock():
    """
    CU09: Obtiene materias primas activas con stock inferior al mínimo.

    Si una materia prima todavía no tiene registro de inventario,
    se considera stock actual 0, igual que en MateriaPrimaSerializer.
    """
    campo_stock = DecimalField(max_digits=10, decimal_places=3)

    return (
        MateriaPrima.objects
        .filter(activo=True)
        .annotate(
            stock_para_alerta=Coalesce(
                F('inventario__stock_actual'),
                Value(
                    Decimal('0.000'),
                    output_field=campo_stock,
                ),
                output_field=campo_stock,
            )
        )
        .filter(stock_para_alerta__lt=F('stock_minimo'))
        .select_related('inventario')
        .order_by('nombre')
    )
