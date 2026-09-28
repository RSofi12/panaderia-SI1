# Estado Actual del Proyecto (CURRENT STATE)

## 📌 Proyecto: Sistema de Información Web — Panadería Santiago (SI-1)
**Fecha de última actualización:** 2026-09-28  
**Fase PUDS actual:** Fase de Construcción — **Ciclo 1**

---

## 📊 1. Resumen Ejecutivo de Avance

- **Arquitectura Base:** 100% Definida (Backend modular en 5 Django apps, Frontend React/TypeScript en Vite organizado por pantallas, Base de datos PostgreSQL normalizada).
- **Documentación de Ingeniería:** 100% Actualizada (Perfil, DDL de base de datos, memoria de IA en `docs/ai/`, bitácora de sesiones).
- **Backend:** Estructura de carpetas creada para los 5 paquetes en `backend/apps/`. **CU1 (login con JWT) y CU2 (recuperación de contraseña) completos, probados y verificados end-to-end contra PostgreSQL.** Preparado para la implementación de modelos ORM y endpoints del Ciclo 1.
- **Frontend:** Estructura base inicializada con Vite + React 19 + TypeScript + Tailwind CSS v4, **organizada por ventanas/pantallas** en `frontend/src/apps/`. Contiene la pantalla de Login (CU1), el **shell del dashboard** (`DashboardLayout` + `Sidebar` + `Topbar` + `DashboardHome`) con menú único filtrado por permisos RBAC, y las dos pantallas del CU2 (`ForgotPasswordPage` y `ResetPasswordPage`) con `AuthCard` como envoltorio visual compartido. Cliente Axios con interceptores JWT, `AuthContext`/`AuthProvider` y rutas protegidas. `npm run lint` y `npm run build` estaban en verde **antes** de los cambios del CU2; desde entonces no se volvió a correr ninguno de los dos.
- **Base de Datos:** Script DDL completo documentado en [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql).

---

## 🚦 2. Semáforo de Casos de Uso (26 Casos de Uso)

### 🟢 = Completado | 🟡 = En progreso / Siguiente a implementar | ⚪ = Planificado | 🟠 = Implementado pero sin verificar

