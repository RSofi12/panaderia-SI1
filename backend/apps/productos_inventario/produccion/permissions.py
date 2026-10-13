"""Permisos de acceso para el módulo de producción."""

from rest_framework.permissions import BasePermission


class PuedeConsultarHistorialProduccion(BasePermission):
    """Solo el Personal de Producción tiene acceso a consultar historial de producción."""

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False

        permisos = set(usuario.get_permisos_nombres())
        return 'registrar_produccion' in permisos
