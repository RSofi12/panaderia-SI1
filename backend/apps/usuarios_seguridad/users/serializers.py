"""
Serializadores de la administración de cuentas (CU3).

Cada serializer tiene un trabajo y ninguno repite lo del otro:

  UsuarioListSerializer       qué se ve en la tabla del panel (solo lectura)
  UsuarioCreateSerializer     alta, con la política de contraseñas
  UsuarioUpdateSerializer     edición, donde la contraseña es OPCIONAL
  CambioEstadoSerializer      activar / inactivar
  RestablecerContrasenaSerializer  reset administrativo de clave

Por qué están separados y no hay un solo `UsuarioSerializer` con `fields = '*'`:
porque las reglas de escritura y de lectura no son las mismas. El listado expone
`esta_bloqueado` y `minutos_bloqueo_restantes`, que son propiedades calculadas y
no columnas; la alta expone `password` en claro y la edición no debería
obligar a reescribirla. Un serializer único terminaría exponiendo campos que no
deben salir juntos.

Sobre la unicidad de `nombre_usuario` y `email`: los dos se validan SIN
DISTINGUIR MAYÚSCULAS porque así está el índice único en la base
(`users/migrations/0005`) y porque el login busca por coincidencia exacta. Si el
código dijera "disponible" para un `Admin` que la base va a rechazar, el
Administrador vería un error de integridad en vez de un mensaje de validación.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.usuarios_seguridad.roles.models import Rol
from apps.usuarios_seguridad.users.password_validators import validar_contrasena

Usuario = get_user_model()


def _normalizar_texto(valor):
    """Recorta y colapsa espacios. Devuelve cadena vacía si no hay valor."""
    return ' '.join(str(valor).split()) if valor is not None else ''


def _existe_nombre_usuario_de_otro(valor, usuario=None):
    """
    ¿`nombre_usuario` ya está tomado, ignorando mayúsculas y minúsculas?

    El nombre de la función dice lo que consulta. Antes se llamaba
    `_existe_contraseña_de_otro`, que mentía: el argumento que recibe es un
    nombre de usuario y lo que mira es `nombre_usuario__iexact`. La lógica
    siempre estuvo bien, pero un nombre que dice "contraseña" invites al
    próximo a pasarle la contraseña y esperar que así se detecte una repetida,
    que no es lo que hace.
    """
    consulta = Usuario.objects.filter(nombre_usuario__iexact=valor)
    if usuario is not None and usuario.pk:
        consulta = consulta.exclude(pk=usuario.pk)
    return consulta.exists()


def _existe_email_de_otro(valor, usuario=None):
    """¿`email` ya está tomado, ignorando mayúsculas y minúsculas?"""
    consulta = Usuario.objects.filter(email__iexact=valor)
    if usuario is not None and usuario.pk:
        consulta = consulta.exclude(pk=usuario.pk)
    return consulta.exists()


class UsuarioListSerializer(serializers.ModelSerializer):
    """
    Fila de la tabla de usuarios del panel del Administrador.

    Se separates de la escritura porque es de SOLO LECTURA: no tiene `create`
    ni `update`, y por lo tanto no puede usarse por accidente en un POST. En DRF
    un serializer sin `create` que recibe datos lanza `AssertionError` al
    intento de guardar, que es justo la clase de error que no queremos ver en
    producción.

    `total_permisos` es un número y no la lista completa de permisos a propósito:
    serializar la lista por cada fila del listado dispararía una consulta por
    usuario (N+1). Con `prefetch_related` en la vista, el conteo sale de la
    caché y la lista de permisos se pide solo en el detalle.
    """

    rol = serializers.CharField(source='rol_nombre', read_only=True)
    esta_bloqueado = serializers.BooleanField(source='is_bloqueado', read_only=True)
    minutos_bloqueo_restantes = serializers.IntegerField(read_only=True)
    total_permisos = serializers.SerializerMethodField()
    puede_iniciar_sesion = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'email',
            'activo',
            'id_rol',
            'rol',
            'total_permisos',
            'intentos_fallidos',
            'esta_bloqueado',
            'minutos_bloqueo_restantes',
            'ultimo_intento_fallido',
            'last_login',
            'puede_iniciar_sesion',
        )
        read_only_fields = fields

    def get_total_permisos(self, usuario):
        if not usuario.id_rol_id:
            return 0
        return usuario.id_rol.permisos.count()

    def get_puede_iniciar_sesion(self, usuario):
        """
        ¿Puede esta cuenta autenticarse ahora mismo?

        Responde de una sola vez a las tres razones por las que el login puede
        negarse: que esté inactiva, que esté bloqueada, o que no tenga ningún
        rol asignado. El frontend lo usa para explicar el motivo en la propia
        fila, en vez de obligar al Administrador a deducirlo de tres columnas.
        """
        if not usuario.activo:
            return False
        if usuario.is_bloqueado:
            return False
        return usuario.id_rol_id is not None


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    Alta de cuenta (`registrar()`).

    `password` es `write_only` y nunca vuelve en la respuesta. Tampoco se
    acepta en la lectura, así que un `GET` a este serializer no puede exponer un
    hash por accidente aunque alguien lo reutilice donde no toca.

    La política de contraseñas se ejecuta con `validar_contrasena()`, la misma
    función que consume CU2. Que el alta de una cuenta y el restablecimiento de
    una contraseña apliquen exactamente las mismas reglas es lo que evita que
    exista una puerta trasera por la que se puedan crear cuentas con claves que
    el sistema rechazaría en el login.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        trim_whitespace=False,
        style={'input_type': 'password'},
        label='Contraseña',
        help_text='Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo.',
    )
    rol = serializers.CharField(source='rol_nombre', read_only=True)

    class Meta:
        model = Usuario
        fields = (
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'email',
            'password',
            'id_rol',
            'rol',
            'activo',
        )
        read_only_fields = ('id_usuario', 'rol')
        # `trim_whitespace` en `nombre_usuario` es False a propósito: si el
        # Administrador pega un espacio al final, es mejor que se note en el
        # mensaje de error que aceptarlo en silencio y crear "mgonzales " que
        # después no podrá escribir en el login.
        extra_kwargs = {
            'nombre_usuario': {
                'trim_whitespace': False,
                'label': 'Nombre de usuario',
                'help_text': 'Con este nombre inicia sesión la persona.',
            },
        }

    def validate_nombre_usuario(self, valor):
        valor = _normalizar_texto(valor)
        if not valor:
            raise serializers.ValidationError('El nombre de usuario es obligatorio.')

        if _existe_nombre_usuario_de_otro(valor):
            raise serializers.ValidationError(
                'Ya existe una cuenta con ese nombre de usuario. '
                'Recuerde que no se distinguen las mayúsculas de las minúsculas.'
            )
        return valor

    def validate_email(self, valor):
        valor = _normalizar_texto(valor)
        if _existe_email_de_otro(valor):
            raise serializers.ValidationError(
                'Ya existe una cuenta registrada con ese correo electrónico.'
            )
        return valor

    def validate(self, attrs):
        # El validador de similitud de Django compara la contraseña contra los
        # atributos del usuario. Hay que construir una instancia con los datos
        # que ya se recibieron, o compararía contra una cuenta vacía y dejaría
        # pasar contraseñas como "mgonzales2026!" para el usuario "mgonzales".
        provisional = Usuario(
            nombre_usuario=attrs.get('nombre_usuario', ''),
            nombre_completo=attrs.get('nombre_completo', ''),
            email=attrs.get('email', ''),
        )

        errores = validar_contrasena(attrs['password'], usuario=provisional)
        if errores:
            # Se acumulan TODOS los errores de la política en un solo mensaje en
            # vez de fallar en el primero: corregir la contraseña de a un error por
            # intento es la forma más rápida de que un Administrador se rinda.
            raise serializers.ValidationError({'password': [' '.join(errores)]})

        return attrs

    def create(self, validated_data):
        # El servicio es el dueño del `set_password` y de la bitácora. Acá solo
        # se le pasa lo ya validado; ninguna regla de negocio vive en el
        # serializer más allá de la forma de los datos.
        from apps.usuarios_seguridad.users.services.usuarios import registrar_usuario

        request = self.context.get('request')
        ejecutor = request.user if request else None

        return registrar_usuario(
            datos=validated_data,
            ejecutado_por=ejecutor,
            ip=self._ip(request),
            agente=self._agente(request),
        )

    @staticmethod
    def _ip(request):
        if not request:
            return None
        reenviado = request.META.get('HTTP_X_FORWARDED_FOR')
        if reenviado:
            return reenviado.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    @staticmethod
    def _agente(request):
        if not request:
            return None
        return (request.META.get('HTTP_USER_AGENT') or '')[:255] or None


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    Edición de cuenta (`editar()`).

    La contraseña NO aparece en `fields`. Es una decisión, no un olvido: en el
    diagrama de clases `editar()` y `cambiarContrasena()` son operaciones
    distintas, y mezclarlas haría que cambiar el nombre de alguien exigiera
    escribir su clave, que es una forma de que el Administrador descubra o
    cambie la clave de otro sin haberlo planeado.

    Todos los campos son opcionales: un PATCH con un solo campo debe cambiar
    solo ese campo.
    """

    rol = serializers.CharField(source='rol_nombre', read_only=True)
    esta_bloqueado = serializers.BooleanField(source='is_bloqueado', read_only=True)
    minutos_bloqueo_restantes = serializers.IntegerField(read_only=True)
    total_permisos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = (
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'email',
            'id_rol',
            'rol',
            'activo',
            'total_permisos',
            'esta_bloqueado',
            'minutos_bloqueo_restantes',
        )
        read_only_fields = (
            'id_usuario',
            'rol',
            'total_permisos',
            'esta_bloqueado',
        )

    def validate_nombre_usuario(self, valor):
        valor = _normalizar_texto(valor)
        if not valor:
            raise serializers.ValidationError('El nombre de usuario es obligatorio.')

        if _existe_nombre_usuario_de_otro(valor, self.instance):
            raise serializers.ValidationError(
                'Ya existe otra cuenta con ese nombre de usuario. '
                'Recuerde que no se distinguen las mayúsculas de las minúsculas.'
            )
        return valor

    def validate_email(self, valor):
        valor = _normalizar_texto(valor)
        if _existe_email_de_otro(valor, self.instance):
            raise serializers.ValidationError(
                'Ese correo electrónico ya pertenece a otra cuenta.'
            )
        return valor

    def get_total_permisos(self, usuario):
        if not usuario.id_rol_id:
            return 0
        return usuario.id_rol.permisos.count()

    def update(self, instance, validated_data):
        from apps.usuarios_seguridad.users.services.usuarios import editar_usuario

        request = self.context.get('request')
        ejecutor = request.user if request else None

        return editar_usuario(
            usuario=instance,
            cambios=validated_data,
            ejecutado_por=ejecutor,
            ip=UsuarioCreateSerializer._ip(request),
            agente=UsuarioCreateSerializer._agente(request),
        )


