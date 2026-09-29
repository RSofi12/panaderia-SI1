# Estado Actual del Proyecto (CURRENT STATE)

## 📌 Proyecto: Sistema de Información Web — Panadería Santiago (SI-1)
**Fecha de última actualización:** 2026-09-28  
**Fase PUDS actual:** Fase de Construcción — **Ciclo 1**

---

## 📊 1. Resumen Ejecutivo de Avance

- **Arquitectura Base:** 100% Definida (Backend modular en 5 Django apps, Frontend React/TypeScript en Vite organizado por pantallas, Base de datos PostgreSQL normalizada).
- **Documentación de Ingeniería:** 100% Actualizada (Perfil, DDL de base de datos, memoria de IA en `docs/ai/`, bitácora de sesiones).
- **Backend:** Estructura de carpetas creada para los 5 paquetes en `backend/apps/`. **CU1 (login con JWT) y CU2 (recuperación de contraseña) completos, probados y verificados end-to-end contra PostgreSQL.** Preparado para la implementación de modelos ORM y endpoints del Ciclo 1.
- **Frontend:** Estructura base inicializada con Vite + React 19 + TypeScript + Tailwind CSS v4, **organizada por ventanas/pantallas** en `frontend/src/apps/`. Contiene la pantalla de Login (CU1), el **shell del dashboard** (`DashboardLayout` + `Sidebar` + `Topbar` + `DashboardHome`) con menú único filtrado por permisos RBAC, las dos pantallas del CU2 (`ForgotPasswordPage` y `ResetPasswordPage`) con `AuthCard` como envoltorio visual compartido, y la SPA completa de Gestión de Usuarios (CU3) en `src/apps/dashboard/usuarios/` con modales accesibles y CRUD completo. Cliente Axios con interceptores JWT, `AuthContext`/`AuthProvider` y rutas protegidas. `npm run lint` y `npm run build` verificados **en verde al 100% (0 errores, 0 advertencias)**.
- **Base de Datos:** Script DDL completo documentado en [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql).

---

## 🚦 2. Semáforo de Casos de Uso (26 Casos de Uso)

### 🟢 = Completado | 🟡 = En progreso / Siguiente a implementar | ⚪ = Planificado | 🟠 = Implementado pero sin verificar

