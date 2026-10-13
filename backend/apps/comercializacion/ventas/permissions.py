from rest_framework.permissions import BasePermission


class PuedeRegistrarVentas(BasePermission):
    """Quien tenga el permiso registrar_ventas. No se compara el nombre del rol."""
    message = 'Tu rol no cuenta con el permiso registrar_ventas.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return 'registrar_ventas' in set(user.get_permisos_nombres())
