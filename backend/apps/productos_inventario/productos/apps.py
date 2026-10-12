from django.apps import AppConfig


class ProductosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.productos_inventario.productos'
    label = 'productos'
    verbose_name = 'Gestión de Productos'