### 📌 Ciclo 1 (7 Casos de Uso) — *Iteración Actual*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado | Detalle |
|---|---|---|:---:|---|
| **CU1** | Iniciar sesión | `apps.usuarios_seguridad` | 🟢 | **Completo end-to-end, con endurecimiento de seguridad.** Backend: endpoints `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/me/`, `/api/auth/logout/` con JWT, claims de roles/permisos y **revocación del refresh token** en el logout. **Política de bloqueo configurable:** sub-app `configuracion` con el modelo `ConfiguracionSeguridad` (singleton, 3 intentos / 10 minutos por defecto, editable desde el panel del Administrador) y lógica en `auth_app/services/politica_bloqueo.py`. Bloqueo Devuelve **HTTP 429** (con `Retry-After` y `retry_after_seconds`) y se evalúa **antes** de tocar la contraseña. El conteo usa `select_for_update()` dentro de una transacción, así que es correcto ante intentos simultáneos. **Anti-enumeración:** usuario inexistente y contraseña incorrecta devuelven el mismo mensaje y nunca se revela cuántos intentos quedan. **Anti-fuerza bruta por IP:** throttling `10/min` en login y `30/min` en refresh. **Auditoría de fallos:** `bitacora.id_usuario` ahora es nullable (`SET NULL`) y se agregó `nombre_usuario_intento`, por lo que los intentos fallidos —incluso contra usuarios inexistentes— quedan registrados. Las acciones de bitácora usan el enum controlado `AccionBitacora` y se registra también el `User-Agent`. **Validación de contraseña** lista en `users/password_validators.validar_contrasena()` para CU3. **31 pruebas automatizadas** en `auth_app/tests.py` en verde. Frontend: `src/apps/auth/LoginPage.tsx` con contador regresivo `mm:ss` y botón deshabilitado hasta que expire la ventana, `AuthProvider` con persistencia en `localStorage`, refresco automático ante `401` guardando también el refresh rotado, `ProtectedRoute` como guardia, redirección a `/dashboard` si ya hay sesión, y `DashboardLayout`/`DashboardHome` como destino post-login. El logout ahora envía el `refresh_token` para que la revocación sea efectiva. |
| **CU2** | Recuperar contraseña | `apps.usuarios_seguridad` | 🟢 | **Completo end-to-end (92 pruebas backend en verde, frontend compilado y verificado).** Sub-app `recuperacion` con modelo `TokenRecuperacion` (tabla `token_recuperacion`). Endpoints `/api/auth/password-reset-request/` y `/api/auth/password-reset-confirm/`, ambos sin autenticación. **Token de enlace de 20 caracteres** sobre alfabeto de 32 símbolos (~100 bits) generado con `secrets.choice()`; en la base solo se guarda el **SHA-256**, nunca el token en claro. **Un solo uso, con expiración (15 min) e invalidación del enlace anterior** al pedir uno nuevo. **Límites configurables** en `ConfiguracionSeguridad` (`minutos_expiracion_token`, `max_intentos_token`, `max_solicitudes_por_hora`, con CHECK en base) más throttling por IP (`5/min` y `15/min`). **Anti-enumeración estricta:** cuenta inexistente, inactiva y con la cuota agotada devuelven el mismo 200 y el mismo cuerpo; la diferencia solo queda en la bitácora. **Recuperación real, no simple cambio de clave:** levanta el bloqueo de cuenta y revoca todos los refresh tokens vivos. Correo multipart (texto + HTML) por SMTP configurable, con enlace a la ruta frontend `PASSWORD_RESET_URL`. **`Usuario.email` pasó a `NOT NULL`** y único sin distinguir mayúsculas (`Lower('email')`), con los 6 usuarios del seed usando correos de prueba `*.mail.com`. Se corrigió además un bug preexistente: `validar_contrasena()` nunca funcionó (se llamaba a sí misma con un keyword inexistente) y rompía CU2. **Candado de concurrencia verificado con dos conexiones reales de PostgreSQL:** dos confirmaciones simultáneas del mismo enlace → una gana, la otra se rechaza y ambas quedan auditadas. **Frontend implementado y validado con `npm run lint` y `npm run build` en verde:** `ForgotPasswordPage` (paso 1, mensaje genérico anti-enumeración) y `ResetPasswordPage` (paso 2, inicialización perezosa de token, limpieza de barra con `replaceState`, checklist vivo de política y separación de errores). Ambas rutas públicas en `AppRoutes.tsx`. `AuthCard` compartido, `PasswordRequirements` y `politicaContrasena.ts` desacoplados para Fast Refresh. |
| **CU3** | Gestionar usuarios | `apps.usuarios_seguridad` | 🟢 | **Completo end-to-end (52 pruebas backend en verde, frontend compilado y verificado con `npm run lint` y `npm run build`).** Endpoints `GET/POST /api/usuarios/`, `GET/PATCH /api/usuarios/<id>/`, `PATCH /api/usuarios/<id>/toggle-activo/`, más extensiones aprobadas `POST /api/usuarios/<id>/restablecer-contrasena/`, `POST /api/usuarios/<id>/desbloquear/` y `GET /api/usuarios/roles/`. **RBAC real:** `users/permissions.py` con `TienePermiso` (`gestionar_usuarios`). **Sin borrado:** la baja es `activo=false` y `DELETE` responde 405. **Guardas de auto-destrucción** en `users/services/usuarios.py`: nadie se inactiva a sí mismo, nadie se quita su propio rol y no se puede dejar el sistema sin ningún Administrador activo. **Revocación de sesiones** al cambiar rol, inactivar o restablecer contraseña. **Unicidad real sin distinguir mayúsculas:** índice `usuario_username_unico_ci` sobre `Lower(nombre_usuario)`. **Auditoría** con cuatro acciones en `AccionBitacora` (`ALTA_USUARIO`, `EDICION_USUARIO`, `CAMBIAR_ESTADO_USUARIO`, `RESTABLECER_CONTRASENA`) y desbloqueo con `DESBLOQUEO_CUENTA`. **Frontend completo en `src/apps/dashboard/usuarios/`:** `UsuariosPage.tsx` con listado paginado, búsqueda con debounce de 300 ms, filtros combinados por estado y rol, y orden estable; `UsuariosTabla.tsx` con estados de carga (esqueleto animado), badges textuales para daltonismo, tabla accesible con scroll horizontal, y acciones de editar, clave, activar/inactivar y desbloquear; modales accesibles (`ModalUsuario.tsx`, `ModalEstado.tsx`, `ModalRestablecerContrasena.tsx`) basados en `Modal.tsx` con focus trap, focus restoration, `useId`, Escape, bloqueo de scroll y `aria-modal="true"`; inicializadores lazy y `key` por usuario para render sin efectos de reseteo; `navigation.ts` con `implemented: true` y tarjeta de acceso directo en `DashboardHome.tsx`. |
| **CU4** | Asignar roles y permisos | `apps.usuarios_seguridad` | 🟢 | **Completo end-to-end (18 pruebas específicas de roles/permisos + 52 de usuarios en verde, frontend compilado y verificado con `npm run build` en 0 errores).** Backend: `permisos.models.Permiso` con enum `modulo` (`ModuloPermiso.TextChoices`) y restricción única insensible a mayúsculas; `roles.models.Rol` y `RolPermiso` con métodos UML `asignar_permiso()`, `quitar_permiso()`, `UniqueConstraint(Lower('nombre'))` e índice único en `RolPermiso`. Capa de servicios `roles/services/matriz.py` bajo `@transaction.atomic` con 4 guardas anti-autobloqueo, inmutabilidad de roles base (`Administrador`, `Propietario`, `Personal de Ventas`, `Personal de Producción`), prohibición de `DELETE` (405) y auditoría con diff en `Bitacora` (`ALTA_ROL`, `EDICION_ROL`, `ASIGNAR_PERMISO_ROL`, `REVOCAR_PERMISO_ROL`, `ACTUALIZACION_MATRIZ_PERMISOS`). Endpoints `GET/POST /api/roles/`, `GET/PATCH /api/roles/<id>/`, `PUT /api/roles/<id>/permisos/`, `POST /api/roles/<id>/permisos/asignar/`, `POST /api/roles/<id>/permisos/quitar/`, `GET /api/permisos/` y `/api/permisos/agrupados/`. Seed actualizado con 12 permisos clasificados en 5 módulos funcionales. Frontend: pestaña unificada "Roles y permisos" en `/dashboard/usuarios` sincronizada por URL (`?tab=roles`), `RolesTab.tsx` con KPI cards de resumen y filtros por segmento (`Todos`, `Sistema`, `Personalizados`), `TarjetaRol.tsx` con avatares temáticos de personal de panadería y barras de cobertura progresiva, `MatrizPermisosModal.tsx` con buscador de permisos interactivo, botones por lote por módulo ("Marcar/Desmarcar módulo") y guarda visual contra auto-bloqueo del Administrador, y `ModalRol.tsx` con contadores de caracteres y foco accesible. |
| **CU26**| Gestionar bitácora (versión simple) | `apps.usuarios_seguridad` | 🟢 | Sub-app `bitacora` implementada y vinculada a eventos de login/logout y auditoría. |
| **CU5** | Gestionar productos (catálogo base) | `apps.productos_inventario`| ⚪ | Planificado en Ciclo 1 |
| **CU6** | Gestionar proveedores (catálogo base)| `apps.compras` | ⚪ | Planificado en Ciclo 1 |

