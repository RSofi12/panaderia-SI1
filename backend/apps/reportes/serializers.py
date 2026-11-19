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
