from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from apps.usuarios_seguridad.users.models import Usuario


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador de Login JWT para Panadería Santiago (CU1).
    Valida credenciales, comprueba estado activo e inyecta claims con Rol y Permisos.
    """
    username_field = 'nombre_usuario'

    def validate(self, attrs):
        nombre_usuario = attrs.get('nombre_usuario')
        password = attrs.get('password')

        if not nombre_usuario or not password:
            raise serializers.ValidationError(
                {'error': 'Debe proporcionar el nombre de usuario y la contraseña.'},
                code='authorization'
            )

        # Autenticación con Django backend
        user = authenticate(
            request=self.context.get('request'),
            nombre_usuario=nombre_usuario,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                {'error': 'Credenciales inválidas. Verifique su usuario y contraseña.'},
                code='authorization'
            )

        if not user.activo:
            raise serializers.ValidationError(
                {'error': 'Esta cuenta de usuario se encuentra inactiva. Contacte al administrador.'},
                code='authorization'
            )

        # Generación estándar de tokens
        refresh = self.get_token(user)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id_usuario': user.id_usuario,
                'nombre_usuario': user.nombre_usuario,
                'nombre_completo': user.nombre_completo,
                'email': user.email,
                'id_rol': user.id_rol.id_rol if user.id_rol else None,
                'rol': user.rol_nombre,
                'permisos': user.get_permisos_nombres(),
            }
        }

        # Guardamos el usuario autenticado en la instancia para que la vista pueda registrarlo en Bitácora
        self.user = user
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Inyectar claims personalizados dentro del payload del JWT
        token['id_usuario'] = user.id_usuario
        token['nombre_usuario'] = user.nombre_usuario
        token['nombre_completo'] = user.nombre_completo
        token['id_rol'] = user.id_rol.id_rol if user.id_rol else None
        token['rol'] = user.rol_nombre
        token['permisos'] = user.get_permisos_nombres()

        return token


class UsuarioProfileSerializer(serializers.ModelSerializer):
    """Serializador para el endpoint /api/auth/me/"""
    id_rol = serializers.IntegerField(source='id_rol.id_rol', read_only=True)
    rol = serializers.CharField(source='rol_nombre', read_only=True)
    permisos = serializers.ListField(source='get_permisos_nombres', read_only=True)

    class Meta:
        model = Usuario
        fields = (
            'id_usuario',
            'nombre_usuario',
            'nombre_completo',
            'email',
            'activo',
            'id_rol',
            'rol',
            'permisos',
        )
        read_only_fields = fields
