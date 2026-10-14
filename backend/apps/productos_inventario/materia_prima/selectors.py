from decimal import Decimal

from django.db.models import DecimalField, F, Value
from django.db.models.functions import Coalesce

from apps.productos_inventario.materia_prima.models import MateriaPrima


def filtrar_materias_primas_bajo_minimo(materias):
    """
    CU08/CU09: Filtra stock menor o igual al mínimo sin alterar otros filtros.

    Si una materia prima todavía no tiene registro de inventario,
    se considera stock actual 0, igual que en los serializadores de stock.
    """
    campo_stock = DecimalField(max_digits=10, decimal_places=3)

    return (
        materias.annotate(
            stock_para_alerta=Coalesce(
                F('inventario__stock_actual'),
                Value(
                    Decimal('0.000'),
                    output_field=campo_stock,
                ),
                output_field=campo_stock,
            )
        )
        .filter(stock_para_alerta__lte=F('stock_minimo'))
    )


def obtener_materias_primas_bajo_stock():
    """CU09: Obtiene materias primas activas que alcanzaron el stock mínimo."""
    return (
        filtrar_materias_primas_bajo_minimo(
            MateriaPrima.objects.filter(activo=True)
        )
        .select_related('inventario')
        .order_by('nombre')
    )
