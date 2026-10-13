from rest_framework.permissions import SAFE_METHODS, BasePermission


class PuedeGestionarMateriaPrima(BasePermission):
    """La consulta requiere autenticación; las escrituras requieren permiso de gestión (CU8)."""

    message = 'Tu rol no cuenta con el permiso gestionar_materias_primas.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return 'gestionar_materias_primas' in user.get_permisos_nombres()


class EsRolAutorizadoCU09(BasePermission):
    """
    CU09: Permite consultar alertas de bajo stock al Administrador,
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
