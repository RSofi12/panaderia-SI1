from django.db import models


class Permiso(models.Model):
    id_permiso = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Nombre del Permiso')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')

    class Meta:
        db_table = 'permiso'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        ordering = ['id_permiso']

    def __str__(self):
        return self.nombre
