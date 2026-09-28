# Sesión de Desarrollo: CU3 — Gestionar usuarios (backend)

- **Fecha:** 2026-09-28
- **Autor / Integrante:** opencode (agente IA del proyecto)
- **Paquete / Módulo:** `apps.usuarios_seguridad` (sub-app `users`)
- **Casos de Uso abordados:** CU3 (núcleo) y extensión de administración de cuentas
- **Ciclo:** Ciclo 1

---

## 1. 🎯 Objetivo de la sesión

Implementar el **backend** del CU3 "Gestionar usuarios" para el actor
Administrador: registro, edición, activación e inactivación de cuentas, con control
de acceso basado en roles, auditoría en bitácora y la unicidad real del nombre de
usuario.

El frontend quedó explícitamente fuera de esta sesión, por decisión del usuario: se
implementa después, en el módulo `src/apps/dashboard/usuarios/`.

---

## 2. 🛠️ Cambios realizados

### Backend — archivos creados

| Archivo | Responsabilidad |
|---|---|
| `users/permissions.py` | `TienePermiso(nombre)` y `EsAdministrador`. Cierra un hueco que venía abierto desde CU1: hasta ahora todo se protegía con `IsAuthenticated`, que responde "¿hay sesión?" y no "¿qué te permite tu rol?". |
| `users/exceptions.py` | `OperacionInvalidaError` (400) con cuerpo `{"error": "..."}`, el mismo formato que ya consume `LoginPage`. |
| `users/serializers.py` | 6 serializers: `UsuarioListSerializer`, `UsuarioCreateSerializer`, `UsuarioUpdateSerializer`, `CambioEstadoSerializer`, `RestablecerContrasenaSerializer`, `RolSimpleSerializer`. |
| `users/services/usuarios.py` | Toda la lógica de negocio: `registrar_usuario`, `editar_usuario`, `cambiar_estado`, `restablecer_contrasena`, `desbloquear_cuenta`, y las tres guardas de auto-destrucción. |
| `users/views.py` | `UsuarioViewSet`, delgado a propósito. |
| `users/urls.py` | `DefaultRouter` con el prefijo `usuarios`. |
| `users/tests.py` | 52 pruebas organizadas por regla, no por método. |
| `users/migrations/0005_...py` | Índice único sobre `Lower(nombre_usuario)`. |
| `bitacora/migrations/0006_...py` | Cuatro acciones nuevas en `AccionBitacora`. |

### Backend — archivos modificados

- **`users/models.py`**: se agrega `UniqueConstraint(Lower('nombre_usuario'))` con
  nombre `usuario_username_unico_ci`. El `unique=True` de la columna **se conserva**
  (ver decisión 25).
- **`users/services/__init__.py`**: expone el módulo de servicios.
- **`bitacora/models.py`**: `ALTA_USUARIO`, `EDICION_USUARIO`,
  `CAMBIAR_ESTADO_USUARIO`, `RESTABLECER_CONTRASENA`. `DESBLOQUEO_CUENTA` ya existía
  desde CU1 y se reutiliza.
- **`config/urls.py`**: `path('api/', include('apps.usuarios_seguridad.users.urls'))`.
- **`config/settings.py`**: `PageNumberPagination` con `PAGE_SIZE = 10` de forma
  global, y `DEFAULT_THROTTLE_RATES['usuarios'] = '120/min'`.

### Base de datos

- `users.0005` y `bitacora.0006` aplicadas con `manage.py migrate` sobre
  `panaderia_db`. Sin conflictos: no había cuentas que solo difirieran en mayúsculas.
- `docs/informes/Database_Panaderia_Santiago.sql` actualizado con el índice nuevo,
  el comentario de los cuatro valores de bitácora, y la deriva de `rol_permiso`.

### Endpoints

```
GET    /api/usuarios/                             listado filtrado, buscable y paginado
POST   /api/usuarios/                             alta
GET    /api/usuarios/roles/                       roles para el desplegable
GET    /api/usuarios/<id>/                        detalle
PATCH  /api/usuarios/<id>/                        edición parcial
PUT    /api/usuarios/<id>/                        edición completa
PATCH  /api/usuarios/<id>/toggle-activo/          activar / inactivar
POST   /api/usuarios/<id>/restablecer-contrasena/ reset administrativo  (extensión)
POST   /api/usuarios/<id>/desbloquear/            levantar bloqueo CU1  (extensión)
DELETE /api/usuarios/<id>/                        405 — no hay borrado
```

### Frontend
Nada. Queda como siguiente paso.

---

## 3. 🧠 Decisiones técnicas tomadas

El detalle completo, con el motivo de cada una, está en
[`DECISIONS_LOG.md`](../DECISIONS_LOG.md) (decisiones 20 a 28). Las cinco que más
importan para la defense:

1. **No hay borrado.** El CU3 enumera "activación e inactivación", y `usuario` es
   referenciado por `bitacora`, `pedido`, `venta`, `compra`, `produccion` y
   `movimiento_economico`. Un DELETE físico destruiría el historial económico y
   dejaría la auditoría sin autor. La baja es `activo = false` y `DELETE` devuelve
   **405**, no 404: 404 diría "esta ruta no existe", 405 dice "el borrado está en la
   API y está prohibido por diseño".

2. **El permiso se lee de la tabla, no de `is_superuser`.** `TienePermiso` consulta
   `Usuario.get_permisos_nombres()`, que es el mismo método que viaja como claim
   `permisos` en el JWT. Que backend y frontend lean la misma fuente es lo que evita
   que la pantalla muestre un botón que el servidor va a rechazar.

