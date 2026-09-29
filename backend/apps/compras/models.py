from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Proveedor(models.Model):
    """
    Maestro de proveedores de materias primas e insumos (CU6).
    Cumple con la tabla 'proveedor' de Database_Panaderia_Santiago.sql.
    No se borra: la baja es activo=False (soft delete).
    """
    id_proveedor = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=150, verbose_name='Nombre del proveedor')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    direccion = models.CharField(max_length=200, blank=True, null=True, verbose_name='Dirección')
    fecha_registro = models.DateTimeField(default=timezone.now, verbose_name='Fecha de registro')
    activo = models.BooleanField(default=True, verbose_name='Proveedor activo')

    class Meta:
        db_table = 'proveedor'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(
                Lower('nombre'),
                name='proveedor_nombre_unico_ci',
            ),
        ]

    def __str__(self):
        return self.nombre
