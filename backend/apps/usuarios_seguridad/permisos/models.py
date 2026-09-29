from django.db import models
from django.db.models.functions import Lower


class ModuloPermiso(models.TextChoices):
    """
    Agrupación de permisos según los 5 paquetes del backend y del mapa de casos de uso
    (PACKAGE_CU_MAP.md). Permite organizar la matriz de roles y permisos en el dashboard.
    """
    USUARIOS_SEGURIDAD = 'usuarios_seguridad', 'Usuarios y Seguridad'
    PRODUCTOS_INVENTARIO = 'productos_inventario', 'Productos e Inventario'
    COMPRAS = 'compras', 'Compras y Proveedores'
    COMERCIALIZACION = 'comercializacion', 'Comercialización'
    REPORTES = 'reportes', 'Reportes'


class Permiso(models.Model):
    id_permiso = models.BigAutoField(primary_key=True)
    nombre = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nombre del Permiso',
        help_text='Identificador único del permiso en código (ej. asignar_permisos).'
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    modulo = models.CharField(
        max_length=30,
        choices=ModuloPermiso.choices,
        default=ModuloPermiso.USUARIOS_SEGURIDAD,
        verbose_name='Módulo o Paquete'
    )

    class Meta:
        db_table = 'permiso'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['id_permiso']
        constraints = [
            models.UniqueConstraint(
                Lower('nombre'),
                name='permiso_nombre_unico_ci',
                violation_error_message='Ya existe un permiso con este nombre (no distingue mayúsculas).'
            )
        ]

    def __str__(self):
        return f'{self.nombre} ({self.get_modulo_display()})'
