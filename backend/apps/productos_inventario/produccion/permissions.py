"""Permisos de acceso para el módulo de producción (CU10, CU11)."""

from rest_framework.permissions import BasePermission


class PuedeConsultarHistorialProduccion(BasePermission):
    """
    Permite la consulta del historial de producción a:
    - Personal de Producción ('registrar_produccion')
    - Propietario y Administrador ('gestionar_productos', 'generar_reportes')
    """

    message = 'Tu rol no cuenta con permisos para consultar el historial de producción.'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False

        if usuario.is_superuser:
            return True

        permisos = set(usuario.get_permisos_nombres())
        permisos_permitidos = {'registrar_produccion', 'gestionar_productos', 'generar_reportes'}
        return bool(permisos & permisos_permitidos)


class PuedeRegistrarProduccion(BasePermission):
    """
    Permite el registro de producción diaria (CU10) a:
    - Personal de Producción ('registrar_produccion')
    - Propietario y Administrador ('gestionar_productos', 'gestionar_inventario')
    - Superusuario
    """

    message = 'Tu rol no cuenta con permisos para registrar producción diaria.'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False

        if usuario.is_superuser:
            return True

        permisos = set(usuario.get_permisos_nombres())
        permisos_permitidos = {'registrar_produccion', 'gestionar_productos', 'gestionar_inventario'}
        return bool(permisos & permisos_permitidos)

