"""
Servicio de emisión y validación de tokens de recuperación (CU2).

Decisiones de diseño que importan en la defensa del proyecto:

1. UN SOLO ENLACE VIGENTE POR CUENTA. Cada vez que se pide un token se invalidan
   los anteriores (`invalidar_anteriores`). Si no, un atacante que obtiene un
   enlace antiguo mantiene el acceso aunque la víctima ya haya pedido uno nuevo,
   y además el usuario recibiría varios correos válidos a la vez sin saber cuál
   es el bueno.

2. EL LÍMITE POR CUENTA SE CUENTA CON UNA CONSULTA, NO CON UN CONTADOR.
   `max_solicitudes_por_hora` se evalúa contando las filas creadas en la última
   hora. Es la inversa de la política de bloqueo de CU1, que sí acumula en una
   columna: allá el contador se reinicia con el login exitoso y no interesa el
   histórico, así que un entero alcanza. Acá el histórico ES el dato ("pedí tres
   enlaces en diez minutos"), y por eso se consulta.

3. `select_for_update()` AL RECLAMAR EL TOKEN, igual que en `politica_bloqueo`.
   Dos confirmaciones simultáneas con el mismo enlace leerían el mismo estado y
   las dos pasarían la validación; con el lock de fila el leer-evaluar-escribir
   es indivisible y la segunda encuentra el token ya usado.

4. NUNCA SE DIFIERE POR QUÉ FALLÓ UN TOKEN. `buscar_por_token` distingue los
   casos internamente para que la bitácora sea útil, pero el estado devuelto se
   traduce SIEMPRE al mismo mensaje al usuario. Un atacante que probara enlaces
   no puede usar el mensaje como oráculo para adivinar si un token existe,
   está vence o ya se usó.

5. EL LÍMITE POR IP NO ESTÁ ACÁ. Eso es throttling HTTP y lo resuelve DRF en la
   vista, con los mismos `AnonRateThrottle` que ya protegen el login. Las dos
   capas son distintas y complementarias: la de acá frena el abuso dirigido a UNA
   cuenta desde IPs rotatorias; la de DRF frena el barrido de muchas cuentas
   desde UNA IP.
"""
from dataclasses import dataclass
from datetime import timedelta
from math import ceil

from django.db import transaction
from django.db.models import Count, Min
from django.utils import timezone

from apps.usuarios_seguridad.configuracion.models import ConfiguracionSeguridad
from apps.usuarios_seguridad.recuperacion.models import TokenRecuperacion
from apps.usuarios_seguridad.users.models import Usuario

# Antigüedad máxima del User-Agent que se guarda, igual que en la bitácora.
MAX_USER_AGENT = 255

VENTANA_SOLICITUDES = timedelta(hours=1)


class EstadoToken:
    """
    Posibles resultados de validar un token. Son constantes y no un `TextChoices`
    porque NUNCA se guardan en la base de datos: son estados de una operación en
    memoria, no una categoría almacenada.
    """

    OK = 'ok'
    INEXISTENTE = 'inexistente'
    USADO = 'usado'
    INVALIDADO = 'invalidado'
    EXPIRADO = 'expirado'
    INTENTOS_AGOTADOS = 'intentos_agotados'


@dataclass(frozen=True)
class EstadoSolicitud:
    """Resultado de evaluar si la cuenta puede pedir otro enlace."""

    permitida: bool
    solicitudes_ultima_hora: int
    max_por_hora: int
    minutos_para_reintentar: int

    @property
    def mensaje_limite(self):
        """Mensaje para el usuario. No revela nada sobre la cuenta: solo sobre la IP/petición."""
        plural = 'minutos' if self.minutos_para_reintentar != 1 else 'minuto'
        return (
            f'Demasiadas solicitudes de recuperación. '
            f'Vuelve a intentar en {self.minutos_para_reintentar} {plural}.'
        )


def obtener_configuracion():
    """Punto de acceso único a la política vigente."""
    return ConfiguracionSeguridad.cargar()


def localizar_usuario(identificador):
    """
    Devuelve el usuario que corresponde a un identificador, o None.

    Acepta nombre de usuario O correo, como pide el enunciado del CU2. El correo
    se compara con `iexact` para que escribirlo en mayúsculas o minúsculas
    funcione igual, que es lo que espera cualquier persona.

    NO se filtra por `activo` acá: decidir qué hacer con una cuenta desactivada es
    responsabilidad de quien llama, y además filtrar en la consulta ocultaría las
    solicitudes ya registradas y falsearía la política de una cuenta desactivada.
    """
    identificador = (identificador or '').strip()
    if not identificador:
        return None
    return (
        Usuario.objects.filter(nombre_usuario=identificador).first()
        or Usuario.objects.filter(email__iexact=identificador).first()
    )


