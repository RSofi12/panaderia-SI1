from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.productos_inventario.productos_terminados.models import InventarioProductoTerminado
from apps.productos_inventario.productos_terminados.permissions import PuedeConsultarExistenciasTerminados

from .serializers import DisponibilidadProductoSerializer


class DisponibilidadProductosView(APIView):
    """GET /api/disponibilidad/ — CU17, panes activos con stock disponible."""

    permission_classes = [PuedeConsultarExistenciasTerminados]

    def get(self, request):
        productos = InventarioProductoTerminado.objects.select_related(
            'id_producto', 'id_producto__id_categoria'
        ).filter(id_producto__activo=True, stock_actual__gt=0)
        q = request.query_params.get('q', '').strip()
        if q:
            productos = productos.filter(
                Q(id_producto__nombre__icontains=q)
                | Q(id_producto__descripcion__icontains=q)
            )
        categoria = request.query_params.get('categoria', '').strip()
        if categoria.isdigit():
            productos = productos.filter(id_producto__id_categoria_id=int(categoria))
        productos = productos.order_by('id_producto__nombre')
        return Response(DisponibilidadProductoSerializer(productos, many=True).data)
