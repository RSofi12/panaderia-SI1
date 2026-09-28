"""
Rutas de API para el módulo de Permisos.
"""
from rest_framework.routers import DefaultRouter
from .views import PermisoViewSet

router = DefaultRouter()
router.register(r'permisos', PermisoViewSet, basename='permiso')

urlpatterns = router.urls
