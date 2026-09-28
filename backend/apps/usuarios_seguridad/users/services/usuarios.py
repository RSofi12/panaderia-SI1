"""
Servicios de administración de cuentas (CU3 — Gestionar usuarios).

ESTE ES EL MOTIVO DE QUE EXISTA UNA CAPA DE SERVICIO, y vale la pena poder
explicarlo en la defensa: la lógica de negocio del CU3 no vive ni en la vista
ni en el serializador. Vive acá, para poder probarla sin levantar HTTP y para
que el panel de Django y la API compartan exactamente las mismas reglas.

Reglas del CU3 tal como las define el proyecto:

1. **No existe el borrado.** El caso de uso dice "registro, edición, activación
   e inactivación" (`backend/apps/PACKAGE_CU_MAP.md`), y el diagrama de clases
   define `activar()` e `inactivar()` pero no `eliminar()`. La baja es
   `activo = false`. La razón es de integridad: `usuario` es referenciado por
   `bitacora`, `token_recuperacion`, `pedido`, `venta`, `compra`, `produccion` y
   `movimiento_economico`. Un DELETE físico destruiría el historial económico de
   la panadería y dejaría la auditoría sin autor.

2. **Cambiar el estado o el rol revoca las sesiones abiertas.** El JWT lleva
   `rol` y `permisos` como *claims* (`auth_app/serializers.py`, `get_token`).
   Eso significa que un access token válido sigue afirmando el rol anterior
   durante toda su vida, que por defecto son 60 minutos. Si el Administrador
   inactiva a un usuario o le cambia el rol y no se le revocan los tokens, la
   medida no surte efecto hasta que el token caduque. Se revoca con el mismo
   servicio que ya usa CU2 (`recuperacion.services.confirmacion`), porque
    revocar es revocar, y escribirlo dos veces garantiza que un día las copias
   divergan.

3. **La contraseña nunca viaja ni se guarda en claro.** Entra por el serializer,
   pasa por `validar_contrasena()` y sale de acá como hash. Los servicios no
   registran contraseñas en la bitácora, ni siquiera dentro de la descripción.

4. **Tres guardas de auto-destrucción.** Un Administrador puede, sin querer,
   quedarse sin sistema: inactivándose a sí mismo, quitándose su propio rol, o
   inactivando al último Administrador activo. Ninguna de las tres es un descuido
   del usuario; las tres son consecuencias previsibles de una operación
   legítima. Se bloquean acá y no en el frontend, porque ocultar un botón es
    usabilidad, no seguridad: la API tiene que rechazar el intento aunque llegue
    por curl.

    Un cuarto detalle: las guardas preguntan por el ROL DE NEGOCIO
    ("Administrador"), no por `is_superuser`. Son dos conceptos distintos en
    este proyecto y confundirlos haría que un superusuario de mantenimiento,
    que existe para atender el panel técnico de Django, contara como respaldo
    administrativo de la API. Y no lo es.
"""
from django.db import transaction

from apps.usuarios_seguridad.auth_app.services import politica_bloqueo
from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.recuperacion.services.confirmacion import revocar_sesiones
from apps.usuarios_seguridad.users.exceptions import OperacionInvalidaError
from apps.usuarios_seguridad.users.models import Usuario
from apps.usuarios_seguridad.users.permissions import EsAdministrador

#: Campos que el Administrador puede modificar en una cuenta existente, y que
#: por lo tanto se copian al texto de auditoría. La lista es explícita a
#: propósito: si mañana `editar()` acepta un campo más, hay que agregarlo aquí
#: también, y ese es exactamente el recordatorio que impide que un campo
#: sensible termine en la bitácora por descuido.
CAMPOS_AUDITADOS = ('nombre_usuario', 'nombre_completo', 'email', 'id_rol')


# ==================================================================
# Guardas de auto-destrucción
# ==================================================================


