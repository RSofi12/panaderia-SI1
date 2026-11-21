"""
Reporte de Resultados Económicos y Balance Operativo (CU25).
Paquete: apps.reportes
Ciclo: 4 (Control Financiero y Toma de Decisiones)

Servicio analítico de solo lectura (OLAP) que consolida:
  1. Ingresos por Ventas (CU13)
  2. Costos directos de Aprovisionamiento/Compras (CU07)
  3. Costos de Bajas / Mermas de vitrina (CU18)
  4. Gastos operativos e Inversiones (CU20)

Calcula:
  - Margen Bruto = Ingresos - (Compras + Mermas)
  - Utilidad Operativa = Margen Bruto - Gastos Operativos
  - Resultado Neto = Utilidad Operativa - Inversiones
  - Márgenes porcentuales de rentabilidad sobre ingresos
"""
from datetime import date
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Count, DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce

from apps.comercializacion.ventas.models import MetodoPago, Venta
from apps.compras.compra_materia_prima.models import Compra
from apps.compras.gastos.models import MovimientoEconomico, TipoMovimientoEconomico
from apps.productos_inventario.productos_terminados.models import NotaPerdidaProducto

CERO = Decimal('0.00')


def reporte_resultados_economicos(*, desde: date, hasta: date) -> dict[str, Any]:
    """
    Genera el balance de resultados económicos para el rango de fechas [desde, hasta].
    """
    if desde > hasta:
        raise ValidationError({'hasta': 'La fecha final no puede ser anterior a la inicial.'})

    # =========================================================================
    # 1. INGRESOS POR VENTAS (CU13)
    # =========================================================================
    ventas_qs = Venta.objects.filter(
        fecha_hora__date__gte=desde,
        fecha_hora__date__lte=hasta,
    )
    ventas_agg = ventas_qs.aggregate(
        cantidad=Count('id_venta'),
        suma_total=Coalesce(Sum('total'), CERO),
        suma_efectivo=Coalesce(Sum('total', filter=Q(metodo_pago=MetodoPago.EFECTIVO)), CERO),
        suma_tarjeta=Coalesce(Sum('total', filter=Q(metodo_pago=MetodoPago.STRIPE)), CERO),
    )
    total_ingresos = Decimal(ventas_agg['suma_total'])
    total_efectivo = Decimal(ventas_agg['suma_efectivo'])
    total_tarjeta = Decimal(ventas_agg['suma_tarjeta'])
    cantidad_ventas = int(ventas_agg['cantidad'])

    # =========================================================================
    # 2. COSTOS DIRECTOS: COMPRAS DE MATERIA PRIMA (CU07)
    # =========================================================================
    compras_qs = Compra.objects.filter(
        fecha_hora__date__gte=desde,
        fecha_hora__date__lte=hasta,
    )
    compras_agg = compras_qs.aggregate(
        cantidad=Count('id_compra'),
        suma_total=Coalesce(Sum('total'), CERO),
    )
    total_compras = Decimal(compras_agg['suma_total'])
    cantidad_compras = int(compras_agg['cantidad'])

    # =========================================================================
    # 3. COSTOS POR MERMAS / PÉRDIDAS DE PAN TERMINADO (CU18)
    # =========================================================================
    mermas_qs = NotaPerdidaProducto.objects.filter(
        fecha_salida__date__gte=desde,
        fecha_salida__date__lte=hasta,
    )
    mermas_agg = mermas_qs.aggregate(
        cantidad_unidades=Coalesce(Sum('cantidad'), 0),
        costo_total=Coalesce(
            Sum(F('cantidad') * F('costo_unitario'), output_field=DecimalField(max_digits=12, decimal_places=2)),
            CERO,
        ),
    )
    total_mermas = Decimal(mermas_agg['costo_total'])
    unidades_mermas = int(mermas_agg['cantidad_unidades'])

    # =========================================================================
    # 4. GASTOS OPERATIVOS E INVERSIONES (CU20)
    # =========================================================================
    movimientos_qs = MovimientoEconomico.objects.filter(
        anulado=False,
        fecha_hora__date__gte=desde,
        fecha_hora__date__lte=hasta,
    )

    # Gastos operativos
    gastos_qs = movimientos_qs.filter(tipo=TipoMovimientoEconomico.GASTO)
    gastos_agg = gastos_qs.aggregate(
        cantidad=Count('id_movimiento'),
        total=Coalesce(Sum('monto'), CERO),
    )
    total_gastos = Decimal(gastos_agg['total'])
    cantidad_gastos = int(gastos_agg['cantidad'])

    # Desglose de gastos por categoría
    desglose_gastos = list(
        gastos_qs.values('categoria')
        .annotate(
            total_categoria=Coalesce(Sum('monto'), CERO),
            cantidad=Count('id_movimiento'),
        )
        .order_by('-total_categoria')
    )

    # Inversiones de capital
    inversiones_qs = movimientos_qs.filter(tipo=TipoMovimientoEconomico.INVERSION)
    inversiones_agg = inversiones_qs.aggregate(
        cantidad=Count('id_movimiento'),
        total=Coalesce(Sum('monto'), CERO),
    )
    total_inversiones = Decimal(inversiones_agg['total'])
    cantidad_inversiones = int(inversiones_agg['cantidad'])

    desglose_inversiones = list(
        inversiones_qs.values('categoria')
        .annotate(
            total_categoria=Coalesce(Sum('monto'), CERO),
            cantidad=Count('id_movimiento'),
        )
        .order_by('-total_categoria')
    )

    # =========================================================================
    # 5. CÁLCULO DE MÁRGENES Y ESTADO DE RESULTADOS
    # =========================================================================
    total_costos_directos = total_compras + total_mermas
    utilidad_bruta = total_ingresos - total_costos_directos

    total_egresos_operativos = total_costos_directos + total_gastos
    utilidad_operativa = total_ingresos - total_egresos_operativos

    total_egresos_totales = total_egresos_operativos + total_inversiones
    utilidad_neta = utilidad_operativa - total_inversiones

    if total_ingresos > CERO:
        margen_bruto_pct = round((utilidad_bruta / total_ingresos) * Decimal('100.00'), 2)
        margen_operativo_pct = round((utilidad_operativa / total_ingresos) * Decimal('100.00'), 2)
        margen_neto_pct = round((utilidad_neta / total_ingresos) * Decimal('100.00'), 2)
    else:
        margen_bruto_pct = CERO
        margen_operativo_pct = CERO
        margen_neto_pct = CERO

    # Estructura del estado de resultados formal
    estado_resultados = [
        {
            'concepto': 'Ingresos por ventas de productos',
            'monto': total_ingresos,
            'tipo': 'ingreso',
            'porcentaje_ingresos': Decimal('100.00') if total_ingresos > CERO else CERO,
        },
        {
            'concepto': '(-) Costo de materias primas compradas',
            'monto': total_compras,
            'tipo': 'costo_directo',
            'porcentaje_ingresos': round((total_compras / total_ingresos * 100), 2) if total_ingresos > CERO else CERO,
        },
        {
            'concepto': '(-) Costo de mermas y pérdidas de pan',
            'monto': total_mermas,
            'tipo': 'costo_directo',
            'porcentaje_ingresos': round((total_mermas / total_ingresos * 100), 2) if total_ingresos > CERO else CERO,
        },
        {
            'concepto': '(=) Margen / Utilidad Bruta',
            'monto': utilidad_bruta,
            'tipo': 'subtotal',
            'porcentaje_ingresos': margen_bruto_pct,
        },
        {
            'concepto': '(-) Gastos operativos de administración y venta',
            'monto': total_gastos,
            'tipo': 'gasto_operativo',
            'porcentaje_ingresos': round((total_gastos / total_ingresos * 100), 2) if total_ingresos > CERO else CERO,
        },
        {
            'concepto': '(=) Utilidad Operativa (EBITDA)',
            'monto': utilidad_operativa,
            'tipo': 'subtotal',
            'porcentaje_ingresos': margen_operativo_pct,
        },
        {
            'concepto': '(-) Inversiones en equipamiento e infraestructura',
            'monto': total_inversiones,
            'tipo': 'inversion',
            'porcentaje_ingresos': round((total_inversiones / total_ingresos * 100), 2) if total_ingresos > CERO else CERO,
        },
        {
            'concepto': '(=) Resultado Económico Neto Final',
            'monto': utilidad_neta,
            'tipo': 'total_neto',
            'porcentaje_ingresos': margen_neto_pct,
        },
    ]

    tiene_movimientos = (
        cantidad_ventas > 0
        or cantidad_compras > 0
        or unidades_mermas > 0
        or cantidad_gastos > 0
        or cantidad_inversiones > 0
    )

    return {
        'desde': desde,
        'hasta': hasta,
        'tiene_movimientos': tiene_movimientos,
        # Ingresos
        'ingresos': {
            'total': total_ingresos,
            'efectivo': total_efectivo,
            'tarjeta': total_tarjeta,
            'cantidad_transacciones': cantidad_ventas,
        },
        # Costos y Egresos
        'costos': {
            'compras_materia_prima': total_compras,
            'cantidad_compras': cantidad_compras,
            'mermas_perdidas': total_mermas,
            'unidades_mermas': unidades_mermas,
            'total_costos_directos': total_costos_directos,
        },
        'gastos_operativos': {
            'total': total_gastos,
            'cantidad': cantidad_gastos,
            'desglose': [
                {
                    'categoria': fila['categoria'],
                    'total': Decimal(fila['total_categoria']),
                    'cantidad': fila['cantidad'],
                }
                for fila in desglose_gastos
            ],
        },
        'inversiones': {
            'total': total_inversiones,
            'cantidad': cantidad_inversiones,
            'desglose': [
                {
                    'categoria': fila['categoria'],
                    'total': Decimal(fila['total_categoria']),
                    'cantidad': fila['cantidad'],
                }
                for fila in desglose_inversiones
            ],
        },
        # Totales agregados y márgenes
        'resumen_financiero': {
            'total_ingresos': total_ingresos,
            'total_egresos_operativos': total_egresos_operativos,
            'total_egresos_totales': total_egresos_totales,
            'utilidad_bruta': utilidad_bruta,
            'utilidad_operativa': utilidad_operativa,
            'utilidad_neta': utilidad_neta,
            'margen_bruto_pct': margen_bruto_pct,
            'margen_operativo_pct': margen_operativo_pct,
            'margen_neto_pct': margen_neto_pct,
        },
        'estado_resultados': estado_resultados,
    }
