from django.contrib import admin
from .models import Permiso


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('id_permiso', 'nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
