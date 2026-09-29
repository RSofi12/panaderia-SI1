from django.contrib import admin

from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id_proveedor', 'nombre', 'telefono', 'direccion', 'activo', 'fecha_registro')
    list_filter = ('activo',)
    search_fields = ('nombre', 'telefono')
    readonly_fields = ('fecha_registro',)
