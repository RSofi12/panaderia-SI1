"""
Permisos de DRF del paquete de Usuarios y Seguridad (CU3).

Este archivo cubre un hueco que llevaba abierto desde CU1: el control de acceso
basado en roles existía como dato (`usuario.id_rol`, tabla `rol_permiso`) pero
ninguna clase de permiso de DRF lo leía. Todo lo que se protegía hasta ahora
usaba `IsAuthenticated`, que responde a una sola pregunta: "¿hay sesión?".

Para el Administrador eso no alcanza. El Propietario, el Personal de Ventas y el
Personal de Producción también llegan autenticados, y ninguno puede dar de alta
cuentas. La pregunta correcta no es "¿quién eres?" sino "¿qué te permite tu rol?".

La diferencia entre las dos es exactamente la que separa a una autenticación de
un control de acceso, y es el punto defendible del CU4 ante la docente.

Decisión de diseño: el permiso se lee de la TABLA, no de una constante en el
código. Agregar un módulo nuevo al sistema es una fila en `permiso` y una
asignación en `rol_permiso`; no es un despliegue. Es el mismo criterio que se
aplicó en CU1 al mover los umbrales de bloqueo de `settings.py` a la tabla
`configuracion_seguridad`.
"""
from rest_framework.permissions import BasePermission


class TienePermiso(BasePermission):
    """
    Exige que el usuario autenticado tenga un permiso concreto del catálogo.

    Se instancia, no se declara, y hay una razón técnica precisa para eso.
    `APIView.get_permissions()` hace `permission()` sobre cada elemento de
    `permission_classes`: vuelve a INSTANCIAR lo que encuentra en la lista. Si
    la lista contiene una instancia ya construida —que es justo lo que es
    `TienePermiso('gestionar_usuarios')`—, el intento de llamarla como
    constructor revienta con
    `TypeError: 'TienePermiso' object is not callable`.

    La forma correcta es sobreescribir el método en la vista:

        def get_permissions(self):
            return [TienePermiso('gestionar_usuarios')]

    Los permisos se leen con `Usuario.get_permisos_nombres()`, que es el mismo
    método que viaja dentro del JWT y que ya consume el frontend para filtrar el
    menú del panel. Que backend y frontend lean la MISMA fuente es lo que evita
    que la pantalla muestre un botón que el servidor va a rechazar.
    """

    def __init__(self, nombre_permiso):
        self.nombre_permiso = nombre_permiso

    def has_permission(self, request, view):
        usuario = request.user

        # Un usuario no autenticado no tiene permisos que evaluar, y la respuesta
        # correcta la decide DRF: 401 si no hay credenciales, 403 si las hay pero
        # no alcanzan. Devolver False en ambos casos conserva esa distinción.
        if not usuario or not usuario.is_authenticated:
            return False

        return self.nombre_permiso in usuario.get_permisos_nombres()

    def __repr__(self):
        return f'TienePermiso({self.nombre_permiso!r})'


class EsAdministrador(BasePermission):
    """
    Verifica contra el ROL, no contra `is_superuser`.

    Existe por dos razones concretas:

    1. `is_superuser` es un campo de Django que además concede acceso al panel
       de administración nativo. Acoplar la autorización de la API a ese campo
       haría que "puede entrar a /api/usuarios/" y "puede entrar a /admin/"
       fueran la misma decisión, cuando son dos superficies distintas.

    2. El proyecto tiene dos nociones de administrador que no son idénticas: el
       rol de negocio "Administrador" (el que gestiona las cuentas de los
       actores) y el superusuario de Django (el que mantiene el sistema). La API
       de CU3 necesita la primera.

    Ojo con la diferencia: un Administrador de negocio NO puede entrar a
    /admin/ salvo que además se le marque `is_staff`. Es deliberado. El panel de
    Django es una herramienta de mantenimiento técnico, no la herramienta de
    trabajo del panadero.
    """

    ROL_ADMINISTRADOR = 'Administrador'

    def has_permission(self, request, view):
        usuario = request.user

        if not usuario or not usuario.is_authenticated:
            return False

        return usuario.rol_nombre == self.ROL_ADMINISTRADOR
