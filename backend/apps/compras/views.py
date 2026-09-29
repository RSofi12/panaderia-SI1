from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora

from .models import Proveedor
from .permissions import PuedeGestionarProveedores
from .serializers import ProveedorSerializer


class ProveedorListCreateView(APIView):
    """
    GET  /api/proveedores/ — Directorio con filtros ?q=, ?nombre=, ?telefono=, ?activo=
    POST /api/proveedores/ — Alta (requiere gestionar_proveedores)
    """
    permission_classes = [PuedeGestionarProveedores]

    def get(self, request):
        proveedores = Proveedor.objects.all()

        consulta = request.query_params.get('q')
        nombre = request.query_params.get('nombre')
        telefono = request.query_params.get('telefono')
        activo = request.query_params.get('activo')

        if consulta:
            termino = consulta.strip()
            proveedores = proveedores.filter(
                Q(nombre__icontains=termino) | Q(telefono__icontains=termino)
            )
        if nombre:
            proveedores = proveedores.filter(nombre__icontains=nombre.strip())
        if telefono:
            proveedores = proveedores.filter(telefono__icontains=telefono.strip())
        if activo in ('true', 'false'):
            proveedores = proveedores.filter(activo=(activo == 'true'))

        return Response(ProveedorSerializer(proveedores, many=True).data)

    def post(self, request):
        serializer = ProveedorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            proveedor = serializer.save()
            Bitacora.registrar(
                usuario=request.user,
                accion=AccionBitacora.ALTA_PROVEEDOR,
                tabla_afectada='proveedor',
                descripcion=f'Alta del proveedor {proveedor.nombre}',
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )

        return Response(ProveedorSerializer(proveedor).data, status=status.HTTP_201_CREATED)


class ProveedorDetailView(APIView):
    """
    GET       /api/proveedores/<id>/ — Detalle
    PUT/PATCH /api/proveedores/<id>/ — Edición de contacto/dirección
    """
    permission_classes = [PuedeGestionarProveedores]

    def get(self, request, pk):
        proveedor = get_object_or_404(Proveedor, pk=pk)
        return Response(ProveedorSerializer(proveedor).data)

    def put(self, request, pk):
        return self._actualizar(request, pk, partial=False)

    def patch(self, request, pk):
        return self._actualizar(request, pk, partial=True)

    def _actualizar(self, request, pk, partial):
        proveedor = get_object_or_404(Proveedor, pk=pk)
        serializer = ProveedorSerializer(proveedor, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            proveedor = serializer.save()
            Bitacora.registrar(
                usuario=request.user,
                accion=AccionBitacora.EDICION_PROVEEDOR,
                tabla_afectada='proveedor',
                descripcion=f'Edición de datos del proveedor {proveedor.nombre}',
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )

        return Response(ProveedorSerializer(proveedor).data)


class ProveedorToggleActivoView(APIView):
    """PATCH /api/proveedores/<id>/toggle-activo/ — Activa o inactiva (no se borra)."""
    permission_classes = [PuedeGestionarProveedores]

    def patch(self, request, pk):
        proveedor = get_object_or_404(Proveedor, pk=pk)

        with transaction.atomic():
            proveedor.activo = not proveedor.activo
            proveedor.save(update_fields=['activo'])
            estado = 'activado' if proveedor.activo else 'inactivado'
            Bitacora.registrar(
                usuario=request.user,
                accion=AccionBitacora.CAMBIAR_ESTADO_PROVEEDOR,
                tabla_afectada='proveedor',
                descripcion=f'Proveedor {proveedor.nombre} {estado}',
                agente_usuario=request.META.get('HTTP_USER_AGENT'),
            )

        return Response(ProveedorSerializer(proveedor).data)
