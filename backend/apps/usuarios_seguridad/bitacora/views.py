"""
Consulta de la bitácora de auditoría (CU26 — Gestionar bitácora).

El REGISTRO de la bitácora no pasa por aquí: cada caso de uso lo hace con
`Bitacora.registrar()` dentro de su propia transacción. Esta API solo consulta,
y por eso no expone alta, edición ni borrado: una traza de auditoría que se
puede modificar por HTTP deja de ser evidencia.
"""
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usuarios_seguridad.users.models import Usuario
from apps.usuarios_seguridad.users.permissions import TienePermiso

from .models import AccionBitacora, Bitacora
from .serializers import BitacoraSerializer

PERMISO_REQUERIDO = 'consultar_bitacora'
ACCIONES_VALIDAS = set(AccionBitacora.values)


def _leer_fecha(params, clave):
    valor = params.get(clave)
    if not valor:
        return None
    try:
        fecha = parse_date(valor)
    except ValueError:
        fecha = None
    if fecha is None:
        raise ValidationError({clave: 'Fecha inválida. Usa el formato AAAA-MM-DD.'})
    return fecha


class ConsultaBitacoraMixin:
    """Administrador y Propietario: los roles que tienen `consultar_bitacora`."""

    def get_permissions(self):
        return [TienePermiso(PERMISO_REQUERIDO)]


class BitacoraListView(ConsultaBitacoraMixin, generics.ListAPIView):
    """
    GET /api/bitacora/ — Historial de auditoría, del más reciente al más antiguo.

    Filtros opcionales (combinables):
      ?fecha_desde=AAAA-MM-DD  ?fecha_hasta=AAAA-MM-DD  (inclusive, hora local)
      ?usuario=<id_usuario>    ?modulo=<tabla_afectada>  ?accion=<AccionBitacora>
      ?q=<texto>               busca en descripción y nombre de usuario
    """
    serializer_class = BitacoraSerializer

    def get_queryset(self):
        params = self.request.query_params
        registros = Bitacora.objects.select_related('usuario').order_by('-fecha_hora', '-id_bitacora')

        fecha_desde = _leer_fecha(params, 'fecha_desde')
        fecha_hasta = _leer_fecha(params, 'fecha_hasta')
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError({'fecha_hasta': 'La fecha final no puede ser anterior a la inicial.'})
        if fecha_desde:
            registros = registros.filter(fecha_hora__date__gte=fecha_desde)
        if fecha_hasta:
            registros = registros.filter(fecha_hora__date__lte=fecha_hasta)

        usuario = params.get('usuario')
        if usuario:
            if not usuario.isdigit():
                raise ValidationError({'usuario': 'El usuario debe ser un identificador numérico.'})
            registros = registros.filter(usuario_id=int(usuario))

        modulo = params.get('modulo')
        if modulo:
            registros = registros.filter(tabla_afectada=modulo)

        accion = params.get('accion')
        if accion:
            if accion not in ACCIONES_VALIDAS:
                raise ValidationError({'accion': 'Acción desconocida.'})
            registros = registros.filter(accion=accion)

        texto = (params.get('q') or '').strip()
        if texto:
            registros = registros.filter(
                Q(descripcion__icontains=texto)
                | Q(usuario__nombre_usuario__icontains=texto)
                | Q(usuario__nombre_completo__icontains=texto)
                | Q(nombre_usuario_intento__icontains=texto)
            )

        return registros


class BitacoraOpcionesView(ConsultaBitacoraMixin, APIView):
    """
    GET /api/bitacora/opciones/ — Valores para los filtros de la pantalla:
    el catálogo de acciones, los módulos y los usuarios que tienen registros.
    """

    def get(self, request):
        modulos = (
            Bitacora.objects.exclude(tabla_afectada__isnull=True)
            .exclude(tabla_afectada='')
            .values_list('tabla_afectada', flat=True)
            .distinct()
            .order_by('tabla_afectada')
        )
        usuarios = (
            Usuario.objects.filter(bitacoras__isnull=False)
            .distinct()
            .order_by('nombre_usuario')
            .values('id_usuario', 'nombre_usuario', 'nombre_completo')
        )
        return Response({
            'acciones': [{'valor': valor, 'etiqueta': etiqueta} for valor, etiqueta in AccionBitacora.choices],
            'modulos': list(modulos),
            'usuarios': list(usuarios),
        })
