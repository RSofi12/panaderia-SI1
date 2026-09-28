from django.contrib import admin

from .models import TokenRecuperacion


@admin.register(TokenRecuperacion)
class TokenRecuperacionAdmin(admin.ModelAdmin):
    """
    Panel de solo lectura para el Administrador.

    Ni se puede crear ni editar un token a mano. Un token es un artefacto
    emitido por el sistema: si el Administrador pudiera escribir uno a mano, la
    trazabilidad de "¿quién generó este enlace?" se rompería justo en el flujo que
    más se vigila. Lo que sí sirve es poder CONSULTAR la tabla para auditar
    cuántas solicitudes hizo cada usuario y si llegaron a usarse.
    """

    list_display = (
        'id_token',
        'usuario',
        'email_destino',
        'creado_en',
        'expira_en',
        'usado_en',
        'invalidado_en',
        'intentos',
    )
    list_filter = ('invalidado_en', 'usado_en')
    search_fields = (
        'usuario__nombre_usuario',
        'usuario__nombre_completo',
        'email_destino',
    )
    ordering = ('-creado_en',)
    readonly_fields = (
        'id_token', 'usuario', 'token_hash', 'email_destino', 'creado_en',
        'expira_en', 'usado_en', 'invalidado_en', 'intentos', 'ip_origen',
        'agente_usuario',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