---

### 📌 Ciclo 2 (6 Casos de Uso) — *Planificado*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado |
|---|---|---|:---:|
| **CU7** | Registrar compra de materia prima | `apps.compras` | ⚪ |
| **CU8** | Consultar stock de materia prima | `apps.productos_inventario` | ⚪ |
| **CU9** | Consultar alertas de bajo stock | `apps.productos_inventario` | ⚪ |
| **CU10**| Registrar producción diaria | `apps.productos_inventario` | ⚪ |
| **CU11**| Consultar historial de producción | `apps.productos_inventario` | ⚪ |
| **CU12**| Consultar existencias de productos terminados | `apps.productos_inventario` | ⚪ |

---

### 📌 Ciclo 3 (7 Casos de Uso) — *Planificado*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado |
|---|---|---|:---:|
| **CU13**| Registrar venta | `apps.comercializacion` | ⚪ |
| **CU14**| Registrar pedido | `apps.comercializacion` | ⚪ |
| **CU15**| Consultar estado de pedido | `apps.comercializacion` | ⚪ |
| **CU16**| Generar comprobante de venta | `apps.comercializacion` | ⚪ |
| **CU17**| Consultar disponibilidad de productos | `apps.comercializacion` | ⚪ |
| **CU18**| Registrar baja de productos terminados | `apps.productos_inventario` | ⚪ |
| **CU19**| Consultar historial de precios | `apps.productos_inventario` | ⚪ |

---

