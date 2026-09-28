from django.db import models
from django.db.models.functions import Lower
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
    # El correo es OBLIGATORIO desde CU2: es el canal por el que sale el enlace
    # de recuperación de contraseña. Dejarlo opcional significaba que un usuario
    # sin correo podía pedir un restablecimiento, recibir el mensaje genérico de
    # "te enviamos un correo" y no recibir nunca nada, lo que además entrena al
    # usuario para desconfiar del sistema.
    email = models.EmailField(
        max_length=150,
        verbose_name='Correo electrónico'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Usuario activo'
    )

    # --- Estado de la política de bloqueo por intentos fallidos (CU1) ---
    # Son datos, no configuración de despliegue: viven en la tabla usuario
    # para poder contabilizar y auditar por cuenta. La escritura de estos
    # campos está encapsulada en auth_app.services.politica_bloqueo.
    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0,
        db_default=0,
        verbose_name='Intentos fallidos consecutivos',
        help_text='Se reinicia a 0 tras un inicio de sesión exitoso.'
    )
    bloqueado_hasta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bloqueado hasta',
        help_text='Instante en que expira el bloqueo. Null significa cuenta desbloqueada.'
    )
    ultimo_intento_fallido = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último intento fallido'
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
    REQUIRED_FIELDS = ['nombre_completo', 'email']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['id_usuario']
        constraints = [
            # Unicidad sobre `Lower('email')` y no sobre `email` a secas, porque
            # en PostgreSQL la comparación de texto distingue mayúsculas: sin
            # esto, 'Admin@mail.com' y 'admin@mail.com' serían dos cuentas
            # distintas y la recuperación de contraseña quedaría ambigua. Aplica
            # la misma lógica que la contraseña de MySQL, donde la collation no
            # distingue mayúsculas.
            models.UniqueConstraint(
                Lower('email'),
                name='usuario_email_unico_ci',
            ),
        ]

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
    def is_bloqueado(self):
        """
        Estado derivado: True si la ventana de bloqueo sigue vigente.

        OJO: es una propiedad de solo lectura, no una consulta. Para obtener el
        tiempo restante y limpiar bloqueos vencidos hay que pasar por
        auth_app.services.politica_bloqueo.evaluar_bloqueo(), que sí toca la BD.
        """
        from django.utils import timezone
        if not self.bloqueado_hasta:
            return False
        return self.bloqueado_hasta > timezone.now()

    @property
    def minutos_bloqueo_restantes(self):
        """Minutos que faltan para que expire el bloqueo. 0 si no está bloqueado."""
        from django.utils import timezone
        if not self.is_bloqueado:
            return 0
        segundos = (self.bloqueado_hasta - timezone.now()).total_seconds()
        return max(1, int(segundos // 60) + (1 if segundos % 60 else 0))

    @property
    def esta_bloqueado(self):
        """Alias legible usado en el panel de administración."""
        return self.is_bloqueado

    @property
    def rol_nombre(self):
        """Retorna el nombre del rol asignado o 'Sin Rol'."""
        return self.id_rol.nombre if self.id_rol else 'Sin Rol'

    def get_permisos_nombres(self):
        """Retorna la lista de códigos/nombres de permisos que posee este usuario según su rol."""
        if not self.id_rol:
            return []
        return list(self.id_rol.permisos.values_list('nombre', flat=True))
