"""
Permisos RBAC para la sub-app de Productos Terminados (CU12: Consultar existencias de productos terminados).

Reglas de negocio y seguridad:
  - Actores autorizados según PUDS (PACKAGE_CU_MAP.md):
      * Propietario (supervisión de existencias en vitrina y valor del inventario)
      * Personal de Ventas (consulta rápida de panes disponibles para despacho)
      * Administrador (control total)
      * Personal de Producción (consulta para reposición)
  - Permisos evaluados:
      * 'gestionar_inventario' (permiso base asignado a Propietario, Ventas y Producción)
      * 'gestionar_productos' (Administrador y Propietario)
      * 'registrar_ventas' (Personal de Ventas)
      * 'registrar_pedidos' (Personal de Ventas)
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

# Permisos que habilitan la lectura de existencias de productos terminados
PERMISOS_CONSULTA_EXISTENCIAS = {
    'gestionar_inventario',
    'gestionar_productos',
    'registrar_ventas',
    'registrar_pedidos',
}


class PuedeConsultarExistenciasTerminados(BasePermission):
    """
    Verifica que el usuario autenticado cuente con al menos uno de los permisos
    requeridos para consultar el inventario de pan listo para la venta (CU12).
    """
    message = 'Tu rol no cuenta con permisos para consultar las existencias de productos terminados.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Superusuarios y administradores tienen acceso irrestricto
        if user.is_superuser or getattr(user, 'is_staff', False):
            return True

        # Obtener nombres de permisos del usuario mediante el helper del modelo
        permisos_usuario = set(user.get_permisos_nombres())

        # Operaciones de lectura (GET, HEAD, OPTIONS): CU12
        if request.method in SAFE_METHODS:
            return bool(permisos_usuario & PERMISOS_CONSULTA_EXISTENCIAS)

        # Operaciones de modificación (futuras o CU18): exige gestionar_inventario
        return 'gestionar_inventario' in permisos_usuario
