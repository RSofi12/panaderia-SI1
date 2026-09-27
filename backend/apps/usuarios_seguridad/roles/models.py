from django.db import models


class Rol(models.Model):
    id_rol = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Nombre del Rol')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    permisos = models.ManyToManyField(
        'permisos.Permiso',
        through='RolPermiso',
        related_name='roles',
        verbose_name='Permisos asignados'
    )

    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['id_rol']

    def __str__(self):
        return self.nombre


class RolPermiso(models.Model):
    rol = models.ForeignKey(
        'roles.Rol',
        on_delete=models.CASCADE,
        db_column='id_rol',
        related_name='rol_permisos',
        verbose_name='Rol'
    )
    permiso = models.ForeignKey(
        'permisos.Permiso',
        on_delete=models.CASCADE,
        db_column='id_permiso',
        related_name='rol_permisos',
        verbose_name='Permiso'
    )

    class Meta:
        db_table = 'rol_permiso'
        unique_together = (('rol', 'permiso'),)
        verbose_name = 'Rol Permiso'
        verbose_name_plural = 'Roles Permisos'

    def __str__(self):
        return f'{self.rol.nombre} -> {self.permiso.nombre}'
