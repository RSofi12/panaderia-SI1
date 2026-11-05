"""
URL configuration for config project.
Panadería Santiago (SI-1)
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    db_status = 'ok'
    tables = []
    err_msg = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
            tables = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        db_status = 'error'
        err_msg = str(e)
    return JsonResponse({
        'status': 'ok',
        'database': db_status,
        'tables_count': len(tables),
        'sample_tables': tables[:10],
        'error': err_msg
    })

urlpatterns = [
    path('', health_check),
    path('api/health/', health_check),
    path('admin/', admin.site.urls),

    # Paquete 1 — Usuarios y Seguridad.
    path('api/auth/', include('apps.usuarios_seguridad.auth_app.urls')),
    path('api/', include('apps.usuarios_seguridad.users.urls')),
    path('api/', include('apps.usuarios_seguridad.roles.urls')),
    path('api/', include('apps.usuarios_seguridad.permisos.urls')),
    path('api/', include('apps.usuarios_seguridad.bitacora.urls')),
    path('api/', include('apps.productos_inventario.urls')),
    path('api/', include('apps.compras.urls')),
    path('api/', include('apps.comercializacion.urls')),
    path('api/', include('apps.reportes.urls')),
]
