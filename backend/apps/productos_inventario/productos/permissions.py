from rest_framework.permissions import SAFE_METHODS, BasePermission


class PuedeGestionarProductos(BasePermission):
    """
    RBAC del CU5: cualquier usuario autenticado consulta el catálogo;
    crear, editar o cambiar el estado exige el permiso 'gestionar_productos'.
    """
    message = 'Tu rol no cuenta con el permiso gestionar_productos.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return 'gestionar_productos' in user.get_permisos_nombres()


class EsPropietarioCU19(BasePermission):
    """CU19 es exclusivo del rol de negocio Propietario, sin bypass de superusuario."""

    message = 'Solo el Propietario puede consultar el historial de precios.'

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.rol_nombre == 'Propietario'
        )
