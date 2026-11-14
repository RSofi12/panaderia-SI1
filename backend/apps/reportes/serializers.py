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
