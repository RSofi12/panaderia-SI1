from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios_seguridad.bitacora.models import Bitacora

from .models import CategoriaProducto, HistorialPrecioProducto, Producto
from .permissions import PuedeGestionarProductos
from .serializers import CategoriaProductoSerializer, ProductoSerializer


class CategoriaProductoListView(APIView):
    """GET /api/categorias-producto/ — Lista de categorías del catálogo."""
    permission_classes = [PuedeGestionarProductos]

    def get(self, request):
        categorias = CategoriaProducto.objects.all()
        return Response(CategoriaProductoSerializer(categorias, many=True).data)


class ProductoListCreateView(APIView):
    """
    GET  /api/productos/ — Catálogo con filtros ?nombre=, ?id_categoria=, ?activo=true|false
    POST /api/productos/ — Alta de producto (requiere gestionar_productos)
    """
    permission_classes = [PuedeGestionarProductos]

    def get(self, request):
        productos = Producto.objects.select_related('id_categoria')

        nombre = request.query_params.get('nombre')
        id_categoria = request.query_params.get('id_categoria')
        activo = request.query_params.get('activo')

        if nombre:
            productos = productos.filter(nombre__icontains=nombre.strip())
        if id_categoria:
            productos = productos.filter(id_categoria_id=id_categoria)
        if activo in ('true', 'false'):
            productos = productos.filter(activo=(activo == 'true'))

        return Response(ProductoSerializer(productos, many=True).data)

    def post(self, request):
        serializer = ProductoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            producto = serializer.save()
            HistorialPrecioProducto.objects.create(
                id_producto=producto,
                precio=producto.precio_venta,
            )
            Bitacora.registrar(
                usuario=request.user,
                accion='CREACION',
                tabla_afectada='producto',
                descripcion=f'Alta del producto {producto.nombre} con precio de venta Bs {producto.precio_venta}',
            )

        return Response(ProductoSerializer(producto).data, status=status.HTTP_201_CREATED)


class ProductoDetailView(APIView):
    """
    GET       /api/productos/<id>/ — Detalle de producto
    PUT/PATCH /api/productos/<id>/ — Edición; un cambio de precio de venta queda en el historial
    """
    permission_classes = [PuedeGestionarProductos]

    def get(self, request, pk):
        producto = get_object_or_404(Producto.objects.select_related('id_categoria'), pk=pk)
        return Response(ProductoSerializer(producto).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, partial):
        producto = get_object_or_404(Producto, pk=pk)
        precio_anterior = producto.precio_venta

        serializer = ProductoSerializer(producto, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            producto = serializer.save()

            if producto.precio_venta != precio_anterior:
                HistorialPrecioProducto.objects.create(
                    id_producto=producto,
                    precio=producto.precio_venta,
                )
                descripcion = (
                    f'Precio de venta de {producto.nombre} actualizado '
                    f'de Bs {precio_anterior} a Bs {producto.precio_venta}'
                )
            else:
                descripcion = f'Edición de datos del producto {producto.nombre}'

            Bitacora.registrar(
                usuario=request.user,
                accion='MODIFICACION',
                tabla_afectada='producto',
                descripcion=descripcion,
            )

        return Response(ProductoSerializer(producto).data)


class ProductoToggleActivoView(APIView):
    """PATCH /api/productos/<id>/toggle-activo/ — Activa o inactiva un producto (no se borra)."""
    permission_classes = [PuedeGestionarProductos]

    def patch(self, request, pk):
        producto = get_object_or_404(Producto, pk=pk)

        with transaction.atomic():
            producto.activo = not producto.activo
            producto.save(update_fields=['activo'])
            estado = 'activado' if producto.activo else 'inactivado'
            Bitacora.registrar(
                usuario=request.user,
                accion='CAMBIO_ESTADO',
                tabla_afectada='producto',
                descripcion=f'Producto {producto.nombre} {estado}',
            )

        return Response(ProductoSerializer(producto).data)
