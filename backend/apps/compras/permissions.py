from rest_framework.permissions import SAFE_METHODS, BasePermission

# Quien registra una compra (CU7) necesita elegir un proveedor, así que también
# puede consultar el directorio aunque no pueda modificarlo.
PERMISOS_LECTURA = {'gestionar_proveedores', 'registrar_compras'}


class PuedeGestionarProveedores(BasePermission):
    """
    RBAC del CU6 (actores: Administrador y Propietario).
    Consultar exige 'gestionar_proveedores' o 'registrar_compras';
    crear, editar o cambiar el estado exige 'gestionar_proveedores'.
    """
    message = 'Tu rol no cuenta con el permiso gestionar_proveedores.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        permisos = set(user.get_permisos_nombres())
        if request.method in SAFE_METHODS:
            return bool(permisos & PERMISOS_LECTURA)
        return 'gestionar_proveedores' in permisos
