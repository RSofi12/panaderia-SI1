from rest_framework.permissions import SAFE_METHODS, BasePermission


class PuedeGestionarMateriaPrima(BasePermission):
    """La consulta requiere autenticación; las escrituras requieren permiso de gestión."""

    message = 'Tu rol no cuenta con el permiso gestionar_materias_primas.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return 'gestionar_materias_primas' in user.get_permisos_nombres()