### 📌 Ciclo 4 (6 Casos de Uso) — *Planificado*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado |
|---|---|---|:---:|
| **CU20**| Registrar gasto / inversión | `apps.compras` | ⚪ |
| **CU21**| Generar reporte de ventas | `apps.reportes` | ⚪ |
| **CU22**| Generar reporte de producción | `apps.reportes` | ⚪ |
| **CU23**| Generar reporte de existencias | `apps.reportes` | ⚪ |
| **CU24**| Generar reporte de compras y gastos | `apps.reportes` | ⚪ |
| **CU25**| Generar reporte de resultados económicos | `apps.reportes` | ⚪ |

---

## 🎯 3. Próximos Pasos Inmediatos
1. **Implementar modelos base y endpoints de `productos_inventario` (CU5)** y `compras` (CU6) en el backend (catálogos de productos y proveedores).
2. **Crear pantalla del catálogo de productos (CU5)** en `src/apps/dashboard/productos/` y conectar su navegación.
3. **Probar el flujo completo con Mailpit** (CU2): agregar el bloque `EMAIL_*` a `backend/.env`, levantar Mailpit, y recorrer login → "¿Olvidaste tu contraseña?" → correo en `http://localhost:8025` → contraseña nueva → login.
4. **Correr `manage.py purgar_tokens_vencidos --dry-run`** y después sin la bandera, para confirmar que el comando funciona antes de agendarlo con el Programador de tareas.
5. **Alinear el seed con la matriz de actores**: quitar `generar_reportes` al Personal de Ventas en `seed_usuarios.py` para cumplir con `PACKAGE_CU_MAP.md`.
6. **Crear `src/components/`** con los primeros átomos compartidos de nivel global (`Button`, `Input`, `Badge`) cuando una segunda app los requiera fuera del dashboard.

### ⚠️ Deuda técnica conocida

- **El usuario de PostgreSQL no tiene permiso `CREATEDB`**, por lo que `manage.py test` falla al crear la base de datos de pruebas. Solución: `ALTER ROLE <usuario> CREATEDB;` en PostgreSQL, o ejecutar la suite con el ajuste temporal de SQLite.
- **Mailpit v1.31.3 ya está descargado** en `C:\Users\PERSONAL\tools\mailpit\mailpit.exe` (portable, fuera del repositorio), pero **no está corriendo**: el `EMAIL_BACKEND=smtp` de `.env` no tiene contra qué enviar.
- Sin suite de tests automatizados en el frontend (el backend tiene **144 pruebas** en verde sobre SQLite).
- `seed_usuarios` vs `PACKAGE_CU_MAP.md` — `generar_reportes` en Personal de Ventas pendiente de ajuste antes del Ciclo 4.

### ✅ Deuda técnica resuelta

- ~~Frontend del CU2 y CU3 sin compilar / errores de lint~~ → Resuelto: `npm run lint` y `npm run build` pasan al 100% en verde con 0 errores y 0 advertencias. Se corrigieron los hooks, se extrajeron funciones fuera de componentes para Fast Refresh de Vite (`politicaContrasena.ts`, `estilosFormulario.ts`), se utilizó `useId` y lazy initializers con `key` en modales.
- ~~Frontend CU3 pendiente~~ → Implementado al 100% en `src/apps/dashboard/usuarios/` con listado paginado, búsqueda con debounce, filtros, alta/edición, activación/inactivación, reseteo de contraseña y desbloqueo.
- ~~`LoginPage.tsx` — "¿Olvidaste tu contraseña?" sin enlace~~ → Implementado con `<Link to="/recuperar-password">`.

