"""
Servicio de política de bloqueo por intentos fallidos (CU1).

ESTA ES LA RESPUESTA A "¿dónde se guarda esa lógica?".
No está en la vista, ni en el serializador, ni en settings.py: está acá, en la
capa de servicio, porque la lógica de negocio debe poder probarse sin levantar
HTTP.

Decisiones de diseño que importan en la defensa del proyecto:

1. El bloqueo se resuelve de forma PEREZOSA. No hay cron ni tarea programada:
   cada vez que se evalúa la política se pregunta "¿la ventana ya venció?". Si
   venció, se limpia en el mismo momento. Esto evita depender de un scheduler
   que en un despliegue local puede no estar corriendo.

2. El conteo de intentos se hace con `select_for_update()` DENTRO de una
   transacción, no con `objeto.intentos_fallidos += 1; objeto.save()`. La
   diferencia importa: `F()` hacía atómico SOLO el `UPDATE` del contador, pero la
   comparación con el umbral (`if intentos >= max`) ocurría en una consulta
   aparte. Con dos contraseñas incorrectas simultáneas contra la misma cuenta,
   ambas leían el mismo contador y ambas decidían "todavía no llego al umbral":
   el bloqueo se atrasaba un intento. `select_for_update()` le pide a PostgreSQL
   un lock de fila (`SELECT ... FOR UPDATE`), de modo que el leer-modificar-
   escribir completo es indivisible y los dos intentos se cuentan uno tras otro.

3. El reloj es `timezone.now()`, que respeta el TIME_ZONE del proyecto.
   Nunca se usa datetime.now().

4. El tiempo restante se devuelve en SEGUNDOS, no en minutos. La ventana se
   configura en minutos, pero el frontend necesita un contador regresivo real, y
   redondeando a minutos un bloqueo de 60 segundos se comunicaría como "1 minuto"
   aunque quedaran 2.

5. Nunca se revela al cliente cuántos intentos le quedan. Decir "te quedan 2
   intentos" confirma que la cuenta existe y permite calibrar un ataque. Solo se
   comunica el bloqueo consumado.
"""
from dataclasses import dataclass
from datetime import timedelta
from math import ceil

from django.db import transaction
from django.utils import timezone

from apps.usuarios_seguridad.configuracion.models import ConfiguracionSeguridad
from apps.usuarios_seguridad.users.models import Usuario


def _segundos_que_faltan(hasta, ahora):
    """
    Segundos que faltan para que expire la ventana, redondeados hacia ARRIBA.

    El redondeo hacia arriba importa: entre que se guarda `bloqueado_hasta` y se
    calcula este valor pasan unos microsegundos, así que el tiempo real restante
    es 599.98 s y un truncado informaría "reintenta en 599 s". El usuario
    obedecería, reintentaría un segundo antes de tiempo y recibiría otro 429 sin
    entender por qué. Redondear hacia arriba nunca le pide esperar de más.
    """
    if not hasta:
        return 0
    return max(0, ceil((hasta - ahora).total_seconds()))


@dataclass(frozen=True)
class EstadoBloqueo:
    """Resultado de evaluar la política. Inmutable porque es una lectura."""

    bloqueado: bool
    segundos_restantes: int
    intentos_fallidos: int
    max_intentos: int
    intentos_restantes: int

    @property
    def minutos_restantes(self):
        """
        Redondeo al alza para el mensaje en texto. Se conserva como propiedad para
        no cambiar los call sites que ya lo usan; la precisión real vive en
        `segundos_restantes`.
        """
        if self.segundos_restantes <= 0:
            return 0
        return (self.segundos_restantes + 59) // 60

    @property
    def mensaje_bloqueo(self):
        """Mensaje para el usuario final. Nunca incluye datos sensibles."""
        if not self.bloqueado:
            return ''
        plural = 'minutos' if self.minutos_restantes != 1 else 'minuto'
        return (
            f'Cuenta bloqueada temporalmente por intentos fallidos. '
            f'Vuelve a intentar en {self.minutos_restantes} {plural}.'
        )


def _estado_bloqueado(segundos, intentos_fallidos, config):
    return EstadoBloqueo(
        bloqueado=True,
        segundos_restantes=max(1, int(segundos)),
        intentos_fallidos=intentos_fallidos,
        max_intentos=config.max_intentos_fallidos,
        intentos_restantes=0,
    )


def _estado_libre(intentos_fallidos, config):
    return EstadoBloqueo(
        bloqueado=False,
        segundos_restantes=0,
        intentos_fallidos=intentos_fallidos,
        max_intentos=config.max_intentos_fallidos,
        intentos_restantes=max(0, config.max_intentos_fallidos - intentos_fallidos),
    )


def obtener_configuracion():
    """Punto de acceso único a la política vigente."""
    return ConfiguracionSeguridad.cargar()


def _limpiar_bloqueo_vencido(usuario):
    """
    Si la ventana de bloqueo ya expiró, la libero en el acto.
    Devuelve True si efectivamente había un bloqueo vencido.
    """
    if not usuario.bloqueado_hasta:
        return False

    if usuario.bloqueado_hasta > timezone.now():
        return False

    Usuario.objects.filter(pk=usuario.pk).update(
        bloqueado_hasta=None,
        intentos_fallidos=0,
    )
    usuario.bloqueado_hasta = None
    usuario.intentos_fallidos = 0
    return True


