from decimal import Decimal

from rest_framework import serializers

from apps.comercializacion.ventas.models import MetodoPago
from apps.productos_inventario.produccion.models import JornadaProduccion
from apps.reportes.choices import PeriodoReporte


# ==============================================================================
# CU21: Reporte de ventas y Asistente de voz
# ==============================================================================

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
    jornada = serializers.CharField(required=False, allow_blank=True)
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


class AnalizarVozEntradaSerializer(serializers.Serializer):
    texto = serializers.CharField(max_length=800, trim_whitespace=True)
    cu_actual = serializers.RegexField(
        regex=r'^CU2[1-5]$',
        required=False,
        allow_blank=True,
        allow_null=True,
    )


class AnalizarVozSalidaSerializer(serializers.Serializer):
    consulta = serializers.CharField()
    tema = serializers.CharField()
    caso_uso = serializers.CharField()
    desde = serializers.DateField()
    hasta = serializers.DateField()
    analisis = serializers.CharField()
    motor = serializers.CharField()
    exportar_ventas = serializers.BooleanField()
    exportar_produccion = serializers.BooleanField()
    respuesta_voz = serializers.CharField()
    comando = InterpretarComandoVozSalidaSerializer()


class AnalizarVozPdfEntradaSerializer(serializers.Serializer):
    consulta = serializers.CharField(max_length=800, trim_whitespace=True)
    tema = serializers.CharField(max_length=40)
    desde = serializers.DateField()
    hasta = serializers.DateField()
    analisis = serializers.CharField(max_length=50000, trim_whitespace=True)
    motor = serializers.CharField(max_length=20, required=False, default='local')


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


# ==============================================================================
# CU22: Reporte de producción
# ==============================================================================

class ReporteProduccionConsultaSerializer(serializers.Serializer):
    """Parámetros de filtro para el reporte dinámico de producción (CU22)."""

    desde = serializers.DateField(required=True)
    hasta = serializers.DateField(required=True)
    jornada = serializers.ChoiceField(
        choices=JornadaProduccion.choices,
        required=False,
        allow_blank=True,
    )
    columnas = serializers.CharField(required=False, allow_blank=True)


class ProductoProducidoSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    vendidas = serializers.IntegerField()
    mermadas = serializers.IntegerField(default=0)
    diferencia = serializers.IntegerField()
    costo = serializers.DecimalField(max_digits=12, decimal_places=2)


class MermaProduccionItemSerializer(serializers.Serializer):
    id_nota_perdida = serializers.IntegerField()
    fecha = serializers.CharField()
    producto = serializers.CharField()
    cantidad = serializers.IntegerField()
    costo_unitario = serializers.DecimalField(max_digits=12, decimal_places=2)
    costo_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    motivo = serializers.CharField()
    observaciones = serializers.CharField(allow_blank=True, default='')
    responsable = serializers.CharField()


class LoteProduccionItemSerializer(serializers.Serializer):
    id_produccion = serializers.IntegerField()
    fecha = serializers.CharField()
    jornada = serializers.CharField()
    jornada_codigo = serializers.CharField()
    responsable = serializers.CharField()
    unidades = serializers.IntegerField()
    variedades = serializers.IntegerField()
    costo = serializers.DecimalField(max_digits=12, decimal_places=2)


class ReporteProduccionSerializer(serializers.Serializer):
    """Esquema de salida para el reporte de producción del período."""

    desde = serializers.DateField()
    hasta = serializers.DateField()
    cantidad = serializers.IntegerField()
    unidades = serializers.IntegerField()
    unidades_vendidas = serializers.IntegerField()
    unidades_mermadas = serializers.IntegerField(default=0)
    costo_mermas = serializers.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    diferencia = serializers.IntegerField()
    costo = serializers.DecimalField(max_digits=12, decimal_places=2)
    manana = serializers.IntegerField()
    tarde = serializers.IntegerField()
    noche = serializers.IntegerField()
    lotes = LoteProduccionItemSerializer(many=True)
    productos = ProductoProducidoSerializer(many=True)
    mermas = MermaProduccionItemSerializer(many=True, required=False)


