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
