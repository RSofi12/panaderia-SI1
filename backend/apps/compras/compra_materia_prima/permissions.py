from rest_framework.permissions import BasePermission


class PuedeRegistrarCompras(BasePermission):
    """RBAC del CU7: registrar y consultar compras."""
    message = 'Tu rol no cuenta con el permiso registrar_compras.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return 'registrar_compras' in set(user.get_permisos_nombres())
