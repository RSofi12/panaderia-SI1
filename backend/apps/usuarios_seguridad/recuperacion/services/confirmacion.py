"""
Aplicación del cambio de contraseña tras validar el token (CU2).

Este módulo solo se invoca cuando el token YA fue validado por
`servicios.token.buscar_por_token` y la contraseña YA pasó el validador de
fuerza. Acá no hay decisiones: hay efectos, y todos dentro de una sola
transacción para que un fallo a la mitad no deje al usuario con la sesión
revocada pero la contraseña sin cambiar.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.recuperacion.models import TokenRecuperacion
from apps.usuarios_seguridad.recuperacion.services import token as servicio_token


def revocar_sesiones(usuario):
    """
    Manda a la lista negra todos los refresh tokens vivos del usuario.

    Esto es lo que convierte el restablecimiento en una recuperación real y no en
    un simple cambio de clave. Si alguien se había metido con la contraseña vieja,
    conservar su sesión significaría que el atacante sigue adentro aunque la
    víctima ya haya cambiado la clave. Como `BLACKLIST_AFTER_ROTATION` está
    activo en SimpleJWT, la app `token_blacklist` ya está instalada y sus tablas
    existen, así que no hay migración nueva.
    """
    ids_ya_revocados = BlacklistedToken.objects.values_list('token_id', flat=True)
    vivos = OutstandingToken.objects.filter(user=usuario).exclude(
        id__in=ids_ya_revocados
    )

    # `ignore_conflicts=True` porque el par (token, fecha) es único: si dos
    # recuperaciones se ejecutan a la vez sobre los mismos tokens, el segundo
    # INSERT no debe abortar la transacción con un error de duplicado.
    return BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=t) for t in vivos],
        ignore_conflicts=True,
    )


@transaction.atomic
def aplicar_nueva_contrasena(fila, nueva_contrasena, ip=None, agente=None):
    """
    Cambia la contraseña, quema el token, cancela el resto de enlaces, revoca las
    sesiones abiertas y deja el rastro en bitácora. Devuelve el usuario.
    """
    usuario = fila.usuario
    ahora = timezone.now()

    usuario.set_password(nueva_contrasena)

    # Al recuperar la contraseña se levanta el bloqueo vigente. Si a alguien se le
    # olvidó la contraseña justamente después de varios intentos fallidos,
    # dejarlo bloqueado sería un círculo sin salida: no puede entrar y no puede
    # recuperar.
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_intento_fallido = None
    usuario.save(update_fields=[
        'password',
        'intentos_fallidos',
        'bloqueado_hasta',
        'ultimo_intento_fallido',
    ])

    # Primero se marca ESTE token como usado, y después se cancelan los demás.
    # El orden importa: el filtro de `invalidar_anteriores` excluye los tokens ya
    # usados, así que si se invirtiera, este token quedaría marcado como
    # invalidado y no como usado, que es un dato falso en la auditoría.
    fila.usado_en = ahora
    fila.save(update_fields=['usado_en'])

    enlaces_cancelados = servicio_token.invalidar_anteriores(usuario, ahora=ahora)

    sesiones_revocadas = revocar_sesiones(usuario)

    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.RECUPERACION_CONFIRMADA,
        tabla_afectada='usuario',
        descripcion=(
            f'Contraseña restablecida mediante enlace de recuperación. '
            f'Token #{fila.id_token} usado. '
            f'Enlaces cancelados: {enlaces_cancelados}. '
            f'Sesiones revocadas: {len(sesiones_revocadas)}. IP: {ip}'
        ),
        agente_usuario=agente,
    )

    return usuario


def auditar_solicitud(usuario, identificador, correo_enviado, ip=None, agente=None):
    """
    Registra el intento de recuperación en la bitácora (CU26).

    `usuario` puede ser None: cuando la cuenta no existe no hay a quién
    atribuírselo, y el registro se hace igual con el identificador que se envía.
    Eso es justamente lo que hace útil la bitácora aquí: por fuera la respuesta es
    idéntica en todos los casos, y por dentro el Administrador ve qué correos se
    enumeraron.
    """
    if correo_enviado:
        descripcion = (
            f'Enlace de recuperación generado y enviado a {usuario.email}. IP: {ip}'
        )
    else:
        descripcion = (
            f'Solicitud de recuperación sin envío para el identificador '
            f'"{identificador}". IP: {ip}'
        )

    Bitacora.registrar(
        usuario=usuario,
        accion=AccionBitacora.SOLICITUD_RECUPERACION,
        tabla_afectada='token_recuperacion',
        descripcion=descripcion,
        nombre_usuario_intento=identificador,
        agente_usuario=agente,
    )


def auditar_token_rechazado(fila, estado, ip=None, agente=None):
    """
    Registra un enlace que no resultó válido.

    Todos los rechazos comparten la acción `RECUPERACION_INVALIDADA`: para el
    Administrador son la misma señal y así aparecen juntos en un solo filtro. El
    detalle del motivo sí queda escrito, porque para auditar sí hace falta saber
    si fue un token vencido o alguien probando suerte.
    """
    motivos = {
        servicio_token.EstadoToken.INEXISTENTE: 'el enlace no corresponde a ningún token',
        servicio_token.EstadoToken.USADO: 'el enlace ya había sido usado',
        servicio_token.EstadoToken.INVALIDADO: 'el enlace fue cancelado por pedir otro',
        servicio_token.EstadoToken.EXPIRADO: 'el enlace había expirado',
        servicio_token.EstadoToken.INTENTOS_AGOTADOS: 'se agotaron los intentos de confirmación',
    }
    # Para un token inexistente no hay fila que citar, y el identificador de la
    # fila tampoco puede escribirse como `fila.id_token` a secas: con `fila=None`
    # eso revienta con AttributeError y el rechazo —que es un caso esperado—
    # se convierte en un 500.
    referencia = f'Token #{fila.id_token}. ' if fila else 'Token no encontrado. '

    Bitacora.registrar(
        usuario=fila.usuario if fila else None,
        accion=AccionBitacora.RECUPERACION_INVALIDADA,
        tabla_afectada='token_recuperacion',
        descripcion=(
            f'Enlace de recuperación rechazado: {motivos.get(estado, estado)}. '
            f'{referencia}'
            f'Intentos registrados: {fila.intentos if fila else 0}. IP: {ip}'
        ),
        agente_usuario=agente,
    )


def purgar_vencidos(ahora=None):
    """
    Cancela los tokens vencidos que siguen marcados como pendientes.

    NO es necesario para que la seguridad funcione: `esta_expirado` ya impide
    usar un token vencido aunque la fila siga "pendiente" en la tabla. Existe
    para que el panel del Administrador no muestre tokens muertos como si fueran
    enlaces válidos, y se puede ejecutar a mano o desde un cron.
    """
    ahora = ahora or timezone.now()
    return TokenRecuperacion.objects.filter(
        usado_en__isnull=True,
        invalidado_en__isnull=True,
        expira_en__lte=ahora,
    ).update(invalidado_en=ahora)