class CambioEstadoSerializer(serializers.Serializer):
    """
    Activar / inactivar (`activar()` / `inactivar()`).

    No es un `ModelSerializer` a propósito: la operación no edita la cuenta,
    cambia su estado. Modelarlo como un serializer de campos del modelo haría
    que el endpoint aceptara un PATCH completo de datos y los aplicara por el
    camino, que es exactamente el camino lateral que este CU quiere evitar.

    `motivo` se acepta vacío y el servicio escribe "no indicado" en ese caso:
    una razón es información valiosa para quien audita, pero volverla campo
    obligatorio genera fricción sin aportar nada al sistema.
    """

    activo = serializers.BooleanField(
        write_only=True,
        required=True,
        label='Estado',
        help_text='True para activar la cuenta, False para inactivarla.',
    )
    motivo = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=200,
        label='Motivo',
    )


class RestablecerContrasenaSerializer(serializers.Serializer):
    """
    Reset administrativo de clave (`cambiarContrasena()`).

    Exige escribir la clave NUEVA dos veces, igual que hace la pantalla de CU2.
    La razón no es redundante: en un formulario de Administrador la contraseña
    se teclea a menudo con prisa y sin que nadie esté mirando, y un error de dedo
    en un campo que no se relee deja la cuenta inaccesible hasta el siguiente
    ciclo de recuperación. Confirmar el tecleo convierte un error de un segundo
    en un inconveniente de treinta segundos.
    """

    nueva_contrasena = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        trim_whitespace=False,
        style={'input_type': 'password'},
        label='Nueva contraseña',
    )
    confirmar_contrasena = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        trim_whitespace=False,
        style={'input_type': 'password'},
        label='Repetir la contraseña',
    )

    def validate_nueva_contrasena(self, valor):
        errores = validar_contrasena(valor, usuario=self.context.get('usuario'))
        if errores:
            raise serializers.ValidationError(' '.join(errores))
        return valor

    def validate(self, attrs):
        if attrs['nueva_contrasena'] != attrs['confirmar_contrasena']:
            raise serializers.ValidationError(
                {'confirmar_contrasena': 'Las contraseñas no coinciden.'}
            )
        return attrs


class RolSimpleSerializer(serializers.ModelSerializer):
    """
    Roles para el desplegable del formulario de alta y edición.

    Es un subconjunto deliberado de CU4: CU3 necesita saber QUÉ roles existen
    para poder asignar uno, pero no administra la matriz de permisos. La
    documentación completa del rol (permisos incluidos) es responsabilidad de
    CU4, y se expone en su propio endpoint.
    """

    total_permisos = serializers.SerializerMethodField()

    class Meta:
        model = Rol
        fields = ('id_rol', 'nombre', 'descripcion', 'total_permisos')
        read_only_fields = fields

    def get_total_permisos(self, rol):
        return rol.permisos.count()


__all__ = [
    'CambioEstadoSerializer',
    'RestablecerContrasenaSerializer',
    'RolSimpleSerializer',
    'UsuarioCreateSerializer',
    'UsuarioListSerializer',
    'UsuarioUpdateSerializer',
]
