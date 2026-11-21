from django.contrib import admin

from apps.compras.proveedores.models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id_proveedor', 'nombre', 'telefono', 'direccion', 'descripcion', 'activo', 'fecha_registro')
    list_filter = ('activo',)
    search_fields = ('nombre', 'telefono', 'descripcion')
    readonly_fields = ('fecha_registro',)
