from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.usuarios_seguridad.auth_app.serializers import (
    CustomTokenObtainPairSerializer,
    UsuarioProfileSerializer
)
from apps.usuarios_seguridad.bitacora.models import Bitacora


class CustomLoginView(TokenObtainPairView):
    """
    Vista de Login (CU1) - Panadería Santiago.
    Autentica al usuario, genera tokens JWT con claims y registra el evento en Bitácora.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            # Obtener el usuario autenticado desde el serializador
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid()
            user = getattr(serializer, 'user', None)

            if user:
                # Obtener la IP del cliente
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

                # Registrar auditoría en la tabla Bitácora (CU26)
                Bitacora.registrar(
                    usuario=user,
                    accion='INICIO_SESION',
                    tabla_afectada='usuario',
                    descripcion=f'Inicio de sesión exitoso desde IP: {ip}'
                )

        return response


class CustomTokenRefreshView(TokenRefreshView):
    """Vista para refrescar el access token a partir de un refresh token válido."""
    pass


class UserProfileView(APIView):
    """
    Endpoint /api/auth/me/
    Retorna la información del usuario autenticado en la sesión activa.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Endpoint /api/auth/logout/
    Registra el cierre de sesión en la Bitácora de auditoría.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Bitacora.registrar(
            usuario=request.user,
            accion='CIERRE_SESION',
            tabla_afectada='usuario',
            descripcion='Cierre de sesión manual del usuario.'
        )
        return Response({'message': 'Sesión cerrada exitosamente.'}, status=status.HTTP_200_OK)
