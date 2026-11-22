from rest_framework import serializers

from apps.comercializacion.ventas.models import MetodoPago
from apps.reportes.models import PeriodoReporte


class ReporteVentasConsultaSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    metodo_pago = serializers.ChoiceField(
        choices=MetodoPago.choices,
        required=False,
        allow_blank=True,
    )


class ProductoVendidoSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


class ReporteVentasSerializer(serializers.Serializer):
    desde = serializers.DateField()
    hasta = serializers.DateField()
    cantidad = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    efectivo = serializers.DecimalField(max_digits=10, decimal_places=2)
    tarjeta = serializers.DecimalField(max_digits=10, decimal_places=2)
    productos = ProductoVendidoSerializer(many=True)


class CierreReporteConsultaSerializer(ReporteVentasConsultaSerializer):
    periodo = serializers.ChoiceField(choices=PeriodoReporte.choices)


class CierreReporteVentasSerializer(ReporteVentasSerializer):
    id_cierre = serializers.IntegerField()
    periodo = serializers.ChoiceField(choices=PeriodoReporte.choices)
    metodo_pago = serializers.CharField(allow_null=True)
    fecha_generacion = serializers.DateTimeField()
    generado_por = serializers.CharField()


# --- CU24: Generar reporte de compras y gastos ---

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