class CierreReporteConsultaSerializer(ReporteVentasConsultaSerializer):
    periodo = serializers.ChoiceField(choices=PeriodoReporte.choices)


class CierreReporteVentasSerializer(ReporteVentasSerializer):
    id_cierre = serializers.IntegerField()
    periodo = serializers.ChoiceField(choices=PeriodoReporte.choices)
    metodo_pago = serializers.CharField(allow_null=True)
    fecha_generacion = serializers.DateTimeField()
    generado_por = serializers.CharField()


# ==============================================================================
# CU23: Reporte de existencias
# ==============================================================================

class ReporteExistenciasConsultaSerializer(serializers.Serializer):
    """Filtros validados del reporte de existencias (CU23)."""

    tipo = serializers.ChoiceField(
        choices=('todos', 'materia_prima', 'producto_terminado'),
        default='todos',
    )
    q = serializers.CharField(
        max_length=100, allow_blank=True, trim_whitespace=True, default='',
    )
    estado = serializers.ChoiceField(
        choices=('todos', 'normal', 'bajo_stock', 'sin_inventario'),
        default='todos',
    )


class ExistenciaItemReporteSerializer(serializers.Serializer):
    """Fila de catálogo; una cantidad nula indica que falta su inventario."""

    id = serializers.IntegerField()
    nombre = serializers.CharField()
    tipo = serializers.ChoiceField(choices=('materia_prima', 'producto_terminado'))
    stock_actual = serializers.DecimalField(
        max_digits=13, decimal_places=3, allow_null=True, coerce_to_string=True,
    )
    stock_minimo = serializers.DecimalField(
        max_digits=13, decimal_places=3, coerce_to_string=True,
    )
    origen_minimo = serializers.ChoiceField(choices=('catalogo', 'referencial_global'))
    unidad_medida = serializers.CharField()
    estado = serializers.ChoiceField(choices=('normal', 'bajo_stock', 'sin_inventario'))
    activo = serializers.BooleanField()


class ResumenExistenciasReporteSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    materias_primas = serializers.IntegerField()
    productos_terminados = serializers.IntegerField()
    bajo_stock = serializers.IntegerField()
    sin_inventario = serializers.IntegerField()


class ReporteExistenciasSerializer(serializers.Serializer):
    umbral_productos_terminados = serializers.DecimalField(
        max_digits=13, decimal_places=3, coerce_to_string=True,
    )
    resumen = ResumenExistenciasReporteSerializer()
    resultados = ExistenciaItemReporteSerializer(many=True)


# ==============================================================================
# CU24: Generar reporte de compras y gastos
# ==============================================================================

class ReporteComprasConsultaSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    id_proveedor = serializers.IntegerField(required=False, allow_null=True)
    id_materia_prima = serializers.IntegerField(required=False, allow_null=True)


class ProveedorComprasSerializer(serializers.Serializer):
    id_proveedor = serializers.IntegerField()
    nombre = serializers.CharField()
    cantidad_compras = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)


class InsumoCompradoSerializer(serializers.Serializer):
    id_materia_prima = serializers.IntegerField(required=False)
    nombre = serializers.CharField()
    unidad_medida = serializers.CharField(allow_blank=True, default='')
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=3)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


class ReporteComprasSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    cantidad = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    proveedores = ProveedorComprasSerializer(many=True)
    insumos = InsumoCompradoSerializer(many=True)


class CierreReporteComprasConsultaSerializer(ReporteComprasConsultaSerializer):
    periodo = serializers.ChoiceField(choices=PeriodoReporte.choices)


class CierreReporteComprasSerializer(serializers.Serializer):
    id_cierre = serializers.IntegerField()
    desde = serializers.DateField()
    hasta = serializers.DateField()
    periodo = serializers.ChoiceField(choices=PeriodoReporte.choices)
    proveedor = serializers.CharField(allow_null=True)
    cantidad = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    fecha_generacion = serializers.DateTimeField()
    generado_por = serializers.CharField()
    insumos = InsumoCompradoSerializer(many=True)


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