def evaluar_bloqueo(usuario):
    """
    Punto de entrada de solo lectura. Responde: ¿esta cuenta puede intentar
    autenticarse ahora mismo?

    No escribe en la base de datos salvo que encuentre un bloqueo vencido, que
    es justamente el momento de limpiarlo.
    """
    _limpiar_bloqueo_vencido(usuario)

    config = obtener_configuracion()

    if usuario.bloqueado_hasta:
        segundos = _segundos_que_faltan(usuario.bloqueado_hasta, timezone.now())
        if segundos > 0:
            return _estado_bloqueado(segundos, usuario.intentos_fallidos, config)

    return _estado_libre(usuario.intentos_fallidos, config)


def registrar_intento_fallido(usuario):
    """
    Suma un intento fallido y, si alcanza el umbral, abre la ventana de bloqueo.

    Devuelve el EstadoBloqueo resultante para que el serializador decida si
    responde 400 (todavía hay margen) o 429 (cuenta bloqueada).
    """
    config = obtener_configuracion()
    ahora = timezone.now()

    with transaction.atomic():
        # El lock de fila es el corazón del parche: desde aquí hasta el save(),
        # ninguna otra petición concurrente sobre esta misma cuenta puede leer ni
        # escribir el contador. Con F() el incremento era atómico pero la decisión
        # de abrir el bloqueo no lo era.
        fila = Usuario.objects.select_for_update().filter(pk=usuario.pk).first()

        if fila is None:
            # La cuenta se borró entre la búsqueda en el serializador y este
            # conteo. No hay nada que bloquear ni a quién avisarle.
            return _estado_libre(0, config)

        # La ventana anterior ya venció: el contador arranca de cero.
        if fila.bloqueado_hasta and fila.bloqueado_hasta <= ahora:
            fila.bloqueado_hasta = None
            fila.intentos_fallidos = 0

        # Ya está bloqueado y la ventana sigue vigente. No se cuenta otro intento
        # porque el umbral no volvería a alcanzarse nunca; solo se informa cuánto
        # falta para que expire.
        if fila.bloqueado_hasta and fila.bloqueado_hasta > ahora:
            segundos = _segundos_que_faltan(fila.bloqueado_hasta, ahora)
            _reflejar_en_memoria(usuario, fila)
            return _estado_bloqueado(segundos, fila.intentos_fallidos, config)

        fila.intentos_fallidos += 1
        fila.ultimo_intento_fallido = ahora

        segundos = 0
        if fila.intentos_fallidos >= config.max_intentos_fallidos:
            fila.bloqueado_hasta = ahora + timedelta(minutes=config.minutos_bloqueo)
            segundos = _segundos_que_faltan(fila.bloqueado_hasta, ahora)

        fila.save(update_fields=[
            'intentos_fallidos',
            'bloqueado_hasta',
            'ultimo_intento_fallido',
        ])

        _reflejar_en_memoria(usuario, fila)
        intentos = fila.intentos_fallidos

    if segundos:
        return _estado_bloqueado(segundos, intentos, config)
    return _estado_libre(intentos, config)


def _reflejar_en_memoria(usuario, fila):
    """
    Copia el estado bloqueado de la fila ya bloqueada hacia el objeto que el
    serializador tiene en mano, para que /me/ y los mensajes siguientes coincidan
    con lo recién escrito.
    """
    usuario.intentos_fallidos = fila.intentos_fallidos
    usuario.bloqueado_hasta = fila.bloqueado_hasta
    usuario.ultimo_intento_fallido = fila.ultimo_intento_fallido


def registrar_intento_exitoso(usuario):
    """
    Login correcto: se reinicia el contador y se marca el último acceso.
    `last_login` se actualiza a mano porque el flujo JWT de DRF nunca entra por
    django.contrib.auth.login(), que es lo que dispara la señal update_last_login.
    """
    ahora = timezone.now()
    Usuario.objects.filter(pk=usuario.pk).update(
        intentos_fallidos=0,
        bloqueado_hasta=None,
        ultimo_intento_fallido=None,
        last_login=ahora,
    )
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.last_login = ahora


def desbloquear_usuario(usuario, motivo='Desbloqueo manual', ejecutado_por=None):
    """
    Uso administrativo: limpia el bloqueo sin esperar a que venza la ventana.
    El dashboard del Administrador consumirá este servicio más adelante.
    """
    Usuario.objects.filter(pk=usuario.pk).update(
        intentos_fallidos=0,
        bloqueado_hasta=None,
        ultimo_intento_fallido=None,
    )
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_intento_fallido = None

    from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
    Bitacora.registrar(
        usuario=ejecutado_por,
        accion=AccionBitacora.DESBLOQUEO_CUENTA,
        tabla_afectada='usuario',
        descripcion=(
            f'Cuenta desbloqueada: {usuario.nombre_usuario}. Motivo: {motivo}.'
        ),
    )
