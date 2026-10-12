from rest_framework import serializers

from apps.productos_inventario.materia_prima.models import MateriaPrima


class MateriaPrimaSerializer(serializers.ModelSerializer):
    stock_actual = serializers.SerializerMethodField()
    precio_ultima_compra = serializers.SerializerMethodField()

    class Meta:
        model = MateriaPrima
        fields = [
            'id_materia_prima',
            'nombre',
            'unidad_medida',
            'stock_minimo',
            'stock_actual',
            'precio_ultima_compra',
            'fecha_registro',
            'activo',
        ]

    # Los SerializerMethodField no pasan por COERCE_DECIMAL_TO_STRING: si se
    # devolviera el Decimal, el JSON llevaría un número y no texto como el
    # resto de los DecimalField de la API.
    def get_stock_actual(self, obj):
        inventario = getattr(obj, 'inventario', None)
        if inventario is None:
            return '0.000'
        return str(inventario.stock_actual)

    def get_precio_ultima_compra(self, obj):
        ultimo = obj.historial_precios.first()
        return str(ultimo.precio) if ultimo else None
