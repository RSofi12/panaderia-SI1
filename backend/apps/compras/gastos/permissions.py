from rest_framework.permissions import BasePermission


class PuedeGestionarGastos(BasePermission):
    """RBAC del CU20: registrar, anular y consultar gastos e inversiones."""
    message = 'Tu rol no cuenta con el permiso registrar_gastos.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return 'registrar_gastos' in set(user.get_permisos_nombres())
