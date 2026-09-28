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