def _es_administrador_activo(usuario):
    """¿La cuenta es, ahora mismo, un Administrador con acceso activo?"""
    return bool(usuario.activo and usuario.id_rol_id == _id_rol_administrador())


def _id_rol_administrador():
    """Id del rol "Administrador", o None si la fila de rol aún no existe."""
    from apps.usuarios_seguridad.roles.models import Rol

    return Rol.objects.filter(nombre=EsAdministrador.ROL_ADMINISTRADOR)\
        .values_list('id_rol', flat=True).first()


def _hay_otros_administradores_activos(usuario):
    """
    ¿Existe algún Administrador activo además de este usuario?

    La pregunta es por los OTROS, no por el conjunto entero: si el Administrador
    #1 es el único y se inactiva a sí mismo, la respuesta debe ser False.
    """
    id_rol = _id_rol_administrador()
    if id_rol is None:
        return False

    return (
        Usuario.objects.filter(id_rol_id=id_rol, activo=True)
        .exclude(pk=usuario.pk)
        .exists()
    )


def _validar_no_auto_inactivar(usuario, ejecutado_por, nuevo_estado):
    """
    Un Administrador no puede desactivar su propia cuenta.

    Sin esta guarda, un clic de más deja el sistema entero sin administración:
    la cuenta que queda inactiva es la única que podría reactivarla.
    """
    if not nuevo_estado and usuario.pk == getattr(ejecutado_por, 'pk', None):
        raise OperacionInvalidaError(
            'No puede desactivar su propia cuenta. '
            'Pídale a otro Administrador que lo haga.'
        )


def _validar_no_quitar_propio_rol(usuario, ejecutado_por, nuevo_rol_id):
    """
    Un Administrador no puede quitarse su propio rol.

    `id_rol` admite NULL, así que el sistema lo permite: un usuario sin rol es
    alguien que entra al panel y no ve ningún módulo. Si ese usuario es el que
    está ejecutando la operación, se queda fuera sin poder recuperar el rol,
    porque el permiso que está cediendo (`gestionar_usuarios`) es justamente el
    que hace falta para devolvérselo.
    """
    if nuevo_rol_id is None and usuario.pk == getattr(ejecutado_por, 'pk', None):
        raise OperacionInvalidaError(
            'No puede quitarse su propio rol. Así se quedaría sin permisos '
            'para volver a asignárselo.'
        )


def _validar_queda_algun_administrador(usuario, era_admin_activo, nuevo_estado, nuevo_rol_id):
    """
    No se puede dejar el sistema sin ningún Administrador activo.

    Solo se evalúa si la cuenta ERA un Administrador activo antes del cambio. Sin
    ese filtro, desactivar a un vendedor de una panadería que por error
    quedó sin administradores sería bloqueado, cuando en realidad no es una
    pérdida: la cuenta que falta no era la del administrador.

    Se cubre el caso en que la cuenta deje de ser administradora por las dos
    vías posibles a la vez: que se desactive, o que se le quite el rol.
    """
    if not era_admin_activo:
        return

    deja_de_ser_admin = (
        not nuevo_estado
        or nuevo_rol_id != _id_rol_administrador()
    )
    if not deja_de_ser_admin:
        return

    if not _hay_otros_administradores_activos(usuario):
        raise OperacionInvalidaError(
            'La operación dejaría al sistema sin ningún Administrador activo. '
            'Cree o active primero otra cuenta con el rol Administrador.'
        )


def _pk_de_rol(valor):
    """
    Normaliza a id de rol lo que llega del serializer.

    Hace falta porque DRF, para un `ForeignKey`, mete en `validated_data` la
    INSTANCIA del objeto relacionado, no su clave primaria. Es la clase de
    detalle que solo aparece al ejecutar: `create_user(id_rol=<Rol: Personal de
    Ventas>)` levanta `TypeError: int() argument must be ... not 'Rol'`, porque
    `id_rol_id` espera un entero.

    La función acepta las tres formas que pueden aparecer —`Rol`, entero o
    `None`— para que la capa de servicio no dependa de cómo serializó DRF hoy.
    Aceptar más de una forma no es tolerancia por pereza: es la frontera entre
    "esto es HTTP" y "esto es negocio", y acá empieza el negocio.
    """
    if valor is None:
        return None
    return getattr(valor, 'pk', valor)


