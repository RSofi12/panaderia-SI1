"""
Servicios del módulo de roles y permisos.
"""
from .matriz import (
    crear_rol,
    editar_rol,
    asignar_permiso_a_rol,
    quitar_permiso_de_rol,
    reemplazar_permisos_rol,
)

__all__ = [
    'crear_rol',
    'editar_rol',
    'asignar_permiso_a_rol',
    'quitar_permiso_de_rol',
    'reemplazar_permisos_rol',
]
