"""
Rutas de la API de administración de cuentas (CU3).

Se usa un `DefaultRouter` y no un `SimpleRouter` por una sola diferencia práctica
que importa en este proyecto: el router por defecto publica `/api/usuarios/` sin
ruta final, es decir, con barra. Un frontend configurado con `baseURL: '/api'`
y un `apiClient` que antepone `/` produce `/api//usuarios/` y recibe un 404 que
no dice nada. La barra final fija evita esa clase de error sin configuración
adicional.

El router registra automáticamente las rutas de `@action`, así que
`toggle-activo`, `restablecer-contrasena`, `desbloquear` y `roles` aparecen
sin escribir una línea por una. Lo que sí hay que declarar a mano es el prefijo
`usuarios`, que es lo que encola este módulo con los demás paquetes en
`config/urls.py`.
"""
from rest_framework.routers import DefaultRouter

from .views import UsuarioViewSet

app_name = 'users'

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = router.urls