# ==================================================================
# Utilidades de auditoría
# ==================================================================


def _describir_cambios(anterior, cambios):
    """
    Arma el texto "campo: valor viejo -> valor nuevo" de una modificación.

    Se compara contra el estado que tenía la cuenta ANTES de aplicar el cambio.
    El texto es lo que le permite al Administrador responder "¿quién me cambió
    el correo y a qué hora?" sin consultar la tabla `usuario`, que solo muestra
    el valor final.
    """
    partes = []

    for campo in CAMPOS_AUDITADOS:
        if campo not in cambios:
            continue

        valor_anterior = anterior.get(campo)
        valor_nuevo = cambios[campo]

        if valor_anterior == valor_nuevo:
            continue

        partes.append(f'{campo}: "{valor_anterior}" -> "{valor_nuevo}"')

    return '; '.join(partes) if partes else 'sin cambios de datos'


# ==================================================================
# Operaciones del CU3
# ==================================================================


@transaction.atomic
def registrar_usuario(datos, ejecutado_por, ip=None, agente=None):
    """
    Alta de una cuenta nueva (`registrar()` del diagrama de clases).

    `datos` es un diccionario YA validado por el serializer: acá no se vuelve a
    validar, solo se aplica. Esa separación es deliberada. La validación vive en
    la capa de presentación porque su salida (errores por campo) la consume el
    formulario; esta capa asume que lo que le entregan ya pasó el filtro.

    La contraseña se descarta al terminar: no se devuelve, no se registra y no
    se guarda en ninguna variable que outlive a la función.
    """
    usuario = Usuario(
        nombre_usuario=datos['nombre_usuario'],
        nombre_completo=datos['nombre_completo'],
        email=datos['email'],
        id_rol_id=_pk_de_rol(datos.get('id_rol')),
        activo=datos.get('activo', True),
    )
    # `set_password` y nunca `password = ...`: es el único camino que aplica el
    # hash. Asignar el texto plano crearía una cuenta que nadie puede
    # autenticar y además dejaría la contraseña legible en la base de datos.
    usuario.set_password(datos['password'])
    usuario.save()

    Bitacora.registrar(
        usuario=ejecutado_por,
        accion=AccionBitacora.ALTA_USUARIO,
        tabla_afectada='usuario',
        descripcion=(
            f'Alta de la cuenta "{usuario.nombre_usuario}" '
            f'({usuario.email}) con el rol "{usuario.rol_nombre}". '
            f'Cuenta activa: {usuario.activo}. IP: {ip}'
        ),
        agente_usuario=agente,
    )

    return usuario


