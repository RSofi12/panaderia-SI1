"""
Constantes de seguridad y configuración para la gestión de roles y permisos (CU4).
"""

#: Roles que forman parte de la arquitectura base del sistema (seed) y cuyo
#: nombre NO puede ser modificado ni eliminado porque existen comprobaciones
#: hardcodeadas y lógica de negocio basada en su identidad.
ROLES_PROTEGIDOS = (
    'Administrador',
    'Propietario',
    'Personal de Ventas',
    'Personal de Producción',
)

ROL_ADMINISTRADOR = 'Administrador'

#: Permiso requerido para administrar la matriz de roles y permisos (CU4).
PERMISO_CU4 = 'asignar_permisos'
