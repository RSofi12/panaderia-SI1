from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('id_usuario', 'nombre_usuario', 'nombre_completo', 'email', 'rol_nombre', 'activo', 'is_bloqueado', 'is_staff')
    list_filter = ('activo', 'is_staff', 'id_rol')
    search_fields = ('nombre_usuario', 'nombre_completo', 'email')
    ordering = ('id_usuario',)
    # El administrador puede ver el estado de bloqueo, pero la única forma
    # soportada de levantarlo es calling servicios.politica_bloqueo.desbloquear_usuario(),
    # que además lo deja asentado en la bitácora.
    readonly_fields = ('intentos_fallidos', 'bloqueado_hasta', 'ultimo_intento_fallido', 'last_login')

    fieldsets = (
        (None, {'fields': ('nombre_usuario', 'password')}),
        ('Información Personal', {'fields': ('nombre_completo', 'email', 'id_rol')}),
        ('Permisos y Estado', {'fields': ('activo', 'is_staff', 'is_superuser')}),
        ('Seguridad CU1', {
            'fields': ('intentos_fallidos', 'bloqueado_hasta', 'ultimo_intento_fallido', 'last_login')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('nombre_usuario', 'nombre_completo', 'email', 'id_rol', 'password', 'activo'),
        }),
    )
