from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado para la Panadería Santiago.
    Cumple estrictamente con la tabla 'usuario' de Database_Panaderia_Santiago.sql.
    """
    id_usuario = models.BigAutoField(primary_key=True)
    id_rol = models.ForeignKey(
        'roles.Rol',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_rol',
        related_name='usuarios',
        verbose_name='Rol asignado'
    )
    nombre_usuario = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nombre de usuario'
    )
    # password se mapea físicamente a la columna hash_contrasena
    password = models.CharField(
        max_length=255,
        db_column='hash_contrasena',
        verbose_name='Hash de contraseña'
    )
    nombre_completo = models.CharField(
        max_length=150,
        verbose_name='Nombre completo'
    )
    email = models.EmailField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name='Correo electrónico'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Usuario activo'
    )

    # Campos administrativos para el panel de Django
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Acceso al panel admin'
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name='Es superadministrador'
    )

    # Evitamos colisiones de nombres con el auth por defecto de Django
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='panaderia_usuarios',
        blank=True,
        verbose_name='Grupos'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='panaderia_usuarios_permissions',
        blank=True,
        verbose_name='Permisos de Django'
    )

    USERNAME_FIELD = 'nombre_usuario'
    REQUIRED_FIELDS = ['nombre_completo']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['id_usuario']

    def __str__(self):
        return f'{self.nombre_usuario} ({self.nombre_completo})'

    @property
    def is_active(self):
        """Propiedad requerida por Django y DRF para validar si el usuario está activo."""
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = bool(value)

    @property
    def rol_nombre(self):
        """Retorna el nombre del rol asignado o 'Sin Rol'."""
        return self.id_rol.nombre if self.id_rol else 'Sin Rol'

    def get_permisos_nombres(self):
        """Retorna la lista de códigos/nombres de permisos que posee este usuario según su rol."""
        if not self.id_rol:
            return []
        return list(self.id_rol.permisos.values_list('nombre', flat=True))
