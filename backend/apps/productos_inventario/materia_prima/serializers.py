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


class MateriaPrimaStockSerializer(serializers.ModelSerializer):
    """Solo lectura: stock de materia prima con su estado (CU8)."""
    stock_actual = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField()

    class Meta:
        model = MateriaPrima
        fields = [
            'id_materia_prima',
            'nombre',
            'unidad_medida',
            'stock_actual',
            'stock_minimo',
            'estado',
            'activo',
        ]
        read_only_fields = fields

    def _stock(self, obj):
        inventario = getattr(obj, 'inventario', None)
        return inventario.stock_actual if inventario else 0

    def get_stock_actual(self, obj):
        return self._stock(obj)

    def get_estado(self, obj):
        stock = self._stock(obj)
        if stock <= 0:
            return 'agotado'
        if stock <= obj.stock_minimo:
            return 'bajo_minimo'
        return 'normal'