### 📌 Ciclo 1 (7 Casos de Uso) — *Iteración Actual*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado | Detalle |
|---|---|---|:---:|---|
| **CU1** | Iniciar sesión | `apps.usuarios_seguridad` | 🟢 | **Completo end-to-end, con endurecimiento de seguridad.** Backend: endpoints `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/me/`, `/api/auth/logout/` con JWT, claims de roles/permisos y **revocación del refresh token** en el logout. **Política de bloqueo configurable:** sub-app `configuracion` con el modelo `ConfiguracionSeguridad` (singleton, 3 intentos / 10 minutos por defecto, editable desde el panel del Administrador) y lógica en `auth_app/services/politica_bloqueo.py`. Bloqueo Devuelve **HTTP 429** (con `Retry-After` y `retry_after_seconds`) y se evalúa **antes** de tocar la contraseña. El conteo usa `select_for_update()` dentro de una transacción, así que es correcto ante intentos simultáneos. **Anti-enumeración:** usuario inexistente y contraseña incorrecta devuelven el mismo mensaje y nunca se revela cuántos intentos quedan. **Anti-fuerza bruta por IP:** throttling `10/min` en login y `30/min` en refresh. **Auditoría de fallos:** `bitacora.id_usuario` ahora es nullable (`SET NULL`) y se agregó `nombre_usuario_intento`, por lo que los intentos fallidos —incluso contra usuarios inexistentes— quedan registrados. Las acciones de bitácora usan el enum controlado `AccionBitacora` y se registra también el `User-Agent`. **Validación de contraseña** lista en `users/password_validators.validar_contrasena()` para CU3. **31 pruebas automatizadas** en `auth_app/tests.py` en verde. Frontend: `src/apps/auth/LoginPage.tsx` con contador regresivo `mm:ss` y botón deshabilitado hasta que expire la ventana, `AuthProvider` con persistencia en `localStorage`, refresco automático ante `401` guardando también el refresh rotado, `ProtectedRoute` como guardia, redirección a `/dashboard` si ya hay sesión, y `DashboardLayout`/`DashboardHome` como destino post-login. El logout ahora envía el `refresh_token` para que la revocación sea efectiva. |
| **CU2** | Recuperar contraseña | `apps.usuarios_seguridad` | 🟠 | **Backend completo y verificado end-to-end (92 pruebas en verde, 1 se salta sin PostgreSQL).** Sub-app `recuperacion` con modelo `TokenRecuperacion` (tabla `token_recuperacion`). Endpoints `/api/auth/password-reset-request/` y `/api/auth/password-reset-confirm/`, ambos sin autenticación. **Token de enlace de 20 caracteres** sobre alfabeto de 32 símbolos (~100 bits) generado con `secrets.choice()`; en la base solo se guarda el **SHA-256**, nunca el token en claro. **Un solo uso, con expiración (15 min) e invalidación del enlace anterior** al pedir uno nuevo. **Límites configurables** en `ConfiguracionSeguridad` (`minutos_expiracion_token`, `max_intentos_token`, `max_solicitudes_por_hora`, con CHECK en base) más throttling por IP (`5/min` y `15/min`). **Anti-enumeración estricta:** cuenta inexistente, inactiva y con la cuota agotada devuelven el mismo 200 y el mismo cuerpo; la diferencia solo queda en la bitácora. **Recuperación real, no simple cambio de clave:** levanta el bloqueo de cuenta y revoca todos los refresh tokens vivos. Correo multipart (texto + HTML) por SMTP configurable, con enlace a la ruta frontend `PASSWORD_RESET_URL`. **`Usuario.email` pasó a `NOT NULL`** y único sin distinguir mayúsculas (`Lower('email')`), con los 6 usuarios del seed usando correos de prueba `*.mail.com`. Se corrigió además un bug preexistente: `validar_contrasena()` nunca funcionó (se llamaba a sí misma con un keyword inexistente) y rompía CU2. **Candado de concurrencia verificado con dos conexiones reales de PostgreSQL:** dos confirmaciones simultáneas del mismo enlace → una gana, la otra se rechaza y ambas quedan auditadas; el `raise` que informa el conflicto se sacó de la transacción porque el rollback borraba el registro de bitácora. **Frontend implementado, sin verificar todavía:** `ForgotPasswordPage` (paso 1, muestra siempre el mensaje genérico para no romper la anti-enumeración) y `ResetPasswordPage` (paso 2, lee el token de la URL y lo borra de la barra con `replaceState`, muestra el checklist vivo de la política y separa errores de campo de errores de negocio). Ambas rutas públicas registradas en `AppRoutes.tsx`. Se extrajo `AuthCard` como envoltorio visual compartido por las tres pantallas públicas y el "¿Olvidaste tu contraseña?" del login pasó de `<span>` muerto a `<Link>` real. El panel de cuentas demo quedó condicionado a `import.meta.env.DEV` para que no se publique en el build de producción. **Pendiente de validación:** por indicación del usuario no se corrieron `npm run build`, `npm run lint` ni `tsc`. **En lugar de Celery:** comando `manage.py purgar_tokens_vencidos` (con `--dry-run` y `-v`) para limpiar tokens vencidos, agendable con el Programador de tareas de Windows. **Mailpit v1.31.3** descargado en `C:\Users\PERSONAL\tools\mailpit\mailpit.exe` para probar el envío SMTP real. |
| **CU3** | Gestionar usuarios | `apps.usuarios_seguridad` | 🟡 | **Backend completo y verificado (52 pruebas propias en verde); falta el frontend.** Endpoints `GET/POST /api/usuarios/`, `GET/PATCH /api/usuarios/<id>/`, `PATCH /api/usuarios/<id>/toggle-activo/`, más las extensiones aprobadas `POST /api/usuarios/<id>/restablecer-contrasena/`, `POST /api/usuarios/<id>/desbloquear/` y `GET /api/usuarios/roles/`. **RBAC real:** `users/permissions.py` con `TienePermiso`, que lee el catálogo `gestionar_usuarios` de `rol_permiso` vía `Usuario.get_permisos_nombres()`; un `Personal de Ventas` recibe 403 y uno sin rol también. **Sin borrado:** la baja es `activo=false` y `DELETE` devuelve 405, porque `usuario` es referenciado por `bitacora`, `pedido`, `venta`, `compra`, `produccion` y `movimiento_economico`. **Guardas de auto-destrucción** en `users/services/usuarios.py`: nadie se inactiva a sí mismo, nadie se quita su propio rol y no se puede dejar el sistema sin ningún Administrador activo. **Revocación de sesiones** al cambiar rol, inactivar o restablecer contraseña, reutilizando `recuperacion.services.confirmacion.revocar_sesiones`, porque el JWT lleva el rol como *claim* y sin revocarlo la medida surte efecto recién a los 60 minutos. **Unicidad real sin distinguir mayúsculas:** migración `users/0005` con el índice `usuario_username_unico_ci` sobre `Lower(nombre_usuario)` y un `RunPython` previo que aborta con un mensaje legible si ya existieran cuentas que solo difieran en mayúsculas. **Auditoría** con cuatro acciones nuevas en `AccionBitacora` (`ALTA_USUARIO`, `EDICION_USUARIO`, `CAMBIAR_ESTADO_USUARIO`, `RESTABLECER_CONTRASENA`); el desbloqueo reutiliza `DESBLOQUEO_CUENTA` de CU1. **Listado** con paginación, `SearchFilter` y `OrderingFilter` de DRF, y sin N+1 gracias a `select_related` + `prefetch_related`. **Pendiente:** la SPA `src/apps/dashboard/usuarios/`. |
| **CU4** | Asignar roles y permisos | `apps.usuarios_seguridad` | 🟡 | Sub-apps `permisos` y `roles` listas con modelos `Permiso`, `Rol`, `RolPermiso`. |
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
1. **Correr `npm run build` y `npm run lint` en `frontend/`**: el frontend del CU2 está escrito pero nunca compilado (ver deuda técnica). Es el paso que convierte CU2 en 🟢.
2. **Probar el flujo completo con Mailpit** (CU2): agregar el bloque `EMAIL_*` a `backend/.env`, levantar Mailpit, y recorrer login → "¿Olvidaste tu contraseña?" → correo en `http://localhost:8025` → contraseña nueva → login. Al final, reusar el mismo enlace para comprobar el 400.
3. **Correr `manage.py purgar_tokens_vencidos --dry-run`** y después sin la bandera, para confirmar que el comando de la segunda tanda funciona antes de agendarlo.
4. **Crear `src/apps/dashboard/usuarios/`** (CU3, CU4, CU26): es el primer módulo real y el que desbloquea el Ciclo 1. Al crearlo, poner `implemented: true` en su entrada de `navigation.ts` y registrar la ruta anidada en `AppRoutes.tsx`.
5. **Alinear el seed con la matriz de actores**: `seed_usuarios` da `generar_reportes` al Personal de Ventas, pero `PACKAGE_CU_MAP.md` asigna CU21–CU25 solo al Propietario. Decidir antes del Ciclo 4.
6. **Crear `src/components/`** con los primeros átomos compartidos: `Button`, `Input`, `Modal`, `DataTable`, `Badge`. `UserAvatar` ya existe en `apps/dashboard/components/` y conviene promoverlo cuando lo use una segunda pantalla. `AuthCard` y `PasswordRequirements` viven en `apps/auth/components/` porque hoy solo los usan pantallas de auth; si el patrón se repite en otro módulo, ese es el momento de promoverlos.
7. **Implementar modelos base** de `productos_inventario` (CU5) y `compras` (CU6) en el backend.