def evaluar_solicitud(usuario, ahora=None):
    """
    ¿Esta cuenta ya pidió demasiados enlaces en la última hora?

    Se responde con UN solo `aggregate`: el total y la fecha de la solicitud más
    antigua dentro de la ventana. Con dos consultas, la segunda podría ver un
    conjunto distinto al de la primera y el cálculo quedaría inconsistente.
    """
    ahora = ahora or timezone.now()
    config = obtener_configuracion()
    desde = ahora - VENTANA_SOLICITUDES

    resumen = TokenRecuperacion.objects.filter(
        usuario=usuario, creado_en__gte=desde
    ).aggregate(total=Count('id_token'), primera=Min('creado_en'))

    total = resumen['total'] or 0
    primera = resumen['primera']

    minutos = 0
    if primera is not None:
        faltan = (primera + VENTANA_SOLICITUDES - ahora).total_seconds() / 60
        minutos = max(0, ceil(faltan))

    return EstadoSolicitud(
        permitida=total < config.max_solicitudes_por_hora,
        solicitudes_ultima_hora=total,
        max_por_hora=config.max_solicitudes_por_hora,
        minutos_para_reintentar=minutos,
    )


def invalidar_anteriores(usuario, ahora=None):
    """
    Cancela los enlaces pendientes del usuario. Devuelve cuántos canceló.
    """
    ahora = ahora or timezone.now()
    return TokenRecuperacion.objects.filter(
        usuario=usuario,
        usado_en__isnull=True,
        invalidado_en__isnull=True,
    ).update(invalidado_en=ahora)


def crear_token(usuario, ip=None, agente=None, ahora=None):
    """
    Crea un token nuevo y cancela los anteriores.

    Devuelve la pareja `(token_en_claro, fila)`. El token en claro NO vuelve a
    existir después de esta línea: solo queda su SHA-256 en la base de datos. Por
    eso el llamador tiene que usarlo enseguida para armar el enlace del correo.
    """
    ahora = ahora or timezone.now()
    config = obtener_configuracion()
    token = TokenRecuperacion.generar_token()

    with transaction.atomic():
        invalidar_anteriores(usuario, ahora=ahora)
        fila = TokenRecuperacion.objects.create(
            usuario=usuario,
            token_hash=TokenRecuperacion.hashear_token(token),
            email_destino=usuario.email,
            creado_en=ahora,
            expira_en=ahora + timedelta(minutes=config.minutos_expiracion_token),
            intentos=0,
            ip_origen=(ip or '')[:45] or None,
            agente_usuario=(agente or '')[:MAX_USER_AGENT] or None,
        )

    return token, fila


def buscar_por_token(token, max_intentos):
    """
    Busca un token y dice en qué estado está. Devuelve `(fila_o_None, estado)`.

    Nunca lanza y jamás consulta por el token en claro: se hashea primero y se
    busca por el hash, que es el único valor que existe en la base de datos.
    """
    if not token:
        return None, EstadoToken.INEXISTENTE

    fila = TokenRecuperacion.objects.filter(
        token_hash=TokenRecuperacion.hashear_token(token.strip())
    ).first()

    if fila is None:
        return None, EstadoToken.INEXISTENTE
    if fila.esta_usado:
        return fila, EstadoToken.USADO
    if fila.esta_invalidado:
        return fila, EstadoToken.INVALIDADO
    if fila.esta_expirado:
        return fila, EstadoToken.EXPIRADO
    if fila.intentos >= max_intentos:
        return fila, EstadoToken.INTENTOS_AGOTADOS
    return fila, EstadoToken.OK


@transaction.atomic
def reclamar_token(fila, max_intentos):
    """
    Reserva el token para esta confirmación. Devuelve la fila bloqueada, o None si
    mientras tanto dejó de ser válida.

    Hace TRES cosas dentro de una sola transacción con lock de fila:

      1. relee la fila con `SELECT ... FOR UPDATE`;
      2. vuelve a evaluar la vigencia, porque entre la búsqueda inicial y este
         instante el token pudo expirar, quemarse o quedarse sin intentos;
      3. consume un intento del contador.

    El paso 2 es el que evita la carrera. Sin él, dos confirmaciones simultáneas
    con el mismo enlace pasarían ambas la validación inicial —el token todavía
    estaba bien en las dos— y las dos cambiarían la contraseña. La segunda sería
    la que quedaría, y el usuario que confirmó primero no se enteraría de que su
    clave cambió un instante después. Con el lock, la segunda transacción espera a
    que la primera escriba `usado_en` y entonces ya no encuentra un token válido.

    Al consumir el último intento disponible el token queda marcado como
    invalidado. Es redundante, porque `es_valido()` ya devuelve False con
    `intentos >= max`, pero evita que el panel muestre un enlace "pendiente" que
    en realidad está muerto.
    """
    bloqueada = TokenRecuperacion.objects.select_for_update().get(pk=fila.pk)

    if not bloqueada.es_valido(max_intentos):
        return None

    bloqueada.intentos += 1
    if bloqueada.intentos >= max_intentos and bloqueada.invalidado_en is None:
        bloqueada.invalidado_en = timezone.now()

    bloqueada.save(update_fields=['intentos', 'invalidado_en'])
    return bloqueada
