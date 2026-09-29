"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Paquete 1 — Usuarios y Seguridad.
    # `auth_app` responde a lo que pasa por la autenticación (CU1, CU2) y
    # `users` a la administración de cuentas (CU3). Son dos Prefijos distintos y
    # no uno solo, porque las preguntas son distintas: "¿puedo entrar?" y "¿qué
    # puedo administrar?"; mezclarlas haría que un endpoint de recuperación de
    # contraseña compartiera permiso con la gestión de cuentas.
    path('api/auth/', include('apps.usuarios_seguridad.auth_app.urls')),
    path('api/', include('apps.usuarios_seguridad.users.urls')),
    path('api/', include('apps.usuarios_seguridad.roles.urls')),
    path('api/', include('apps.usuarios_seguridad.permisos.urls')),
    path('api/', include('apps.productos_inventario.urls')),
    path('api/', include('apps.compras.urls')),
]

