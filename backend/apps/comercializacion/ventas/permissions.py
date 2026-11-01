from rest_framework.permissions import BasePermission


class PuedeRegistrarVentas(BasePermission):
    """Quien tenga el permiso registrar_ventas. No se compara el nombre del rol."""
    message = 'Tu rol no cuenta con el permiso registrar_ventas.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return 'registrar_ventas' in set(user.get_permisos_nombres())

class PuedeConsultarComprobante(BasePermission):
    """
    Permite consultar e imprimir comprobantes de venta (CU16).
    Autorizado para:
    - Personal de Ventas (registrar_ventas)
    - Propietario (generar_reportes)
    - Administrador (gestionar_usuarios) o is_staff/is_superuser
    """
    message = 'Tu rol no cuenta con permiso para consultar comprobantes de venta.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        permisos = set(user.get_permisos_nombres())
        return bool(permisos & {'registrar_ventas', 'generar_reportes', 'gestionar_usuarios'})

