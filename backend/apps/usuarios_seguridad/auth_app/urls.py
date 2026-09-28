from django.urls import path
from .views import (
    CustomLoginView,
    CustomTokenRefreshView,
    UserProfileView,
    LogoutView,
    RecuperacionSolicitudView,
    RecuperacionConfirmacionView,
)

app_name = 'auth_app'

urlpatterns = [
    # CU1 — Iniciar sesión
    path('login/', CustomLoginView.as_view(), name='login'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # CU2 — Recuperar contraseña.
    # Los nombres de las rutas son los que fija el enunciado del CU2 en
    # docs/ai/IMPLEMENTATION_PHASES.md, para que la trazabilidad entre caso de
    # uso y endpoint sea directa y se pueda citar en la defensa.
    path(
        'password-reset-request/',
        RecuperacionSolicitudView.as_view(),
        name='password_reset_request',
    ),
    path(
        'password-reset-confirm/',
        RecuperacionConfirmacionView.as_view(),
        name='password_reset_confirm',
    ),
]
