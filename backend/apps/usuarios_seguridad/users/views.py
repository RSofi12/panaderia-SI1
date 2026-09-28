"""
Vistas de la administración de cuentas (CU3 — Gestionar usuarios).

La vista es DELIBERADAMENTE fina. Su único trabajo es:

  1. traducir HTTP a una llamada de servicio,
  2. decidir qué serializer entra y cuál sale.

No hay una sola regla de negocio dentro de este archivo. Todo lo que decide
algo — si la cuenta puede quedarse sin Administrador, si hay que revocar
sesiones, qué se escribe en la bitácora — vive en
`users/services/usuarios.py`. Es el mismo criterio que YA se aplicó en CU1,
donde `CustomLoginView` quedó reducida a un `throttle_classes` porque la lógica
se mudó al serializador y al servicio. La razón es que la lógica de negocio se
pueda probar sin levantar HTTP.

Lo que la vista sí tiene que resolver, y por eso está aquí y no allá:

  * Los permisos: `gestionar_usuarios` leído del catálogo.
  * El recorte de la consulta, para no traer la tabla entera.
  * El borrado DESACTIVADO. No es un olvido: el CU3 no incluye borrado.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from apps.usuarios_seguridad.roles.models import Rol
from apps.usuarios_seguridad.users.models import Usuario
from apps.usuarios_seguridad.users.permissions import TienePermiso
from apps.usuarios_seguridad.users.serializers import (
    CambioEstadoSerializer,
    RestablecerContrasenaSerializer,
    RolSimpleSerializer,
    UsuarioCreateSerializer,
    UsuarioListSerializer,
    UsuarioUpdateSerializer,
)
from apps.usuarios_seguridad.users.services import usuarios as servicio


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    API de gestión de cuentas del Administrador (CU3).

    Endpoints expuestos:

      GET    /api/usuarios/                             listado filtrado y paginado
      POST   /api/usuarios/                             alta de cuenta
      GET    /api/usuarios/roles/                       roles para el desplegable
      GET    /api/usuarios/<id>/                        detalle
      PATCH  /api/usuarios/<id>/                        edición parcial
      PUT    /api/usuarios/<id>/                        edición completa
      PATCH  /api/usuarios/<id>/toggle-activo/          activar / inactivar
      POST   /api/usuarios/<id>/restablecer-contrasena/ reset administrativo de clave
      POST   /api/usuarios/<id>/desbloquear/            levantar bloqueo de CU1

    NO hay `DELETE`. El CU3 no contempla el borrado de cuentas y el modelo no lo
    soporta: `usuario` es referenciado por `bitacora`, `token_recuperacion`,
    `pedido`, `venta`, `compra`, `produccion` y `movimiento_economico`. Un
    DELETE sobre esas referencias destruiría el historial económico de la
    panadería y dejaría la auditoría sin autor, que es justo lo contrario de lo
    que la bitácora existe para evitar.

    Pedir `/api/usuarios/<id>/` por DELETE devuelve 405, no 404. La diferencia no
    es cosmética: 404 diría "este endpoint no existe", mientras que 405 dice "el
    borrado está en la API y está prohibido por diseño".
    """

    # NO se escribe `permission_classes = [TienePermiso('gestionar_usuarios')]`.
    #
    # Parece la forma obvia y no funciona: `APIView.get_permissions()` hace
    # `permission()` sobre cada elemento de `permission_classes`, es decir,
    # vuelve a INSTANCIAR lo que hay en la lista. Si en la lista hay una
    # instancia ya construida —que es lo que es `TienePermiso('...')`—, el
    # intento de llamarla como un constructor revienta con
    # `TypeError: 'TienePermiso' object is not callable`.
    #
    # La forma correcta para un permiso con parámetro es sobreescribir
    # `get_permissions()`, que es exactamente para esto.
    permission_classes = [TienePermiso]  # noqa: RUF012 — se instancia abajo.

    def get_permissions(self):
        """
        Instancia el permiso de DRF con el nombre del permiso que exige el CU3.

        Que el string 'gestionar_usuarios' viva en un solo lugar y no repetido
        en cinco endpoints es la razón de que el permiso sea parametrizado: si
        estuviera fijo en la clase, el día que el catálogo lo renombre habría que
        buscar cada aparición.
        """
        return [TienePermiso(self.PERMISO_REQUERIDO)]

    #: Clave del permiso en la tabla `permiso`, leída por
    #: `Usuario.get_permisos_nombres()`. Es el mismo dato que viaja como claim
    #: `permisos` en el JWT, así que el botón que el frontend muestra y el que
    #: el backend acepta no pueden desincronizarse.
    PERMISO_REQUERIDO = 'gestionar_usuarios'

    # `ScopedRateThrottle` lee la clave `throttle_scope` de la vista y busca su
    # nombre en `DEFAULT_THROTTLE_RATES`. Es un límite POR USUARIARIO
    # autenticado, no por IP: la IP no sirve de nada acá, porque el Administrador
    # de la panadería y un atacante que robó su sesión están detrás del mismo
    # cable y se verían igual.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'usuarios'

    # `delete` queda fuera de la lista de forma explícita. Es lo que produce el
    # 405 sin tener que escribir un `perform_destroy` que aborte, y de paso deja
    # el motivo documentado en el mismo lugar donde alguien lo va a buscar.
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    # Los filtros se declaran AQUÍ y no en `DEFAULT_FILTER_BACKENDS` a
    # propósito. Los filtros de DRF alcanzan a cualquier `GenericAPIView` que
    # exponga `get_queryset`, y `TokenObtainPairView` de CU1/CU2 lo es. Un
    # ajuste global también lo tocaría, y no hay motivo para que el login
    # dependa de la configuración de la API de usuarios.
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['nombre_usuario', 'nombre_completo', 'email']
    ordering_fields = ['id_usuario', 'nombre_usuario', 'nombre_completo', 'last_login']
    ordering = ['id_usuario']

    def get_queryset(self):
        """
        Consulta base de la tabla de usuarios, con los filtros de la URL aplicados.

        `select_related('id_rol')` evita una consulta por usuario para leer el
        nombre del rol. `prefetch_related` precarga los permisos del rol, que el
        serializer cuenta en `total_permisos`: sin esto, un listado de 10 filas
        dispararía 10 consultas adicionales, que es el problema clásico de N+1
        y la razón más común de que un listado "lentito" se vuelva de golpe
        lento cuando le agregan un filtro de rol.
        """
        consulta = (
            Usuario.objects.select_related('id_rol')
            .prefetch_related('id_rol__permisos')
            .order_by('id_usuario')
        )

        parametros = self.request.query_params

        # Filtro por estado. Se acepta `activo=true|false` y también
        # `activo=1|0`, porque el frontend manda el valor de un <select> y el
        # que llega del backend es un booleano de Python, no una cadena.
        activo = parametros.get('activo')
        if activo not in (None, ''):
            consulta = consulta.filter(activo=str(activo).lower() in ('true', '1', 'activo'))

        # Filtro por rol. Se ignora un valor vacío para que el desplegable
        # pueda mandar "" como "todos los roles" sin ensuciar la URL.
        id_rol = parametros.get('id_rol')
        if id_rol not in (None, '', 'todos'):
            try:
                consulta = consulta.filter(id_rol_id=int(id_rol))
            except (TypeError, ValueError):
                # Un id_rol no numérico no es un error del servidor: es una
                # búsqueda mal formada, y la respuesta razonable es ignorar el
                # filtro y devolver la lista completa.
                pass

        return consulta

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UsuarioUpdateSerializer
        if self.action == 'roles':
            return RolSimpleSerializer
        return UsuarioListSerializer

    def perform_create(self, serializer):
        """
        El `create` real lo hace el servicio, dentro de una transacción.

        `ModelViewSet` exige que este método exista; se deja explícito para que
        quede claro que no se salta nada por descuido. Toda la lógica de alta —
        hash, auditoría, reglas de negocio — ocurre en `registrar_usuario`.
        """
        serializer.save()

    def perform_update(self, serializer):
        """Igual que `perform_create`: el `update` real vive en el servicio."""
        serializer.save()

    @action(detail=True, methods=['patch'], url_path='toggle-activo')
    def toggle_activo(self, request, pk=None):
        """
        Activar o inactivar una cuenta (`activar()` / `inactivar()`).

        Se expone como acción aparte y no como un `PATCH` de `activo` por dos
        razones. La primera es que el caso de uso la nombra como operación
        propia, y una ruta propia se puede proteger y auditar por separado. La
        segunda es que inactivar tiene un efecto que un PATCH normal no tiene:
        revoca las sesiones abiertas del usuario. Un endpoint genérico de
        actualización no puede envolver eso sin dejar de ser genérico.
        """
        usuario = self.get_object()

        datos = CambioEstadoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)

        servicio.cambiar_estado(
            usuario=usuario,
            nuevo_estado=datos.validated_data['activo'],
            ejecutado_por=request.user,
            motivo=datos.validated_data.get('motivo'),
            ip=self._ip(request),
        )

        return Response(
            self._serializar_detalle(usuario),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='restablecer-contrasena')
    def restablecer_contrasena(self, request, pk=None):
        """
        Restablecimiento administrativo de clave (`cambiarContrasena()`).

        Este endpoint NO es parte del núcleo del CU3, que según
        `backend/apps/PACKAGE_CU_MAP.md` es "registro, edición, activación e
        inactivación". Es la contraparte del CU2 vista desde el Administrador, y
        se implementa porque el diagrama de clases define `cambiarContrasena()`
        en la clase `Usuario`. La frontera queda anotada en `DECISIONS_LOG.md`
        para que la revisión vea con precisión qué es núcleo del CU y qué es
        extensión de administración de cuentas.
        """
        usuario = self.get_object()

        datos = RestablecerContrasenaSerializer(
            data=request.data,
            context={'usuario': usuario, 'request': request},
        )
        datos.is_valid(raise_exception=True)

        servicio.restablecer_contrasena(
            usuario=usuario,
            nueva_contrasena=datos.validated_data['nueva_contrasena'],
            ejecutado_por=request.user,
            ip=self._ip(request),
            agente=self._agente(request),
        )

        return Response(
            {
                'message': (
                    f'Contraseña de "{usuario.nombre_usuario}" restablecida. '
                    'Las sesiones abiertas de esa cuenta quedaron cerradas.'
                ),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='desbloquear')
    def desbloquear(self, request, pk=None):
        """
        Levanta el bloqueo por intentos fallidos.

        Delega íntegramente en `politica_bloqueo.desbloquear_usuario`, la función
        escrita en CU1. La regla de cuándo una cuenta está bloqueada ya está
        probada y auditada; reimplementarla acá abriría la puerta a que las dos
        versiones diverijan, que es el peor defecto posible en una política de
        seguridad.
        """
        usuario = self.get_object()

        servicio.desbloquear_cuenta(
            usuario=usuario,
            ejecutado_por=request.user,
            motivo=request.data.get('motivo')
            or 'Desbloqueo solicitado por el Administrador',
        )

        return Response(
            {
                'message': (
                    f'Cuenta "{usuario.nombre_usuario}" desbloqueada. '
                    'Ya puede volver a iniciar sesión.'
                ),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='roles', url_name='roles')
    def roles(self, request):
        """
        Roles disponibles para el desplegable del formulario de alta y edición.

        Vive en este ViewSet y no en uno de la sub-app `roles` por una razón
        práctica: la página de gestión de usuarios lo necesita en su mismo
        módulo. Exponer aquí un `/api/roles/` completo equivaldría a publicar la
        gestión de la matriz de permisos, que es CU4, antes de que ese CU exista.

        No va paginado a propósito: son cuatro filas. Paginarlas sería ruido.
        """
        serializer = RolSimpleSerializer(
            Rol.objects.prefetch_related('permisos').order_by('id_rol'),
            many=True,
            context=self.get_serializer_context(),
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _serializar_detalle(self, usuario):
        return UsuarioListSerializer(
            usuario,
            context=self.get_serializer_context(),
        ).data

    @staticmethod
    def _ip(request):
        reenviado = request.META.get('HTTP_X_FORWARDED_FOR')
        if reenviado:
            return reenviado.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _agente(request):
        return (request.META.get('HTTP_USER_AGENT') or '')[:255] or None
