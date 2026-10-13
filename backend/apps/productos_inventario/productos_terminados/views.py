"""
Vistas de API para Existencias de Productos Terminados (CU12) y Bajas/Mermas (CU18).
Autor de la implementación CU12: Roberto (Equipo Panadería Santiago).
"""
from decimal import Decimal
from django.db.models import Sum, Q, F
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    InventarioProductoTerminado,
    MovimientoProductoTerminado,
    NotaPerdidaProducto,
)
from .permissions import PuedeConsultarExistenciasTerminados
from .serializers import (
    InventarioProductoTerminadoSerializer,
    MovimientoProductoTerminadoSerializer,
    NotaPerdidaProductoSerializer,
    ResumenExistenciasSerializer,
)


class ExistenciasListView(APIView):
    """
    GET /api/productos-terminados/existencias/

    Caso de Uso CU12: Consultar existencias de productos terminados.
    Permite consultar en tiempo real las existencias disponibles de cada tipo de pan listo
    para la venta en mostrador.

    Parámetros de consulta (Query Params):
      - q: Búsqueda insensible a mayúsculas por nombre del pan.
      - categoria: ID numérico de la categoría de producto.
      - estado_stock: Filtro de disponibilidad ('disponible', 'critico', 'agotado').
      - solo_activos: 'true' (por defecto) para mostrar solo panes activos, 'false' para incluir inactivos.
      - ordenar_por: Criterio de ordenamiento ('nombre_asc', 'nombre_desc', 'stock_asc', 'stock_desc', 'precio_asc', 'precio_desc').
    """
    permission_classes = [PuedeConsultarExistenciasTerminados]

    def get(self, request):
        queryset = InventarioProductoTerminado.objects.select_related(
            'id_producto',
            'id_producto__id_categoria',
        )

        # 1. Filtro por estado activo del producto (por defecto solo productos activos)
        solo_activos = request.query_params.get('solo_activos', 'true').lower()
        if solo_activos != 'false':
            queryset = queryset.filter(id_producto__activo=True)

        # 2. Búsqueda por texto (nombre o descripción)
        q = request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(id_producto__nombre__icontains=q) |
                Q(id_producto__descripcion__icontains=q)
            )

        # 3. Filtro por categoría
        categoria_id = request.query_params.get('categoria')
        if categoria_id and categoria_id.isdigit():
            queryset = queryset.filter(id_producto__id_categoria_id=int(categoria_id))

        # 4. Filtro por estado de stock
        estado_stock = request.query_params.get('estado_stock', '').strip().lower()
        if estado_stock == 'agotado':
            queryset = queryset.filter(stock_actual__lte=0)
        elif estado_stock == 'critico':
            queryset = queryset.filter(stock_actual__gt=0, stock_actual__lte=20)
        elif estado_stock == 'disponible':
            queryset = queryset.filter(stock_actual__gt=20)

        # 5. Ordenamiento
        ordenar_por = request.query_params.get('ordenar_por', 'nombre_asc').lower()
        if ordenar_por == 'nombre_desc':
            queryset = queryset.order_by('-id_producto__nombre')
        elif ordenar_por == 'stock_asc':
            queryset = queryset.order_by('stock_actual', 'id_producto__nombre')
        elif ordenar_por == 'stock_desc':
            queryset = queryset.order_by('-stock_actual', 'id_producto__nombre')
        elif ordenar_por == 'precio_asc':
            queryset = queryset.order_by('id_producto__precio_venta', 'id_producto__nombre')
        elif ordenar_por == 'precio_desc':
            queryset = queryset.order_by('-id_producto__precio_venta', 'id_producto__nombre')
        else:
            # nombre_asc por defecto
            queryset = queryset.order_by('id_producto__nombre')

        serializer = InventarioProductoTerminadoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResumenExistenciasView(APIView):
    """
    GET /api/productos-terminados/existencias/resumen/

    Retorna métricas consolidadas (KPIs) en tiempo real para las tarjetas de información:
      - Total de variedades de pan en catálogo activo
      - Total de piezas de pan listas en mostrador
      - Valor monetario total del stock en vitrina (Bs.)
      - Conteo de productos agotados, críticos y con stock normal
    """
    permission_classes = [PuedeConsultarExistenciasTerminados]

    def get(self, request):
        queryset = InventarioProductoTerminado.objects.filter(
            id_producto__activo=True
        ).select_related('id_producto')

        total_panes_distintos = queryset.count()
        total_unidades = 0
        valor_total = Decimal('0.00')
        agotados = 0
        criticos = 0
        disponibles = 0

        for inv in queryset:
            stock = inv.stock_actual or 0
            precio = inv.id_producto.precio_venta or Decimal('0.00')
            total_unidades += stock
            valor_total += (Decimal(stock) * precio)

            if stock <= 0:
                agotados += 1
            elif stock <= 20:
                criticos += 1
            else:
                disponibles += 1

        datos = {
            'total_panes_distintos': total_panes_distintos,
            'total_unidades_stock': total_unidades,
            'valor_total_inventario': str(valor_total.quantize(Decimal('0.01'))),
            'productos_agotados': agotados,
            'productos_stock_critico': criticos,
            'productos_disponibles': disponibles,
        }

        serializer = ResumenExistenciasSerializer(datos)
        return Response(serializer.data, status=status.HTTP_200_OK)


class KardexProductoTerminadoView(APIView):
    """
    GET /api/productos-terminados/existencias/<int:id_producto>/movimientos/

    Kardex / Historial de movimientos del producto terminado:
    Permite auditar el flujo de un pan específico (entradas por horneado y salidas por venta/merma).
    """
    permission_classes = [PuedeConsultarExistenciasTerminados]

    def get(self, request, id_producto: int):
        inventario = get_object_or_404(
            InventarioProductoTerminado.objects.select_related('id_producto'),
            id_producto_id=id_producto,
        )

        movimientos = MovimientoProductoTerminado.objects.filter(
            id_inventario=inventario
        ).select_related(
            'id_inventario__id_producto',
            'id_produccion',
            'id_nota_perdida',
        ).order_by('-fecha_hora', '-id_movimiento')[:50]

        serializer = MovimientoProductoTerminadoSerializer(movimientos, many=True)
        return Response({
            'producto_id': inventario.id_producto.id_producto,
            'producto_nombre': inventario.id_producto.nombre,
            'stock_actual': inventario.stock_actual,
            'movimientos': serializer.data,
        }, status=status.HTTP_200_OK)


class NotaPerdidaProductoListCreateView(APIView):
    """
    GET  /api/productos-terminados/mermas/ — Historial de bajas de producto terminado (CU18).
    POST /api/productos-terminados/mermas/ — Registrar baja/merma descontando stock (CU18 - Ciclo 3).
    """
    permission_classes = [PuedeConsultarExistenciasTerminados]

    def get(self, request):
        notas = NotaPerdidaProducto.objects.select_related(
            'id_detalle_produccion__id_producto',
            'id_usuario',
        ).order_by('-fecha_salida')
        return Response(NotaPerdidaProductoSerializer(notas, many=True).data)
