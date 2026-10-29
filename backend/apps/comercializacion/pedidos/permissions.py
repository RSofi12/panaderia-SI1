from rest_framework.permissions import BasePermission


class PuedeRegistrarPedidos(BasePermission):
    """Quien tenga el permiso registrar_pedidos. No se compara el nombre del rol."""
    message = 'Tu rol no cuenta con el permiso registrar_pedidos.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return 'registrar_pedidos' in set(user.get_permisos_nombres())


class PuedeConsultarPedidos(BasePermission):
    """CU15: ventas y producción pueden consultar el estado de los pedidos."""

    message = 'Tu rol no cuenta con permisos para consultar pedidos.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or getattr(user, 'is_staff', False):
            return True
        return bool(set(user.get_permisos_nombres()) & {'registrar_pedidos', 'registrar_produccion'})
