# apps/usuarios_seguridad/apps.py
from django.apps import AppConfig

class UsuariosSeguridadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios_seguridad'   # ← antes decía solo 'usuarios_seguridad'