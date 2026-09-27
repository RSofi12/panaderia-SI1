from django.contrib.auth.base_user import BaseUserManager


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario de la Panadería Santiago.
    Usa 'nombre_usuario' como identificador único principal en lugar de email.
    """

    def create_user(self, nombre_usuario, password=None, **extra_fields):
        if not nombre_usuario:
            raise ValueError('El nombre de usuario es obligatorio.')

        extra_fields.setdefault('activo', True)
        usuario = self.model(nombre_usuario=nombre_usuario, **extra_fields)

        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()

        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, nombre_usuario, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('activo', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(nombre_usuario, password, **extra_fields)
