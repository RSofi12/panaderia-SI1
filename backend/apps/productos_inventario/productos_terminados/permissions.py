"""
Permisos RBAC para la sub-app de Productos Terminados:
  - CU12: Consultar existencias de productos terminados.
  - CU18: Registrar baja de productos terminados (mermas/pérdidas).

Reglas de negocio y seguridad segun PUDS (PACKAGE_CU_MAP.md):
  - Actores autorizados CU12:
      * Propietario
      * Personal de Ventas
      * Administrador
      * Personal de Produccion
  - Actores autorizados CU18:
      * Personal de Produccion
      * Propietario
      * Administrador
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

PERMISOS_CONSULTA_EXISTENCIAS = {
    'gestionar_inventario',
    'gestionar_productos',
    'registrar_ventas',
    'registrar_pedidos',
    'registrar_produccion',
}

PERMISOS_REGISTRO_BAJAS = {
    'gestionar_inventario',
    'registrar_produccion',
    'gestionar_productos',
}


class PuedeConsultarExistenciasTerminados(BasePermission):
    """
    Verifica que el usuario autenticado cuente con permisos para consultar existencias (CU12).
    """
    message = 'Tu rol no cuenta con permisos para consultar las existencias de productos terminados.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or getattr(user, 'is_staff', False):
            return True

        permisos_usuario = set(user.get_permisos_nombres())

        if request.method in SAFE_METHODS:
            return bool(permisos_usuario & PERMISOS_CONSULTA_EXISTENCIAS)

        return 'gestionar_inventario' in permisos_usuario


class PuedeRegistrarBajaProducto(BasePermission):
    """
    Verifica que el usuario autenticado cuente con permisos para registrar bajas/mermas (CU18).
    Actores: Personal de Produccion, Propietario, Administrador.
    """
    message = 'Tu rol no cuenta con permisos para registrar bajas o mermas de productos terminados.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or getattr(user, 'is_staff', False):
            return True

        permisos_usuario = set(user.get_permisos_nombres())
        return bool(permisos_usuario & PERMISOS_REGISTRO_BAJAS)
