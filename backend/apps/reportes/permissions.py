from rest_framework.permissions import BasePermission


class PuedeGenerarReportes(BasePermission):
    """CU21–CU25. Entra quien tiene generar_reportes. El seed se lo deja solo al Propietario."""

    message = 'Tu rol no cuenta con el permiso generar_reportes.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return 'generar_reportes' in set(user.get_permisos_nombres())
