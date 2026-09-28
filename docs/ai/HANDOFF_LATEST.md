# Resumen de Entrega y Continuidad (HANDOFF LATEST)

## 📌 Proyecto: Sistema de Información Web - Panadería Santiago (SI-1)
- **Fecha:** 2026-09-28
- **Estado del Ciclo:** Ciclo 1 - CU1, CU2 y CU3 (backend) terminados
- **Entorno:** Local directo (Python Virtualenv + Vite/React + PostgreSQL)

> Este archivo se reescribió por completo. La versión anterior era del 2026-09-26 y
> describía el plan de arranque, cuando todavía no existía ni el login. Un handoff
> que miente sobre el estado es peor que no tener handoff.

---

## 📊 1. Estado real por caso de uso

| CU | Nombre | Estado | Dónde está |
|---|---|---|---|
| CU1 | Iniciar sesión | 🟢 Completo end-to-end | `auth_app/` + `LoginPage.tsx` |
| CU2 | Recuperar contraseña | 🟢 Completo end-to-end | `recuperacion/` + `/recuperar-password` |
| CU3 | Gestionar usuarios | 🟡 **Backend completo y verificado, falta el frontend** | `users/` |
| CU4 | Asignar roles y permisos | ⚪ Pendiente | Modelos ya existen en `roles/` y `permisos/` |
| CU26 | Gestionar bitácora | 🟡 Registros ya se escriben, falta la pantalla | `bitacora/` |
| CU5 | Gestionar productos | ⚪ Pendiente | `productos_inventario/` vacío |
| CU6 | Gestionar proveedores | ⚪ Pendiente | `compras/` vacío |

Detalle por caso de uso: [`CURRENT_STATE.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/CURRENT_STATE.md)
Decisiones con su motivo: [`DECISIONS_LOG.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/DECISIONS_LOG.md)

---

## 📦 2. Lo entregado en esta sesión (CU3, backend)

### Endpoints nuevos
```
GET    /api/usuarios/                             listado filtrado, buscable y paginado
POST   /api/usuarios/                             alta de cuenta
GET    /api/usuarios/roles/                       roles para el desplegable del formulario
GET    /api/usuarios/<id>/                        detalle
PATCH  /api/usuarios/<id>/                        edición parcial
PUT    /api/usuarios/<id>/                        edición completa
PATCH  /api/usuarios/<id>/toggle-activo/          activar / inactivar
POST   /api/usuarios/<id>/restablecer-contrasena/ reset administrativo de clave  (extensión)
POST   /api/usuarios/<id>/desbloquear/            levantar bloqueo de CU1          (extensión)
DELETE /api/usuarios/<id>/                        405 — el CU3 no tiene borrado
```

Parámetros aceptados por el listado: `search`, `ordering`, `page`,
`activo=true|false`, `id_rol=<n>`.

### Archivos creados
- `backend/apps/usuarios_seguridad/users/permissions.py` — RBAC real (`TienePermiso`, `EsAdministrador`)
- `backend/apps/usuarios_seguridad/users/exceptions.py` — `OperacionInvalidaError` (400 con `{"error": "..."}`)
- `backend/apps/usuarios_seguridad/users/serializers.py` — 6 serializers, separados por lectura/escritura
- `backend/apps/usuarios_seguridad/users/services/usuarios.py` — la lógica de negocio
- `backend/apps/usuarios_seguridad/users/views.py` — `UsuarioViewSet`
- `backend/apps/usuarios_seguridad/users/urls.py` — router
- `backend/apps/usuarios_seguridad/users/tests.py` — 52 pruebas
- `backend/apps/usuarios_seguridad/users/migrations/0005_alter_usuario_nombre_usuario_and_more.py`
- `backend/apps/usuarios_seguridad/bitacora/migrations/0006_alter_bitacora_accion.py`

