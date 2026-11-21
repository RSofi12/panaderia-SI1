from rest_framework import serializers

from apps.comercializacion.ventas.models import MetodoPago


class ReporteVentasConsultaSerializer(serializers.Serializer):
    """Parámetros de filtro para el reporte dinámico de ventas (CU21)."""
    desde = serializers.DateField(required=True)
    hasta = serializers.DateField(required=True)
    metodo_pago = serializers.ChoiceField(
        choices=MetodoPago.choices,
        required=False,
        allow_blank=True,
    )
    columnas = serializers.CharField(required=False, allow_blank=True)


class ProductoVendidoSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


class VentaItemReporteSerializer(serializers.Serializer):
    id_venta = serializers.IntegerField()
    numero_comprobante = serializers.IntegerField()
    fecha = serializers.CharField()
    fecha_hora = serializers.CharField()
    metodo_pago = serializers.CharField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    cajero = serializers.CharField()


class InterpretarComandoVozEntradaSerializer(serializers.Serializer):
    """Entrada para POST /api/reportes/voz/interpretar/ (comando hablado o escrito)."""

    texto = serializers.CharField(max_length=500, trim_whitespace=True)
    cu_actual = serializers.RegexField(
        regex=r'^CU2[1-5]$',
        required=False,
        allow_blank=True,
        allow_null=True,
    )


class FiltrosComandoVozSerializer(serializers.Serializer):
    periodo = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    desde = serializers.DateField(required=False, allow_null=True)
    hasta = serializers.DateField(required=False, allow_null=True)
    metodo_pago = serializers.CharField(required=False, allow_blank=True)
    columnas = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
    )


class InterpretarComandoVozSalidaSerializer(serializers.Serializer):
    caso_uso = serializers.CharField()
    formato = serializers.CharField()
    accion = serializers.CharField()
    requiere_seleccion_formato = serializers.BooleanField()
    filtros = FiltrosComandoVozSerializer()
    respuesta_voz = serializers.CharField()
    modulo_disponible = serializers.BooleanField()
    motor = serializers.CharField()


class ReporteVentasSerializer(serializers.Serializer):
    """Esquema de salida para el reporte de ventas del período."""
    desde = serializers.DateField()
    hasta = serializers.DateField()
    cantidad = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    efectivo = serializers.DecimalField(max_digits=10, decimal_places=2)
    tarjeta = serializers.DecimalField(max_digits=10, decimal_places=2)
    productos = ProductoVendidoSerializer(many=True)
    ventas = VentaItemReporteSerializer(many=True, required=False)


# =============================================================================
# SERIALIZERS PARA CU25: RESULTADOS ECONÓMICOS
# =============================================================================

class ReporteResultadosEconomicosConsultaSerializer(serializers.Serializer):
    """Parámetros de consulta para el reporte de resultados económicos (CU25)."""
    desde = serializers.DateField(required=True)
    hasta = serializers.DateField(required=True)


class DesgloseCategoriaMontoSerializer(serializers.Serializer):
    categoria = serializers.CharField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad = serializers.IntegerField()


class EstadoResultadosFilaSerializer(serializers.Serializer):
    concepto = serializers.CharField()
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    tipo = serializers.CharField()
    porcentaje_ingresos = serializers.DecimalField(max_digits=6, decimal_places=2)


class ResumenFinancieroSerializer(serializers.Serializer):
    total_ingresos = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_egresos_operativos = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_egresos_totales = serializers.DecimalField(max_digits=12, decimal_places=2)
    utilidad_bruta = serializers.DecimalField(max_digits=12, decimal_places=2)
    utilidad_operativa = serializers.DecimalField(max_digits=12, decimal_places=2)
    utilidad_neta = serializers.DecimalField(max_digits=12, decimal_places=2)
    margen_bruto_pct = serializers.DecimalField(max_digits=6, decimal_places=2)
    margen_operativo_pct = serializers.DecimalField(max_digits=6, decimal_places=2)
    margen_neto_pct = serializers.DecimalField(max_digits=6, decimal_places=2)


class IngresosReporteEconomicoSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    efectivo = serializers.DecimalField(max_digits=12, decimal_places=2)
    tarjeta = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad_transacciones = serializers.IntegerField()


class CostosReporteEconomicoSerializer(serializers.Serializer):
    compras_materia_prima = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad_compras = serializers.IntegerField()
    mermas_perdidas = serializers.DecimalField(max_digits=12, decimal_places=2)
    unidades_mermas = serializers.IntegerField()
    total_costos_directos = serializers.DecimalField(max_digits=12, decimal_places=2)


class GastosOperativosReporteSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad = serializers.IntegerField()
    desglose = DesgloseCategoriaMontoSerializer(many=True)


class InversionesReporteSerializer(serializers.Serializer):
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    cantidad = serializers.IntegerField()
    desglose = DesgloseCategoriaMontoSerializer(many=True)


class ReporteResultadosEconomicosSerializer(serializers.Serializer):
    """Esquema de salida completo para el reporte de resultados económicos (CU25)."""
    desde = serializers.DateField()
    hasta = serializers.DateField()
    tiene_movimientos = serializers.BooleanField()
    ingresos = IngresosReporteEconomicoSerializer()
    costos = CostosReporteEconomicoSerializer()
    gastos_operativos = GastosOperativosReporteSerializer()
    inversiones = InversionesReporteSerializer()
    resumen_financiero = ResumenFinancieroSerializer()
    estado_resultados = EstadoResultadosFilaSerializer(many=True)