3. **Cambiar rol, inactivar o restablecer la contraseña revoca las sesiones.** El
   JWT lleva el rol como claim, así que sin revocarlo la medida surte efecto recién a
   los 60 minutos. Se reutiliza `recuperacion.services.confirmacion.revocar_sesiones`
   en vez de escribir una segunda copia.

4. **La unicidad del nombre de usuario era falsa.** `unique=True` en PostgreSQL es
   "único Y DISTINTO DE MAYÚSCULAS", así que `Admin` y `admin` coexistían y, como el
   login resuelve por coincidencia exacta, una de las dos quedaba inaccesible para
   siempre. La migración agrega el índice sobre `Lower(...)`, con un `RunPython`
   previo que aborta con un mensaje legible si ya hubiera duplicados.

5. **La lógica de negocio vive en el servicio, no en la vista ni en el serializer.**
   Es el mismo criterio que ya se aplicó en CU1 con `CustomLoginView`. Ocultar un
   botón en el frontend es usabilidad, no seguridad: la API tiene que rechazar el
   intento aunque llegue por `curl`.

### Tres bugs reales encontrados por las pruebas

Ninguno se ve leyendo el código; los tres aparecieron al ejecutar.

- **`permission_classes = [TienePermiso('gestionar_usuarios')]` está mal.** DRF hace
  `permission()` sobre cada elemento de la lista, o sea que vuelve a instanciar lo que
  encuentra, y llamar a una instancia como si fuera un constructor lanza
  `TypeError: 'TienePermiso' object is not callable`. La forma correcta es
  sobreescribir `get_permissions()`.

- **DRF entrega la instancia `Rol`, no su id.** `Usuario(id_rol_id=<Rol: ...>)` falla
  con `TypeError: int() argument must be ... not 'Rol'`. Y el mismo descuido hacía que
  `editar_usuario` comparara un `Rol` contra un entero en la guarda de "no dejes el
  sistema sin Administradores", con lo que la guarda se disparaba en cada edición de
  una cuenta que sí tenía rol. Se normaliza con `_pk_de_rol()`.

- **`minutos_bloqueo_restantes` estaba declarado en el serializer de edición pero no
  en su `Meta.fields`.** DRF lo detecta con un `AssertionError` al construir los
  campos, que es una de esas validaciones que solo se ven en ejecución.

---

## 4. ⚠️ Pendientes o siguientes pasos

1. **Frontend del CU3** — `src/apps/dashboard/usuarios/`: tabla con buscador, filtros
   por rol y estado y paginación; modales de alta, edición, cambio de estado y
   reset de clave. Al crearlo, poner `implemented: true` en `navigation.ts` y
   registrar la ruta anidada en `AppRoutes.tsx`.

2. **CU4** — además del módulo propio, debe resolver la deriva entre el DDL y el
   modelo en `rol_permiso` (clave primaria compuesta en el DDL, implícita en Django).
   Queda documentada en el DDL y en la decisión 28.

3. **CU26** — los registros ya se escriben con las cuatro acciones nuevas, pero falta
   la pantalla de consulta.

4. **Permiso `CREATEDB`** — ver la sección siguiente. Es lo único que impide correr
   `manage.py test` contra PostgreSQL.

---

## 5. 🧪 Cómo probar lo implementado

### Verificación automática

```powershell
cd backend
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py test apps.usuarios_seguridad
```

**Estado actual de esta verificación:** `check` y `makemigrations --check` pasan en
verde. La suite da **144 pruebas en verde (1 se salta)**, pero corrió contra SQLite
en vez de PostgreSQL, porque el usuario de base de datos no tiene `CREATEDB`:

> `Got an error creating the test database: se ha denegado el permiso para crear la
> base de datos`

Para habilitarla, una sola vez, desde un usuario superusuario de PostgreSQL:

```sql
ALTER ROLE panaderia_admin CREATEDB;
```

Vale la pena hacerlo: la prueba
`test_la_base_rechaza_el_duplicado_por_mayusculas` depende del comportamiento del
índice de expresión, que SQLite no reproduce igual que PostgreSQL. La comparación de
`Lower()` sí se verificó a mano contra la base real: el índice rechaza `MGONZALES` y
acepta un nombre nuevo.

### Verificación manual

```powershell
cd backend
.\venv\Scripts\python.exe manage.py seed_usuarios
.\venv\Scripts\python.exe manage.py runserver
```

1. Loguearse como `admin` / `Admin123!` en `http://localhost:5173/login`.
2. Con ese token, `GET /api/usuarios/` debe devolver 200 con
   `{count, next, previous, results}`.
3. Con el token de `mgonzales` / `Admin123!` (Personal de Ventas), la misma llamada
   debe devolver **403**. Ahí está la prueba de que el RBAC no es decorativo.
4. `POST /api/usuarios/` con una contraseña débil debe devolver 400 con el detalle de
   la política.
5. `PATCH /api/usuarios/<id>/toggle-activo/` sobre la propia cuenta `admin` debe
   devolver 400.
6. `DELETE /api/usuarios/<id>/` debe devolver 405.
7. `GET /api/usuarios/?activo=false&search=Elena` debe filtrar y buscar.
8. Revisar `SELECT * FROM bitacora ORDER BY fecha_hora DESC;`: deben aparecer
   `ALTA_USUARIO`, `EDICION_USUARIO`, `CAMBIAR_ESTADO_USUARIO` y
   `RESTABLECER_CONTRASENA` según lo que se haya hecho.
