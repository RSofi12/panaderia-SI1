from django.db import models
from django.utils import timezone

# Los navegadores y proxies reales mandan cadenas de user-agent largas. Se corta
# antes de guardar para no depender de que la columna sea lo bastante ancha.
MAX_USER_AGENT = 255


class AccionBitacora(models.TextChoices):
    """
    Vocabulario controlado de acciones auditables (CU26).

    Antes estas acciones se escribían como cadenas sueltas en cada vista
    ('INICIO_SESION', 'LOGIN_FALLIDO', ...). Ese estilo tiene un fallo difícil de
    detectar: una errata crea una categoría nueva en lugar de fallar, así que la
    bitácora queda repartida entre 'LOGIN_FALLIDO' y 'LOGIN_FALIDO' y ningún
    reporte las agrupa. Con el enum, el error aparece al escribir el código y no al
    tres meses cuando se consulta el histórico.

    Al ser un `TextChoices`, el valor almacenado sigue siendo el texto plano
    'INICIO_SESION': los reportes y el DDL no cambian, solo se controlan las
    claves admitidas en el código Python.
    """

    INICIO_SESION = 'INICIO_SESION', 'Inicio de sesión'
    LOGIN_FALLIDO = 'LOGIN_FALLIDO', 'Intento de acceso fallido'
    ACCESO_BLOQUEADO = 'ACCESO_BLOQUEADO', 'Acceso rechazado por bloqueo'
    ACCESO_DENEGADO = 'ACCESO_DENEGADO', 'Acceso denegado por cuenta inactiva'
    CIERRE_SESION = 'CIERRE_SESION', 'Cierre de sesión'
    DESBLOQUEO_CUENTA = 'DESBLOQUEO_CUENTA', 'Desbloqueo manual de cuenta'

    # --- CU2: Recuperar contraseña ---
    # Un token vencido y un intento de fuerza bruta que agota los intentos
    # comparten acción a propósito: para el Administrador son la misma señal de
    # alerta y deben aparecer juntos en un mismo filtro.
    SOLICITUD_RECUPERACION = 'SOLICITUD_RECUPERACION', 'Solicitud de recuperación de contraseña'
    RECUPERACION_CONFIRMADA = 'RECUPERACION_CONFIRMADA', 'Contraseña restablecida por recuperación'
    RECUPERACION_INVALIDADA = 'RECUPERACION_INVALIDADA', 'Enlace de recuperación rechazado'

    # --- CU3: Gestión de usuarios ---
    # El detalle de QUÉ se cambió se escribe en la descripción, no en el nombre
    # de la acción: un enum con una entrada por cada campo editable ("cambio de
    # nombre", "cambio de correo") crecería sin límite y ningún informe lo
    # agruparía bien. Aquí la acción identifica el TIPO de operación y la
    # descripción lleva el diff.
    ALTA_USUARIO = 'ALTA_USUARIO', 'Alta de usuario'
    EDICION_USUARIO = 'EDICION_USUARIO', 'Modificación de usuario'
    CAMBIAR_ESTADO_USUARIO = 'CAMBIAR_ESTADO_USUARIO', 'Activación o inactivación de usuario'
    RESTABLECER_CONTRASENA = 'RESTABLECER_CONTRASENA', 'Restablecimiento administrativo de contraseña'

    # --- CU4: Asignar roles y permisos ---
    ALTA_ROL = 'ALTA_ROL', 'Alta de rol'
    EDICION_ROL = 'EDICION_ROL', 'Modificación de rol'
    ASIGNAR_PERMISO_ROL = 'ASIGNAR_PERMISO_ROL', 'Asignación de permiso a rol'
    REVOCAR_PERMISO_ROL = 'REVOCAR_PERMISO_ROL', 'Revocación de permiso de rol'
    ACTUALIZACION_MATRIZ_PERMISOS = 'ACTUALIZACION_MATRIZ_PERMISOS', 'Reemplazo masivo de matriz de permisos'


class Bitacora(models.Model):
    """
    Modelo de Auditoría del Sistema para Panadería Santiago.
    Registra todas las acciones críticas (CU26).
    """
    id_bitacora = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        'users.Usuario',
        on_delete=models.SET_NULL,
        db_column='id_usuario',
        null=True,
        blank=True,
        related_name='bitacoras',
        verbose_name='Usuario responsable',
        help_text='Null cuando el evento no proviene de un usuario autenticado.'
    )
    nombre_usuario_intento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Usuario intentado',
        help_text='Nombre de usuario digitado en un intento de acceso fallido.'
    )
    accion = models.CharField(
        max_length=50,
        choices=AccionBitacora.choices,
        verbose_name='Acción realizada'
    )
    tabla_afectada = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Tabla o Módulo afectado'
    )
    agente_usuario = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Agente de usuario (navegador)',
        help_text='User-Agent del cliente. Ayuda a distinguir un ataque automatizado de un humano.'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Detalle de la acción'
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y hora'
    )

    class Meta:
        db_table = 'bitacora'
        verbose_name = 'Bitácora de Auditoría'
        verbose_name_plural = 'Bitácoras de Auditoría'
        ordering = ['-fecha_hora']

    def __str__(self):
        actor = self.usuario.nombre_usuario if self.usuario_id else (self.nombre_usuario_intento or 'anónimo')
        return f'[{self.fecha_hora.strftime("%Y-%m-%d %H:%M")}] {actor} - {self.accion}'

    @classmethod
    def registrar(cls, usuario=None, accion='', tabla_afectada=None, descripcion=None,
                  nombre_usuario_intento=None, agente_usuario=None):
        """
        Utilitario para registrar un evento desde cualquier vista o servicio.

        A diferencia de la versión anterior, `usuario` puede ser None: un intento
        de acceso fallido ocurre justamente cuando NADIE está autenticado, y si
        se exigiera un usuario la bitácora descartaba en silencio justo los
        eventos más importantes para detectar un ataque de fuerza bruta. En ese
        caso se conserva el nombre de usuario digitado en
        `nombre_usuario_intento`, para poder correlacionar sin autenticar.
        """
        if isinstance(agente_usuario, str) and len(agente_usuario) > MAX_USER_AGENT:
            agente_usuario = agente_usuario[:MAX_USER_AGENT]

        return cls.objects.create(
            usuario=usuario if (usuario and usuario.is_authenticated) else None,
            nombre_usuario_intento=nombre_usuario_intento,
            accion=accion,
            tabla_afectada=tabla_afectada,
            descripcion=descripcion,
            agente_usuario=agente_usuario,
        )