@transaction.atomic
def editar_usuario(usuario, cambios, ejecutado_por, ip=None, agente=None):
    """
    Modificación de datos de una cuenta existente (`editar()`).

    Recibe `cambios`: solo los campos que el serializer marcó como modificados.
    No se reescribe lo que el Administrador no envió, porque en un PATCH vacío
    de datos la respuesta correcta es "no hice nada", no "borré todo lo que no
    venía en el cuerpo".

    La contraseña NO se toca acá. Tiene su propia operación,
    `restablecer_contrasena`, porque son decisiones distintas: editar el nombre
    de alguien no debería exigir ni volver a escribir su clave, y auditar dos
    hechos en un solo registro vuelve la bitácora menos útil, no más.
    """
    anterior = {campo: getattr(usuario, campo, None) for campo in CAMPOS_AUDITADOS}
    era_admin_activo = _es_administrador_activo(usuario)

    # Todo se compara y se guarda por CLAVE PRIMARIA, nunca por la instancia.
    # Si `nuevo_rol_id` fuera un `Rol`, la comparación contra el id del rol
    # Administrador sería siempre falsa y la guarda "no dejes el sistema sin
    # Administradores" dispararía en cada edición de una cuenta que sí tenía rol.
    # Es un bug que no se ve leyendo el código, solo ejecutándolo.
    nuevo_rol_id = (
        _pk_de_rol(cambios['id_rol']) if 'id_rol' in cambios else usuario.id_rol_id
    )
    nuevo_estado = cambios.get('activo', usuario.activo)

    # Las guardas se evalúan ANTES de tocar nada, para que un rechazo no deje la
    # cuenta a medio camino dentro de la transacción.
    _validar_no_quitar_propio_rol(usuario, ejecutado_por, nuevo_rol_id)
    _validar_no_auto_inactivar(usuario, ejecutado_por, nuevo_estado)
    _validar_queda_algun_administrador(
        usuario, era_admin_activo, nuevo_estado, nuevo_rol_id
    )

    cambio_de_rol = 'id_rol' in cambios and nuevo_rol_id != usuario.id_rol_id
    deactivate = 'activo' in cambios and cambios['activo'] is False and usuario.activo

    for campo, valor in cambios.items():
        if campo == 'id_rol':
            # Asignar por `id_rol_id` y no por `id_rol` fuerza a que Django
            # descarte el objeto relacionado cacheado. Si se asignara la
            # instancia, `usuario.rol_nombre` seguiría devolviendo el nombre
            # del rol ANTERIOR y la bitácora escribiría el valor viejo.
            usuario.id_rol_id = nuevo_rol_id
            continue
        setattr(usuario, campo, valor)
    usuario.save()

    # El token del usuario sigue afirmando el rol y el estado anteriores. Sin
    # revocarlo, el cambio no se refleja hasta que caduque el access token.
    revocados = 0
    if cambio_de_rol or deactivate:
        revocados = len(revocar_sesiones(usuario))

    descripcion = _describir_cambios(anterior, cambios)
    if cambio_de_rol:
        descripcion += (
            f'. Cambio de rol a "{usuario.rol_nombre}"; '
            f'sesiones revocadas: {revocados}'
        )
    elif deactivate:
        descripcion += f'. Cuenta inactivada; sesiones revocadas: {revocados}'

    Bitacora.registrar(
        usuario=ejecutado_por,
        accion=AccionBitacora.EDICION_USUARIO,
        tabla_afectada='usuario',
        descripcion=(
            f'Modificación de la cuenta "{usuario.nombre_usuario}": '
            f'{descripcion}. IP: {ip}'
        ),
        agente_usuario=agente,
    )

    return usuario


@transaction.atomic
def cambiar_estado(usuario, nuevo_estado, ejecutado_por, motivo=None, ip=None):
    """
    Activación o inactivación de una cuenta (`activar()` / `inactivar()`).

    Inactivar REVOCA las sesiones abiertas. Sin eso, un usuario al que se le dio
    de baja seguiría pudiendo operar con el access token que ya tenía, hasta 60
    minutos después de que el Administrador cerró la cuenta.
    """
    if usuario.activo == nuevo_estado:
        raise OperacionInvalidaError(
            f'La cuenta "{usuario.nombre_usuario}" ya está '
            f'{"activa" if nuevo_estado else "inactivada"}.'
        )

    era_admin_activo = _es_administrador_activo(usuario)

    _validar_no_auto_inactivar(usuario, ejecutado_por, nuevo_estado)
    _validar_queda_algun_administrador(
        usuario, era_admin_activo, nuevo_estado, usuario.id_rol_id
    )

    estado_anterior = usuario.activo
    usuario.activo = nuevo_estado

    # Al reactivar una cuenta que estaba bloqueada por intentos fallidos, el
    # bloqueo se levanta. Si no, el Administrador la reactiva y el usuario sigue
    # sin poder entrar hasta que venza la ventana, sin entender por qué.
    bloqueo_limpiado = False
    if nuevo_estado and usuario.bloqueado_hasta:
        politica_bloqueo.desbloquear_usuario(
            usuario,
            motivo='Reactivación de la cuenta por el Administrador',
            ejecutado_por=ejecutado_por,
        )
        bloqueo_limpiado = True

    usuario.save(update_fields=['activo'])

    revocados = 0
    if not nuevo_estado:
        revocados = len(revocar_sesiones(usuario))

    Bitacora.registrar(
        usuario=ejecutado_por,
        accion=AccionBitacora.CAMBIAR_ESTADO_USUARIO,
        tabla_afectada='usuario',
        descripcion=(
            f'Cuenta "{usuario.nombre_usuario}" '
            f'{"activada" if nuevo_estado else "inactivada"}. '
            f'Estado anterior: {"activo" if estado_anterior else "inactivo"}. '
            f'Sesiones revocadas: {revocados}. '
            f'Bloqueo limpiado: {bloqueo_limpiado}. '
            f'Motivo: {motivo or "no indicado"}. IP: {ip}'
        ),
    )

    return usuario


