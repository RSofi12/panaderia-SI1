"""
Serializadores para Existencias de Productos Terminados (CU12) y Mermas (CU18).
Autor de la implementación CU12: Roberto (Equipo Panadería Santiago).
"""
from decimal import Decimal
from rest_framework import serializers

from .models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
)


class InventarioProductoTerminadoSerializer(serializers.ModelSerializer):
    """
    Serializador completo para el listado de existencias de productos terminados (CU12).
    Añade información comercial del producto y cálculo en tiempo real de valorización y estado.
    """
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='id_producto.descripcion', read_only=True)
    categoria_id = serializers.IntegerField(source='id_producto.id_categoria.id_categoria', read_only=True)
    categoria_nombre = serializers.CharField(
        source='id_producto.id_categoria.nombre', default='Sin categoría', read_only=True
    )
    precio_venta = serializers.DecimalField(
        source='id_producto.precio_venta', max_digits=10, decimal_places=2, read_only=True
    )
    costo_produccion = serializers.DecimalField(
        source='id_producto.costo_produccion', max_digits=10, decimal_places=2, read_only=True
    )
    porcentaje_ganancia = serializers.DecimalField(
        source='id_producto.porcentaje_ganancia', max_digits=5, decimal_places=2, read_only=True
    )
    activo = serializers.BooleanField(source='id_producto.activo', read_only=True)

    # Campos calculados dinámicos
    valor_total_stock = serializers.SerializerMethodField()
    estado_stock = serializers.SerializerMethodField()

    class Meta:
        model = InventarioProductoTerminado
        fields = [
            'id_inventario',
            'id_producto',
            'producto_nombre',
            'producto_descripcion',
            'categoria_id',
            'categoria_nombre',
            'precio_venta',
            'costo_produccion',
            'porcentaje_ganancia',
            'stock_actual',
            'activo',
            'valor_total_stock',
            'estado_stock',
        ]

    def get_valor_total_stock(self, obj) -> str:
        """Valor monetario en Bs. del stock actual disponible (stock * precio_venta)."""
        precio = getattr(obj.id_producto, 'precio_venta', Decimal('0.00')) or Decimal('0.00')
        stock = Decimal(obj.stock_actual or 0)
        return str((stock * precio).quantize(Decimal('0.01')))

    def get_estado_stock(self, obj) -> str:
        """
        Clasificación semántica del nivel de stock para badges visuales en la interfaz:
          - 'agotado': stock == 0
          - 'critico': 0 < stock <= 20 unidades (alerta de reposición por horneado)
          - 'disponible': stock > 20 unidades
        """
        stock = obj.stock_actual or 0
        if stock <= 0:
            return 'agotado'
        if stock <= 20:
            return 'critico'
        return 'disponible'


class MovimientoProductoTerminadoSerializer(serializers.ModelSerializer):
    """
    Serializador de movimientos de inventario terminado (Kardex de panadería).
    Permite auditar entradas (producción horneada) y salidas (ventas en mostrador o mermas).
    """
    producto_nombre = serializers.CharField(source='id_inventario.id_producto.nombre', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    origen_detalle = serializers.SerializerMethodField()

    class Meta:
        model = MovimientoProductoTerminado
        fields = [
            'id_movimiento',
            'id_inventario',
            'producto_nombre',
            'fecha_hora',
            'tipo',
            'tipo_display',
            'cantidad',
            'id_produccion',
            'id_nota_perdida',
            'origen_detalle',
        ]

    def get_origen_detalle(self, obj) -> str:
        """Descripción legible del origen del movimiento para el usuario."""
        if obj.id_produccion_id:
            return f'Producción / Horneado #{obj.id_produccion_id}'
        if obj.id_nota_perdida_id:
            return f'Nota de baja / Merma #{obj.id_nota_perdida_id}'
        if obj.tipo == 'entrada':
            return 'Ajuste inicial de inventario'
        return 'Venta en mostrador'


class ResumenExistenciasSerializer(serializers.Serializer):
    """
    Métricas consolidadas (KPIs) de existencias para la cabecera del módulo.
    """
    total_panes_distintos = serializers.IntegerField()
    total_unidades_stock = serializers.IntegerField()
    valor_total_inventario = serializers.CharField()
    productos_agotados = serializers.IntegerField()
    productos_stock_critico = serializers.IntegerField()
    productos_disponibles = serializers.IntegerField()


class NotaPerdidaProductoSerializer(serializers.ModelSerializer):
    """
    Serializador para registro de mermas y bajas de pan terminado (CU18).
    """
    producto_nombre = serializers.CharField(
        source='id_detalle_produccion.id_producto.nombre', read_only=True
    )
    registrado_por = serializers.CharField(
        source='id_usuario.nombre_usuario', read_only=True
    )

    class Meta:
        model = NotaPerdidaProducto
        fields = [
            'id_nota_perdida',
            'id_detalle_produccion',
            'producto_nombre',
            'id_usuario',
            'registrado_por',
            'cantidad',
            'costo_unitario',
            'fecha_salida',
        ]