### Archivos modificados
- `users/models.py` — restricción `usuario_username_unico_ci` sobre `Lower(nombre_usuario)`
- `users/services/__init__.py` — expone el módulo de servicios
- `bitacora/models.py` — cuatro acciones nuevas en `AccionBitacora`
- `config/urls.py` — `path('api/', include('apps.usuarios_seguridad.users.urls'))`
- `config/settings.py` — paginación global, throttle `usuarios: 120/min`
- `docs/informes/Database_Panaderia_Santiago.sql` — índice nuevo, cuatro acciones de bitácora, deriva de `rol_permiso` documentada
- `docs/ai/CURRENT_STATE.md`, `docs/ai/DECISIONS_LOG.md`

---

## 🧪 3. Verificación ejecutada

| Comando | Resultado |
|---|---|
| `python manage.py check` | ✅ sin problemas |
| `python manage.py makemigrations --check --dry-run` | ✅ sin cambios pendientes |
| `python manage.py migrate` | ✅ `bitacora.0006` y `users.0005` aplicadas |
| `python manage.py test apps.usuarios_seguridad` | ✅ **144 pruebas en verde** (1 se salta) |
| Índice en PostgreSQL real | ✅ `usuario_username_unico_ci` creado; rechaza `MGONZALES` y acepta un alta nueva |

### ⚠️ Limitación conocida de la validación
El usuario de base de datos (`panaderia_admin`) **no tiene `CREATEDB`**, así que
`manage.py test` no puede crear `test_panaderia_db` y falla con
*"se ha denegado el permiso para crear la base de datos"*. La suite se ejecutó con
un módulo de ajustes alterno **en SQLite**, que alcanza para detectar errores de
Python y de lógica, pero **no es la validación oficial**.

Para habilitar la corrida oficial, una sola vez, con un usuario superusuario de
PostgreSQL:

```sql
ALTER ROLE panaderia_admin CREATEDB;
```

Después, `python manage.py test apps.usuarios_seguridad` funciona sin cambios
adicionales. Vale la pena hacerlo: la prueba
`test_la_base_rechaza_el_duplicado_por_mayusculas` depende del comportamiento del
índice de expresión, que SQLite no reproduce igual que PostgreSQL.

---

## 🔜 4. Punto exacto de reanudación

**Siguiente paso: la SPA de gestión de usuarios (frontend del CU3).**

1. Crear `frontend/src/apps/dashboard/usuarios/` con:
   - `UsuariosPage.tsx` — tabla, buscador, filtros por rol y estado, paginación
   - `UsuarioFormModal.tsx` — alta y edición, con el desplegable de `GET /api/usuarios/roles/`
   - `ConfirmarEstadoModal.tsx` — activar/inactivar con motivo
   - `RestablecerContrasenaModal.tsx` — extensión aprobada
2. Poner `implemented: true` en la entrada de `navigation.ts` y registrar la ruta
   anidada en `AppRoutes.tsx` (ver paso 4 de `CURRENT_STATE.md`).
3. Leer el shape de la respuesta paginada de DRF: `{count, next, previous, results}`.

**Puntos que el frontend no debe pasar por alto:**
- El listado devuelve `esta_bloqueado` y `minutos_bloqueo_restantes`: son
  propiedades calculadas, y sirven para explicar por qué una cuenta no entra.
- El buscador es `icontains` y **no ignora acentos**: buscar `Maria` no encuentra
  `María`.
- `DELETE` devuelve 405, así que la UI no debe ofrecer una acción de borrar.
- Los errores de las guardas vienen como `{"error": "texto"}`; los de validación de
  campo vienen como `{"campo": ["texto"]}`. Son dos formatos distintos y el
  `setError(...)` de React espera cadenas.

---

## ⚙️ 5. Comandos de verificación local

```powershell
# Backend
cd backend
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py test apps.usuarios_seguridad

# Datos de prueba (crea roles, permisos y las 6 cuentas del seed)
.\venv\Scripts\python.exe manage.py seed_usuarios
#   usuario: admin  |  contraseña: Admin123!
#   usuario: mgonzales (Personal de Ventas) — sirve para probar el 403

# Frontend
cd ..\frontend
npm run lint
npm run build
```