- ~~Sin bloqueo por intentos de login~~ → Implementado: política configurable en la tabla `configuracion_seguridad` (3 intentos / 10 min), lógica en `auth_app/services/politica_bloqueo.py`, respuesta **HTTP 429** (con `Retry-After`) evaluada antes de autenticar, conteo protegido con `select_for_update()` y expiración perezosa sin tarea programada.
- ~~Intentos fallidos invisibles en la bitácora~~ → `bitacora.id_usuario` es nullable con `SET NULL` y se agregó `nombre_usuario_intento`. Ahora se auditan `LOGIN_FALLIDO`, `ACCESO_BLOQUEADO` y `ACCESO_DENEGADO`, incluso contra usuarios inexistentes.
- ~~El logout no invalidaba nada~~ → `rest_framework_simplejwt.token_blacklist` instalada, `BLACKLIST_AFTER_ROTATION: True` y `LogoutView` revoca el token recibido. El frontend ya lo envía.
- ~~Sin rate limiting~~ → Throttling `10/min` en login y `30/min` en refresh, dentro de `REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`.
- ~~`{error: "..."} llegaba al frontend como array~~ → `as_serializer_error()` de DRF convertía todo dict de un `ValidationError` en `{key: [value]}`. Los errores de auth ahora usan `APIException`, que viaja intacta.
- ~~`DEFAULT_THROTTLE_RATES` en el nivel equivocado de settings~~ → DRF solo lee la clave dentro de `REST_FRAMEWORK`; fuera de ella se ignora en silencio.
- ~~`last_login` nunca se actualizaba~~ → El flujo JWT de DRF no pasa por `django.contrib.auth.login()`, que es lo que dispara la señal `update_last_login`. Se actualiza explícitamente en `registrar_intento_exitoso()`.
- ~~El login revalidaba dos veces~~ → La vista volvía a ejecutar la validación completa del serializador para conocer al usuario. La auditoría se movió al serializador y la vista quedó sin `post()`.
- ~~La secuencia `usuario_id_usuario_seq` estaba desfasada~~ → Estaba en 1 con 6 usuarios existentes, por lo que **todo INSERT de usuario fallaba** con violación de PK. Sincronizada con `setval`. El DDL maestro debería declarar la PK como `bigserial`/`GENERATED BY DEFAULT AS IDENTITY` y el seed hacer `setval` tras insertar.
- ~~`ProtectedRoute.tsx` — doble retorno en conflicto~~ → Corregido: cada rama tiene un `return` único; la de permiso denegado renderiza `AccessDenied` con botón "Volver al panel" en vez de redirigir a ciegas.
- ~~Texto de política de contraseña visible desde el primer render~~ → Corregido: solo aparece tras un intento fallido (estado `showPasswordPolicy`).
- ~~Usuario autenticado podía volver a ver `/login`~~ → Corregido: `LoginPage` redirige a `/dashboard` si `isAuthenticated`.
- ~~`validar_contrasena()` nunca funcionó~~ → Corregido: el nombre local `validate_password` tapaba al import de Django y la función se llamaba a sí misma con el keyword `usuario=`, que no existe, reventando con `TypeError` al primer uso. Nadie la llamaba, así que el bug llevaba tiempo latente; CU2 fue el primer consumidor. El import se aliaseó como `validar_con_politica_de_django` y se invoca con `user=`. Esto además confirma que la política de contraseñas del CU3 ya es utilizable.
- ~~La recuperación de contraseña no tenía anti-enumeración real~~ → La cuota por cuenta devolvía 429 solo para cuentas reales, lo que bastaba para enumerarlas. Ahora todos los casos (inexistente, inactiva, cuota agotada) devuelven el mismo 200; la cuota se sigue contando y simplemente no se envía correo.
- ~~Una confirmación con token inexistente daba 500~~ → `auditar_token_rechazado()` dereferenciaba `fila.id_token` fuera del condicional que sí protegía el resto. Ahora un token inventado responde 400 y queda auditado.
- ~~Un permiso de DRF con parámetro reventaba al arrancar~~ → `permission_classes = [TienePermiso('gestionar_usuarios')]` es la forma obvia y está **mal**: `APIView.get_permissions()` hace `permission()` sobre cada elemento de la lista, o sea que vuelve a instanciar lo que encuentra, y llamar a una instancia como si fuera un constructor lanza `TypeError: 'TienePermiso' object is not callable`. La forma correcta es sobreescribir `get_permissions()` y devolver `[TienePermiso('gestionar_usuarios')]`.
- ~~`id_rol` reventaba en toda alta de usuario~~ → DRF mete en `validated_data` la **instancia** `Rol`, no su id, y `Usuario(id_rol_id=<Rol: ...>)` falla con `TypeError: int() argument must be ... not 'Rol'`. El servicio ahora normaliza con `_pk_de_rol()`. El mismo descuido comparaba un `Rol` contra un entero en la guarda "no dejes el sistema sin Administradores", lo que la hacía dispararse en cada edición.
- ~~La unicidad del nombre de usuario no era real~~ → `unique=True` en PostgreSQL es "único Y DISTINTO DE MAYÚSCULAS", así que `Admin` y `admin` coexistían y, como el login resuelve por coincidencia exacta, una de las dos quedaba inaccesible. Migración `users/0005` con el índice `usuario_username_unico_ci` sobre `Lower(nombre_usuario)`, más un `RunPython` previo que aborta con un mensaje legible si ya hubiera duplicados.
