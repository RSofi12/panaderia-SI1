
from rest_framework.permissions import BasePermission


class EsRolAutorizadoCU09(BasePermission):
    """
    CU09: Permite consultar alertas al Administrador,
    Propietario y Personal de Producción.
    """

    message = 'Tu rol no tiene acceso a las alertas de bajo stock.'

    ROLES_PERMITIDOS = {
        'Administrador',
        'Propietario',
        'Personal de Producción',
    }

    def has_permission(self, request, view):
        usuario = request.user

        if not usuario or not usuario.is_authenticated:
            return False

        return usuario.rol_nombre in self.ROLES_PERMITIDOS
