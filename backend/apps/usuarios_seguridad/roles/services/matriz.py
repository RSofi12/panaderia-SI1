"""
Lógica de negocio y servicios para la matriz de Roles y Permisos (CU4).

Garantiza:
1. Operaciones atómicas bajo @transaction.atomic.
2. Inmutabilidad de los nombres de roles protegidos del sistema.
3. Guardas anti-autobloqueo: impedir revocar 'asignar_permisos' del rol Administrador
   o del rol del usuario que ejecuta la petición.
4. Registro estricto de auditoría en la tabla Bitacora con el diff exacto de cambios.
"""
from django.db import transaction
from django.db.models.functions import Lower

from apps.usuarios_seguridad.bitacora.models import AccionBitacora, Bitacora
from apps.usuarios_seguridad.permisos.models import Permiso
from apps.usuarios_seguridad.roles.constants import (
    PERMISO_CU4,
    ROL_ADMINISTRADOR,
    ROLES_PROTEGIDOS,
)
from apps.usuarios_seguridad.roles.exceptions import OperacionInvalidaError
from apps.usuarios_seguridad.roles.models import Rol, RolPermiso


def _registrar_bitacora(accion, descripcion, ejecutado_por=None, ip=None, agente=None, tabla_afectada='rol_permiso'):
    """Registra de forma segura un evento en la bitácora del sistema."""
    usuario_id = getattr(ejecutado_por, 'pk', None)
    Bitacora.objects.create(
        usuario_id=usuario_id,
        accion=accion,
        tabla_afectada=tabla_afectada,
        descripcion=descripcion,
        agente_usuario=(agente or '')[:255] or None,
    )


@transaction.atomic
def crear_rol(nombre, descripcion=None, ejecutado_por=None, ip=None, agente=None):
    """
    Crea un nuevo rol en el sistema.
    Valida unicidad insensible a mayúsculas y audita en Bitácora.
    """
    nombre_limpio = (nombre or '').strip()
    if not nombre_limpio:
        raise OperacionInvalidaError('El nombre del rol es obligatorio.')

    if Rol.objects.annotate(nombre_lower=Lower('nombre')).filter(nombre_lower=nombre_limpio.lower()).exists():
        raise OperacionInvalidaError(f'Ya existe un rol con el nombre "{nombre_limpio}" (no distingue mayúsculas).')

    rol = Rol.objects.create(
        nombre=nombre_limpio,
        descripcion=(descripcion or '').strip() or None,
    )

    _registrar_bitacora(
        accion=AccionBitacora.ALTA_ROL,
        tabla_afectada='rol',
        descripcion=f'Se creó el rol "{rol.nombre}" (ID: {rol.id_rol}).',
        ejecutado_por=ejecutado_por,
        ip=ip,
        agente=agente,
    )
    return rol


@transaction.atomic
def editar_rol(rol, datos, ejecutado_por=None, ip=None, agente=None):
    """
    Edita un rol existente.
    Protege los roles base del sistema contra cambios de nombre.
    """
    cambios = []
    nuevo_nombre = datos.get('nombre')
    if nuevo_nombre is not None:
        nuevo_nombre = nuevo_nombre.strip()
        if nuevo_nombre != rol.nombre:
            if rol.nombre in ROLES_PROTEGIDOS:
                raise OperacionInvalidaError(
                    f'El rol "{rol.nombre}" es un rol protegido del sistema y su nombre no puede ser modificado.'
                )
            if not nuevo_nombre:
                raise OperacionInvalidaError('El nombre del rol no puede quedar vacío.')
            if Rol.objects.annotate(nombre_lower=Lower('nombre')).filter(nombre_lower=nuevo_nombre.lower()).exclude(pk=rol.pk).exists():
                raise OperacionInvalidaError(f'Ya existe otro rol con el nombre "{nuevo_nombre}".')
            cambios.append(f'nombre: "{rol.nombre}" -> "{nuevo_nombre}"')
            rol.nombre = nuevo_nombre

    if 'descripcion' in datos:
        nueva_desc = (datos.get('descripcion') or '').strip() or None
        if nueva_desc != rol.descripcion:
            cambios.append(f'descripcion actualizada')
            rol.descripcion = nueva_desc

    if cambios:
        rol.save()
        _registrar_bitacora(
            accion=AccionBitacora.EDICION_ROL,
            tabla_afectada='rol',
            descripcion=f'Se modificó el rol "{rol.nombre}": {", ".join(cambios)}.',
            ejecutado_por=ejecutado_por,
            ip=ip,
            agente=agente,
        )

    return rol