### ⚠️ Deuda técnica conocida

- **Frontend del CU2 sin compilar.** `ForgotPasswordPage`, `ResetPasswordPage`, `AuthCard`, `PasswordRequirements`, los cuatro archivos modificados y el comando `purgar_tokens_vencidos` no se ejecutaron ni una vez. El código se validó por lectura y contraste contra el backend. Riesgo concreto: el `useEffect` de `ResetPasswordPage` que limpia la URL lleva un `eslint-disable` para `react-hooks/exhaustive-deps`, y ese mismo archivo es el que puede dar problemas de tipos con `searchParams` tras la limpieza. También puede haber quedado un import sin usar en `ForgotPasswordPage` si `Navigate` no se referencia en algún camino de render.
- `LoginPage.tsx` — "¿Olvidaste tu contraseña?" es un `<span>` sin `onClick`, no navega a ninguna parte (ver paso 3).
- `seed_usuarios` vs `PACKAGE_CU_MAP.md` — desacuerdo sobre quién tiene `generar_reportes` (ver paso 4). **El equipo ya confirmó que los reportes (CU21–CU25) son exclusivos del Propietario**, así que corresponde quitar `generar_reportes` al Personal de Ventas en `seed_usuarios.py`.
- `AuthProvider.hasPermission` — atajo de cliente `if (user.rol === 'Administrador') return true;`. Es válido como UX, pero el backend sigue siendo la autoridad; conviene recordarlo al implementar los permisos de DRF.
- Sin suite de tests automatizados en el frontend (el backend tiene **92 pruebas**: 31 de CU1 en `auth_app/tests.py` y 61 de CU2 en `recuperacion/tests.py`, de las cuales 1 se salta sin PostgreSQL).
- **El usuario de PostgreSQL no tiene permiso `CREATEDB`**, por lo que `manage.py test` falla al crear la base de datos de pruebas. Solución: `ALTER ROLE <usuario> CREATEDB;` en PostgreSQL, o ejecutar la suite con el ajuste temporal de SQLite.
- El DDL maestro `docs/informes/Database_Panaderia_Santiago.sql` **ya incluye CU2** (`token_recuperacion` con sus CHECK e índices, los tres parámetros nuevos de `configuracion_seguridad`, y `usuario.email` como `NOT NULL` con índice único sobre `Lower("email")`), contrastado contra el esquema real de PostgreSQL.
- **Mailpit v1.31.3 ya está descargado** en `C:\Users\PERSONAL\tools\mailpit\mailpit.exe` (portable, fuera del repositorio), pero **no está corriendo**: el `EMAIL_BACKEND=smtp` de `.env` no tiene contra qué enviar. Para levantarlo: `mailpit.exe --smtp 0.0.0.0:1025 --listen 0.0.0.0:8025`, y la bandeja se abre en `http://localhost:8025`. Las pruebas automatizadas usan el backend `locmem` de Django y la verificación manual se hizo con el backend de consola.
- **El frontend del CU2 está escrito pero nunca se compiló.** Por indicación del usuario no se corrieron `npm run build`, `npm run lint` ni `tsc`: los cuatro archivos nuevos y los cuatro modificados se revisaron leyéndolos y contrastándolos contra el backend (rutas de `auth_app/urls.py`, contrato de `auth_app/serializers.py` y regex de `users/password_validators.py`), no ejecutándolos. El primer `npm run build` puede sacar errores de tipos o de lint que recién ahora se verán.
- **El comando `purgar_tokens_vencidos` no se ejecutó ni una vez**, ni siquiera con `--dry-run`. Es lo primero que conviene correr antes de agendarlo con el Programador de tareas. Y conviene recordar su alcance: la expiración ya la aplica `buscar_por_token()` en cada confirmación, así que purgar es higiene de tabla, no un control de seguridad.
- **No hay Celery en el proyecto y no se agregó.** La purga periódica quedó como comando de gestión, agendable con el Programador de tareas de Windows. Si más adelante hace falta trabajo asíncrono de verdad (envío con reintentos, generación de PDF pesadas), ahí sí evaluarlo como decisión de arquitectura aparte.
- **La corrección del lock de CU2 está verificada con dos conexiones reales de PostgreSQL** (no queda como revisión manual). Al confirmar el mismo enlace desde dos hilos a la vez, exactamente una gana y la otra se rechaza; el token queda con `usado_en` y `intentos=1`, y quedan `1` registro de `RECUPERACION_CONFIRMADA` más `1` de `RECUPERACION_INVALIDADA`. La prueba se cubre en `PruebasConcurrenciaReal` (solo PostgreSQL) y `PruebasAuditoriaAnteConflicto` (cualquier motor). Sigue siendo cierto que la suite del día a día corre sobre SQLite y por eso la clase de concurrencia se salta allí.
- **La cuota por cuenta de CU2 ya no da feedback al usuario legítimo.** Al agotarse, la respuesta es el 200 genérico (por anti-enumeración) y no se envía correo, así que quien pide tres veces porque se equivocó de correo no se entera de por qué. El motivo queda solo en la bitácora. Si molesta en la práctica, la salida es un aviso dentro del propio correo, nunca un 429.

### ✅ Deuda técnica resuelta

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
