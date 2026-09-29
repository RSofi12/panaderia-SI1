from django.db import models
from django.db.models.functions import Lower


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
        constraints = [
            models.UniqueConstraint(
                Lower('nombre'),
                name='rol_nombre_unico_ci',
                violation_error_message='Ya existe un rol con este nombre (no distingue mayúsculas).'
            )
        ]

    def __str__(self):
        return self.nombre

    def asignar_permiso(self, permiso):
        """
        Método de dominio correspondiente a +asignarPermiso() en el diagrama de clases UML.
        Asocia un permiso al rol si no lo tiene previamente.
        """
        obj, created = RolPermiso.objects.get_or_create(rol=self, permiso=permiso)
        return created

    def quitar_permiso(self, permiso):
        """
        Método de dominio correspondiente a +quitarPermiso() en el diagrama de clases UML.
        Remueve la asociación del permiso con este rol.
        """
        borrados, _ = RolPermiso.objects.filter(rol=self, permiso=permiso).delete()
        return borrados > 0


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
        verbose_name = 'Rol Permiso'
        verbose_name_plural = 'Roles Permisos'
        constraints = [
            models.UniqueConstraint(
                fields=['rol', 'permiso'],
                name='rol_permiso_unico',
                violation_error_message='Este rol ya tiene asignado dicho permiso.'
            )
        ]

    def __str__(self):
        return f'{self.rol.nombre} -> {self.permiso.nombre}'