def _validar_guarda_anti_autobloqueo(rol, nuevos_permisos_nombres, ejecutado_por=None):
    """
    Valida que la operación no deje al sistema sin acceso a administrar la matriz de permisos.
    1. El rol 'Administrador' nunca puede perder 'asignar_permisos'.
    2. El usuario activo no puede quitarse 'asignar_permisos' de su propio rol.
    """
    if rol.nombre == ROL_ADMINISTRADOR and PERMISO_CU4 not in nuevos_permisos_nombres:
        raise OperacionInvalidaError(
            f'Guarda de seguridad: el rol "{ROL_ADMINISTRADOR}" debe conservar '
            f'siempre el permiso "{PERMISO_CU4}".'
        )

    if ejecutado_por and getattr(ejecutado_por, 'id_rol_id', None) == rol.pk:
        if PERMISO_CU4 not in nuevos_permisos_nombres:
            raise OperacionInvalidaError(
                f'Guarda de auto-bloqueo: no puedes revocar el permiso "{PERMISO_CU4}" '
                f'del rol al que actualmente perteneces ({rol.nombre}).'
            )


@transaction.atomic
def asignar_permiso_a_rol(rol, permiso, ejecutado_por=None, ip=None, agente=None):
    """
    Asigna un permiso específico a un rol (+asignarPermiso() del diagrama de clases).
    """
    creado = rol.asignar_permiso(permiso)
    if creado:
        _registrar_bitacora(
            accion=AccionBitacora.ASIGNAR_PERMISO_ROL,
            tabla_afectada='rol_permiso',
            descripcion=f'Se asignó el permiso "{permiso.nombre}" al rol "{rol.nombre}".',
            ejecutado_por=ejecutado_por,
            ip=ip,
            agente=agente,
        )
    return creado


@transaction.atomic
def quitar_permiso_de_rol(rol, permiso, ejecutado_por=None, ip=None, agente=None):
    """
    Quita un permiso de un rol (+quitarPermiso() del diagrama de clases).
    Aplica guardas anti-autobloqueo si el permiso a revocar es 'asignar_permisos'.
    """
    if permiso.nombre == PERMISO_CU4:
        # Al quitarlo, el conjunto resultante no tendrá el permiso
        permisos_restantes = set(rol.permisos.exclude(pk=permiso.pk).values_list('nombre', flat=True))
        _validar_guarda_anti_autobloqueo(rol, permisos_restantes, ejecutado_por=ejecutado_por)

    eliminado = rol.quitar_permiso(permiso)
    if eliminado:
        _registrar_bitacora(
            accion=AccionBitacora.REVOCAR_PERMISO_ROL,
            tabla_afectada='rol_permiso',
            descripcion=f'Se revocó el permiso "{permiso.nombre}" del rol "{rol.nombre}".',
            ejecutado_por=ejecutado_por,
            ip=ip,
            agente=agente,
        )
    return eliminado


@transaction.atomic
def reemplazar_permisos_rol(rol, permisos_ids, ejecutado_por=None, ip=None, agente=None):
    """
    Reemplaza en bloque la lista de permisos asignados a un rol (matriz completa).
    Calcula el diff exacto para bitácora y aplica guardas de seguridad.
    """
    permisos_objetos = list(Permiso.objects.filter(id_permiso__in=permisos_ids))
    if len(permisos_objetos) != len(set(permisos_ids)):
        ids_encontrados = {p.id_permiso for p in permisos_objetos}
        ids_faltantes = set(permisos_ids) - ids_encontrados
        raise OperacionInvalidaError(f'Los siguientes IDs de permisos no existen: {list(ids_faltantes)}.')

    nuevos_nombres = {p.nombre for p in permisos_objetos}
    _validar_guarda_anti_autobloqueo(rol, nuevos_nombres, ejecutado_por=ejecutado_por)

    permisos_actuales = set(rol.permisos.all())
    nuevos_set = set(permisos_objetos)

    agregados = nuevos_set - permisos_actuales
    removidos = permisos_actuales - nuevos_set

    # Si hay cambios, actualizamos y registramos auditoría
    if agregados or removidos:
        rol.permisos.set(permisos_objetos)

        detalle_agregados = f'Agregados ({len(agregados)}): [{", ".join(sorted(p.nombre for p in agregados))}]' if agregados else ''
        detalle_removidos = f'Removidos ({len(removidos)}): [{", ".join(sorted(p.nombre for p in removidos))}]' if removidos else ''
        partes_diff = [p for p in (detalle_agregados, detalle_removidos) if p]
        diff_texto = '; '.join(partes_diff)

        _registrar_bitacora(
            accion=AccionBitacora.ACTUALIZACION_MATRIZ_PERMISOS,
            tabla_afectada='rol_permiso',
            descripcion=f'Se actualizó la matriz de permisos del rol "{rol.nombre}". {diff_texto}. Total actual: {len(nuevos_set)} permisos.',
            ejecutado_por=ejecutado_por,
            ip=ip,
            agente=agente,
        )

    return rol
