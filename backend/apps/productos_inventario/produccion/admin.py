from django.contrib import admin

from .models import DetalleProduccion, Produccion


class DetalleProduccionInline(admin.TabularInline):
    model = DetalleProduccion
    extra = 1


@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    list_display = ('id_produccion', 'fecha', 'jornada', 'id_usuario')
    list_filter = ('fecha', 'jornada')
    search_fields = ('id_produccion', 'id_usuario__nombre_usuario')
    inlines = [DetalleProduccionInline]