@transaction.atomic
def restablecer_contrasena(usuario, nueva_contrasena, ejecutado_por, ip=None, agente=None):
    """
    Restablecimiento administrativo de contraseña (`cambiarContrasena()`).

    Es la contra parte del CU2 desde el otro lado: en CU2 el usuario demuestra
    ser el dueño del buzón; acá quien decide es el Administrador.

    Revoca las sesiones por la misma razón que inactivar: cambiar la contraseña
    de una cuenta que alguien más está usando tiene que cerrar esa sesión. Si no,
    la clave nueva no protege nada, porque la sesión vieja sigue viva.
    """
    usuario.set_password(nueva_contrasena)

    # La cuenta queda utilizable. No tiene sentido "restablecer" una clave y
    # dejar la cuenta bloqueada por intentos fallidos: quedaría con una
    # contraseña nueva que no puede usar.
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_intento_fallido = None
    usuario.save(update_fields=[
        'password',
        'intentos_fallidos',
        'bloqueado_hasta',
        'ultimo_intento_fallido',
    ])

    revocados = len(revocar_sesiones(usuario))

    Bitacora.registrar(
        usuario=ejecutado_por,
        accion=AccionBitacora.RESTABLECER_CONTRASENA,
        tabla_afectada='usuario',
        descripcion=(
            f'Contraseña restablecida por el Administrador para la cuenta '
            f'"{usuario.nombre_usuario}". Sesiones revocadas: {revocados}. '
            f'La contraseña NO se registra en la bitácora. IP: {ip}'
        ),
        agente_usuario=agente,
    )

    return usuario


def desbloquear_cuenta(usuario, ejecutado_por, motivo='Desbloqueo solicitado por el Administrador'):
    """
    Levanta el bloqueo por intentos fallidos sin esperar a que venza la ventana.

    Es la exposición de `politica_bloqueo.desbloquear_usuario`, que se escribió
    en CU1 con la intención explícita de que el panel del Administrador lo
    consumiera. Se delega en vez de reescribirse: la regla de cuándo una cuenta
    está bloqueada ya está probada y auditada, y duplicarla garantizaría que las
    dos copias divergan algún día.

    `desbloquear_usuario` escribe su propio registro de bitácora
    (`DESBLOQUEO_CUENTA`), así que esta operación deja una sola entrada y no
    dos: es un hecho, no dos.
    """
    if not usuario.is_bloqueado:
        raise OperacionInvalidaError(
            f'La cuenta "{usuario.nombre_usuario}" no está bloqueada.'
        )

    politica_bloqueo.desbloquear_usuario(
        usuario,
        motivo=motivo,
        ejecutado_por=ejecutado_por,
    )

    # Se devuelve el usuario y no el resultado de `desbloquear_usuario`, que
    # escribe con `.update()` y no devuelve nada. La vista lo serializa para
    # devolver el estado ya refrescado en la misma respuesta.
    return usuario
