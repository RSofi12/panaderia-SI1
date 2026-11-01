"""
Serializadores para Existencias de Productos Terminados (CU12) y Mermas (CU18).
Autor: Roberto (Equipo Panaderia Santiago).
"""
from decimal import Decimal
from rest_framework import serializers

from apps.productos_inventario.productos.models import Producto
from .models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
)


class InventarioProductoTerminadoSerializer(serializers.ModelSerializer):
    """
    Serializador completo para el listado de existencias de productos terminados (CU12).
    Añade informacion comercial del producto y calculo en tiempo real de valorizacion y estado.
    """
    producto_nombre = serializers.CharField(source='id_producto.nombre', read_only=True)
    producto_descripcion = serializers.CharField(source='id_producto.descripcion', read_only=True)
    categoria_id = serializers.IntegerField(source='id_producto.id_categoria.id_categoria', read_only=True)
    categoria_nombre = serializers.CharField(
        source='id_producto.id_categoria.nombre', default='Sin categoria', read_only=True
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

    # Campos calculados dinamicos
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
        Clasificacion semantica del nivel de stock para badges visuales en la interfaz:
          - 'agotado': stock == 0
          - 'critico': 0 < stock <= 20 unidades
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
    Serializador de movimientos de inventario terminado (Kardex de panaderia).
    Permite auditar entradas (produccion horneada) y salidas (ventas o mermas).
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
            'id_venta',
            'id_pedido',
            'origen_detalle',
        ]

    def get_origen_detalle(self, obj) -> str:
        """Descripcion legible del origen del movimiento para el usuario."""
        if obj.id_produccion_id:
            return f'Produccion / Horneado #{obj.id_produccion_id}'
        if obj.id_nota_perdida_id:
            return f'Nota de baja / Merma #{obj.id_nota_perdida_id}'
        if obj.id_venta_id:
            numero = getattr(obj.id_venta, 'numero_comprobante', obj.id_venta_id)
            return f'Venta comprobante {numero}'
        if obj.id_pedido_id:
            return f'Pedido #{obj.id_pedido_id}'
        if obj.tipo == 'entrada':
            return 'Ajuste inicial de inventario'
        return 'Salida de mostrador'


class ResumenExistenciasSerializer(serializers.Serializer):
    """
    Metricas consolidadas (KPIs) de existencias para la cabecera del modulo.
    """
    total_panes_distintos = serializers.IntegerField()
    total_unidades_stock = serializers.IntegerField()
    valor_total_inventario = serializers.CharField()
    productos_agotados = serializers.IntegerField()
    productos_stock_critico = serializers.IntegerField()
    productos_disponibles = serializers.IntegerField()


class NotaPerdidaProductoSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para registro de mermas y bajas de pan terminado (CU18).
    """
    id_producto = serializers.IntegerField(
        source='id_detalle_produccion.id_producto_id', read_only=True
    )
    producto_nombre = serializers.CharField(
        source='id_detalle_produccion.id_producto.nombre', read_only=True
    )
    categoria_nombre = serializers.CharField(
        source='id_detalle_produccion.id_producto.id_categoria.nombre', default='Sin categoria', read_only=True
    )
    registrado_por = serializers.CharField(
        source='id_usuario.nombre_usuario', read_only=True
    )
    produccion_id = serializers.IntegerField(
        source='id_detalle_produccion.id_produccion_id', read_only=True
    )
    costo_total = serializers.SerializerMethodField()

    class Meta:
        model = NotaPerdidaProducto
        fields = [
            'id_nota_perdida',
            'id_detalle_produccion',
            'id_producto',
            'producto_nombre',
            'categoria_nombre',
            'id_usuario',
            'registrado_por',
            'produccion_id',
            'cantidad',
            'costo_unitario',
            'costo_total',
            'fecha_salida',
        ]

    def get_costo_total(self, obj) -> str:
        costo = obj.costo_unitario or Decimal('0.00')
        total = Decimal(obj.cantidad) * costo
        return str(total.quantize(Decimal('0.01')))


class NotaPerdidaProductoCreateSerializer(serializers.Serializer):
    """
    Serializador de entrada y validacion para registrar baja/merma de pan terminado (CU18).
    """
    id_producto = serializers.IntegerField(required=True)
    cantidad = serializers.IntegerField(min_value=1, required=True)
    id_detalle_produccion = serializers.IntegerField(required=False, allow_null=True)
    motivo = serializers.CharField(
        max_length=150,
        required=False,
        default='Merma / Defecto de elaboracion',
    )
    observaciones = serializers.CharField(
        max_length=300,
        required=False,
        allow_blank=True,
        default='',
    )
    costo_unitario = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    def validate_id_producto(self, value):
        if not Producto.objects.filter(id_producto=value).exists():
            raise serializers.ValidationError(f'El producto con ID {value} no existe.')
        return value

    def validate(self, attrs):
        id_producto = attrs.get('id_producto')
        cantidad = attrs.get('cantidad')

        try:
            inventario = InventarioProductoTerminado.objects.select_related('id_producto').get(
                id_producto_id=id_producto
            )
        except InventarioProductoTerminado.DoesNotExist:
            raise serializers.ValidationError({
                'id_producto': 'El producto seleccionado no cuenta con inventario inicializado.'
            })

        if inventario.stock_actual < cantidad:
            raise serializers.ValidationError({
                'cantidad': (
                    f'Stock insuficiente para dar de baja: actualmente hay '
                    f'{inventario.stock_actual} unidades en vitrina y se solicitan {cantidad}.'
                )
            })

        attrs['inventario'] = inventario
        return attrs