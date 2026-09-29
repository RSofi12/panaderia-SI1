from django.contrib import admin
from .models import Rol, RolPermiso


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')


@admin.register(RolPermiso)
class RolPermisoAdmin(admin.ModelAdmin):
    list_display = ('rol', 'permiso')
    list_filter = ('rol', 'permiso')
