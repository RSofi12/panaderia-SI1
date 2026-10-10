# Registro de Decisiones Técnicas y Arquitectónicas (DECISIONS LOG)

## 📌 Proyecto: Sistema de Información Web — Panadería Santiago (SI-1)

---

## 📅 2026-09-26 — Estructura modular de 5 paquetes backend
- **Decisión:** Organizar el backend en exactamente 5 Django apps (`usuarios_seguridad`, `productos_inventario`, `compras`, `comercializacion`, `reportes`).
- **Motivo:** En versiones previas se consideraba separar catálogo de insumos de la producción. Se decidió unificarlos en `productos_inventario` para mantener un número balanceado de módulos (5 paquetes) y facilitar la trazabilidad entre materia prima, receta/producción y pan horneado.
- **Impacto:** Menor complejidad en migraciones y llaves foráneas cruzadas, cumpliendo con la distribución formal de 26 Casos de Uso en 4 ciclos PUDS.

---

## 📅 2026-09-26 — Alcance y priorización del Ciclo 1 (7 Casos de Uso)
- **Decisión:** El Ciclo 1 implementa CU1 (Iniciar sesión), CU2 (Recuperar contraseña), CU3 (Gestionar usuarios), CU4 (Asignar roles y permisos), CU26 (Gestionar bitácora) en `usuarios_seguridad`, junto con los catálogos base CU5 (Gestionar productos) en `productos_inventario` y CU6 (Gestionar proveedores) en `compras`.
- **Motivo:** Garantizar la autenticación, seguridad RBAC y los datos maestros (productos y proveedores) antes de programar los procesos transaccionales de compras y producción diaria del Ciclo 2.
- **Impacto:** Permite validar la arquitectura base, la conexión con PostgreSQL y el login desde el frontend React desde la primera entrega.

---

## 📅 2026-09-26 — Clientes y Proveedores como entidades de datos (Sin Login)
- **Decisión:** Los clientes que compran en mostrador o hacen pedidos, y los proveedores de materia prima, son entidades de datos administradas por el personal. No cuentan con usuario, contraseña ni acceso al panel del sistema.
- **Motivo:** El alcance del sistema es de gestión interna operativa y administrativa para la panadería. No es un e-commerce abierto al público general.
- **Impacto:** Simplifica la seguridad y evita exponer endpoints públicos de registro (`/auth/register/`). Los roles se limitan a: Administrador, Propietario, Ventas y Producción.

---

## 📅 2026-09-26 — PostgreSQL 14+ y Bitácora de Auditoría
- **Decisión:** Utilizar PostgreSQL como motor relacional con soporte para llaves foráneas en cascada controlada y tabla `bitacora` para auditoría (CU26).
- **Motivo:** Cumplimiento de requerimientos de la materia SI-1 y preservación de la integridad transaccional del negocio.
- **Impacto:** Las operaciones críticas (creación/edición de usuarios, cambios de precios, registros de producción y ventas) quedan registradas con fecha, hora, responsable y acción efectuada.

---

## 📅 2026-09-26 — Postergación de Dockerización tras el Ciclo 1
- **Decisión:** Trabajar el Ciclo 1 en entorno local directo (`python -m venv venv` y `npm install`) y postergar la configuración de Docker/Docker Compose para etapas posteriores.
- **Motivo:** Priorizar la velocidad de desarrollo de los primeros 7 casos de uso y la familiarización del equipo con el código sin fricciones de configuración de contenedores.
- **Impacto:** La documentación de puesta en marcha refleja comandos locales directos y uso de variables de entorno `.env`.

---

## 📅 2026-09-27 — Modularización por Sub-Apps en `usuarios_seguridad` y Modelo Custom
- **Decisión:** Dividir internamente el paquete `usuarios_seguridad` en sub-apps especializadas (`permisos`, `roles`, `users`, `bitacora`, `auth_app`), manteniendo la pertenencia al Paquete 1 de PUDS.
- **Motivo:** Evitar archivos monolíticos (`models.py`, `views.py`) de gran tamaño, otorgando a cada entidad su propio ciclo de vida, modelos, validadores y serializadores.
- **Impacto:** `Usuario` hereda de `AbstractBaseUser` mapeando la columna `hash_contrasena` con Django y `AUTH_USER_MODEL = 'users.Usuario'`.

---

## 📅 2026-09-27 — Política Estricta de Validación de Contraseñas
- **Decisión:** Implementar `ComplexPasswordValidator` en `apps.usuarios_seguridad.users.password_validators`.
- **Motivo:** Requisito de seguridad para garantizar que todas las contraseñas contengan un mínimo de 8 caracteres, al menos 1 letra mayúscula, al menos 1 dígito numérico y al menos 1 carácter especial (`!=@#%`, etc.).
- **Impacto:** Se aplica tanto en el backend a través de `AUTH_PASSWORD_VALIDATORS` como en el endpoint de autenticación y creación de usuarios.

---

## 📅 2026-09-27 — Organización del Frontend por Pantallas (`src/apps/`)
- **Decisión:** El frontend se organiza por **ventanas / flujo visual del usuario** en `frontend/src/apps/`, mientras que el backend se mantiene organizado por **paquetes de dominio** en `backend/apps/`. Se renombra `src/pages/` → `src/apps/`. Las carpetas de pantalla de los módulos futuros (`usuarios/`, `productos/`, `compras/`, `ventas/`, `reportes/`) se crean **bajo demanda**, al implementar su CU, no como placeholders vacías.
- **Motivo:** La asimetría es deliberada y responde a dos interfaces distintas. El backend razona en términos de la base de datos y la lógica de negocio (una misma regla sirve a varios CUs y varias pantallas, y unificarla evita duplicación). El frontend razona en términos de navegación y permisos: una pantalla es una unidad que el usuario abre y que el RBAC debe poder ocultar. Alinear el nombre de la carpeta del frontend con el del backend habría sugerido un acoplamiento que no existe. Además, la convención de Next.js App Router que se tomó como referencia (`page.tsx`, `layout.tsx`) se adapta a React Router, que es el enrutador realmente elegido.
- **Impacto:**
  - Trazabilidad directa y defendible en la defensa PUDS: `src/apps/dashboard/<módulo>/` replica los 5 paquetes del backend, de modo que la cadena **CU → paquete → pantalla** es legible de un vistazo. `auth/` es la única excepción (transversal, su lógica vive en `usuarios_seguridad` pero su vida es independiente del dashboard).
  - `src/contexts/` se divide en `AuthContext.ts` (contexto + hook `useAuth`) y `AuthProvider.tsx` (componente provider), porque un archivo que exporta componente y hook a la vez viola `react-refresh/only-export-components` y rompe el Fast Refresh.
  - Se fija la **Regla de Oro del frontend**: ninguna pantalla llama a `axios` directamente; todo pasa por `src/services/` con contratos tipados en `src/types/`.
  - Se documenta en `docs/ai/ARCHITECTURE.md` (sección 3) y en el subagente `.opencode/agents/frontend.md`.

---

## 📅 2026-09-27 — Corrección del tipo `any` y del lint en el flujo de Login
- **Decisión:** En `LoginPage.tsx` se reemplaza `catch (err: any)` por un estrechamiento de tipo con `isAxiosError<{ error?: string; detail?: string }>(err)` de `axios`.
- **Motivo:** `@typescript-eslint/no-explicit-any` estaba violando la regla de TypeScript estricto del proyecto. Además, `any` desactiva por completo la verificación de tipos justo en la rama que maneja errores del servidor, que es la más propensa a desincronizarse con el contrato de la API.
- **Impacto:** Si el backend cambia la forma del error de autenticación, el compilador ahora lo señala. `npm run lint` y `npm run build` quedan en verde.

---

## 📅 2026-09-27 — Tailwind CSS v4 con plugin de Vite (sin PostCSS)
- **Decisión:** Mantener Tailwind CSS v4 instalado como plugin de Vite (`@tailwindcss/vite`), sin `tailwind.config.js` ni cadena PostCSS/Autoprefixer.
- **Motivo:** En Tailwind v4 la configuración nativa es CSS-first: los tokens se declaran con `@theme` dentro de `src/index.css` y el motor de compilación se conecta como plugin del bundler. Montar PostCSS encima sería configuración heredada de v3 y una fuente de conflictos.
- **Impacto:** `docs/ai/TECH_STACK.md` decía "Tailwind CSS + PostCSS + Autoprefixer", lo cual era incorrecto para este proyecto; fue corregido y se advierte explícitamente en el documento y en el subagente de frontend para que nadie intente reintroducir `tailwind.config.js`.

---

## 📅 2026-09-27 — Un único dashboard con menú filtrado por RBAC (no un dashboard por actor)
- **Decisión:** Existe **un solo** `DashboardLayout` para los cuatro actores. No habrá un dashboard por rol. La personalización se hace con un arreglo de configuración (`src/apps/dashboard/navigation.ts`) cuyos permisos se evalúan con `hasPermission()` del `AuthContext`; el Sidebar renderiza solo las ventanas que (a) el actor tiene permitidas y (b) ya están implementadas (flag `implemented`).
- **Motivo:** La pregunta era si convenía un dashboard por actor o uno común con permisos aparte. Un dashboard por actor duplicaría el shell (`Sidebar`, `Topbar`, `Outlet`) cuatro veces y obligaría a corregir el mismo bug cuatro veces, sin ganar nada: la diferencia entre actores es de **datos** (qué entradas del menú sobreviven), no de **estructura**. Además, la seguridad nunca dependió del diseño de la UI — el bloqueo real ocurre en `ProtectedRoute` y en los permisos de DRF, así que un dashboard separado no sería ni más ni más seguro. Un shell único hace además que el diagrama de navegación del sistema sea legible ante la defensa de 26 CUs.
- **Impacto:**
  - `Sidebar` y `Topbar` no reciben props por rol: leen el usuario de `useAuth()`. Agregar un quinto actor en `seed_usuarios` no requiere tocar el frontend.
  - Cada ventana se registra como ruta anidada dentro de `/dashboard` en `AppRoutes.tsx` (`<Route path="/dashboard" element={<DashboardLayout/>}><Route path="usuarios" .../></Route>`), de modo que el shell se monta una sola vez.
  - El flag `implemented` evita publicar enlaces muertos: hoy el Sidebar muestra un estado vacío honesto en vez de cinco rutas que darían 404.
  - **Única excepción prevista:** en el Ciclo 3, el Personal de Ventas probablemente necesite una ventana de venta rápida para tablet sin el cromo administrativo. Se implementará como ruta dentro del mismo dashboard (`/dashboard/ventas/registro`), no como dashboard paralelo: la diferencia es de flujo de trabajo, no de permiso.
  - Con el seed actual, el menú por actor queda así: Administrador 5/5 módulos, Propietario 4/5, Ventas 2/5, Producción 1/5.

---

## 📅 2026-09-27 — Avatar por iniciales (el modelo `usuario` no tiene campo de imagen)
- **Decisión:** `UserAvatar` genera el avatar con las iniciales de `nombre_completo` y colorea el círculo según el rol, en lugar de intentar cargar una foto.
- **Motivo:** El modelo `Usuario` y los serializadores (`CustomTokenObtainPairSerializer`, `UsuarioProfileSerializer`) no exponen ningún campo de imagen: solo `id_usuario`, `nombre_usuario`, `nombre_completo`, `email`, `activo`, `id_rol`, `rol` y `permisos`. Agregar un campo de imagen sería una decisión de modelo de datos que excede el alcance de esta tarea y requeriría migración.
- **Impacto:** El actor se identifica de inmediato tras el login sin tocar el esquema de base de datos. Si más adelante se decide storing de avatar, el cambio queda encapsulado en un solo componente.

---

## 📅 2026-09-27 — Correcciones al flujo de login y al guardia de rutas
- **Decisión:** Tres correcciones al flujo de autenticación del frontend:
  1. `ProtectedRoute.tsx` ya no mezcla mensaje de error y redirección en un mismo `return`. La rama de permiso denegado renderiza un componente `AccessDenied` con botón "Volver al panel"; la de rol denegado redirige a `/dashboard`. Cada rama tiene un `return` único.
  2. `LoginPage.tsx` muestra la política de contraseña ("Mínimo 8 caracteres, 1 mayúscula, 1 número y 1 símbolo") **solo tras un intento fallido**, mediante el estado `showPasswordPolicy`.
  3. `LoginPage.tsx` redirige a `/dashboard` si `isAuthenticated` es verdadero, para que un usuario con sesión activa no vuelva a ver el formulario.
- **Motivo:** (1) era un bug real: renderizar un `<Navigate>` dentro del mismo árbol que el mensaje de error provocaba que el mensaje fuera instantáneo antes de redirigir, y dejaba al usuario sin salida visible. (2) Mostrar la política antes de que el usuario escriba bruitaba el formulario y adelantaba una regla cuya validación real ocurre en el backend (`ComplexPasswordValidator`). (3) Sin ese guardia, un usuario ya autenticado podía caer en un ciclo perceptual de "login → dashboard → login".
- **Impacto:** El recorrido login → dashboard es ahora completo y navegable de punta a punta. `npm run lint` y `npm run build` en verde.

---

## 📅 2026-09-27 — `LucideIcon` no es usable como tipo en este proyecto
- **Decisión:** El campo `icon` de `NavModule` se tipa como `React.ElementType` en lugar del tipo `LucideIcon` exportado por la librería.
- **Motivo:** En `lucide-react@1.48` el símbolo `LucideIcon` se declara como `type` en el `.d.ts` y se reexporta en la línea `export type { ... LucideIcon ... }`, pero TypeScript lo resuelve como *namespace* en este proyecto. El resultado es `TS2709: Cannot use namespace 'LucideIcon' as a type` más un `TS6133` de valor no usado, tanto con el modificador `type` inline como con un `import type` separado.
- **Impacto:** `React.ElementType` es estructural: acepta cualquier componente que pueda usarse como etiqueta JSX (incluidos los `ForwardRefExoticComponent` de lucide) y no depende de la superficie de exports de tipos de la librería. Conviene recordar esta trampa si en el futuro se tipa algo con `LucideIcon` o `LucideProps`.

---

## 📅 2026-09-27 — La política de bloqueo por intentos vive en la BD, no en `settings.py`
- **Decisión:** Los umbrales (intentos máximos y minutos de bloqueo) se modelan en la tabla `configuracion_seguridad` mediante el patrón *singleton* (clave primaria fija en 1, reforzada con un `CHECK` constraint), y no como constantes en `settings.py`. La lógica que los consume vive en `auth_app/services/politica_bloqueo.py`.
- **Motivo:** El requisito es que el Administrador pueda *gestionar* los intentos máximos y las métricas. Eso exige que el valor sea dato editable y auditable, no configuración de despliegue: un valor en `settings.py` exigiría un redeploy para cambiarlo y no dejaría rastro de quién lo cambió. La tabla lleva `actualizado_por` (FK a `usuario`) para eso.
- **Impacto:** El panel de Django ya permite editar la fila. El futuro dashboard del Administrador (CU3) consumirá el mismo servicio, sin duplicar reglas.

---

## 📅 2026-09-27 — La lógica de negocio del login NO vive en la vista
- **Decisión:** `CustomLoginView` quedó reducida a un `throttle_classes` y nada más. Toda la lógica (evaluar bloqueo, autenticar, contar fallos, auditar, emitir tokens) está en `CustomTokenObtainPairSerializer`, que a su vez delega el cálculo al servicio `politica_bloqueo`.
- **Motivo:** Antes, la vista sobrescribía `post()` y para conocer al usuario autenticado **volvía a ejecutar la validación completa del serializador**: una segunda consulta de usuario y una segunda verificación de contraseña en cada login exitoso. Concentrarlo permite probar la política sin levantar HTTP.
- **Impacto:** Se eliminó trabajo duplicado en cada login y la vista cumple su único papel: traducir HTTP.

---

## 📅 2026-09-27 — El bloqueo se resuelve de forma perezosa, sin tarea programada
- **Decisión:** No hay cron ni celery. Cada vez que se evalúa la política se pregunta si la ventana de bloqueo ya venció, y si venció se limpia en ese momento.
- **Motivo:** Un bloqueo con vencimiento basado en *scheduler* depende de que el proceso esté corriendo. En un despliegue local de coursework es fácil que no lo esté, dejando cuentas bloqueadas para siempre. La evaluación perezosa no tiene esa dependencia.
- **Impacto:** `politica_bloqueo.evaluar_bloqueo()` es la única puerta de entrada y garantiza que nunca exista un bloqueo vencido sin limpiar.

---

## 📅 2026-09-27 — Los errores de autenticación usan `APIException`, no `ValidationError`
- **Decisión:** Los errores del flujo de login (`CredencialesInvalidasError`, `CuentaInactivaError`, `DemasiadosIntentosError`) heredan de `APIException` y devuelven todos el contrato plano `{"error": "<mensaje>"}`. El bloqueo se distingue con **HTTP 429 Too Many Requests** (antes 423 Locked; ver la entrada siguiente).
- **Motivo:** `Serializer.run_validation()` pasa cualquier `ValidationError` por `as_serializer_error()`, que convierte un detalle tipo dict en listas: `{'error': 'texto'}` se convierte en `{'error': ['texto']}`. La clave llegaba al frontend como array, rompiendo el contrato que `LoginPage` espera para pintar el mensaje. Una `APIException` viaja intacta por `exception_handler()`. Además, un código HTTP propio es lo que permite al frontend diferenciar "te equivocaste" de "estás bloqueado" (el valor concreto se corrigió después a 429; ver la entrada 5).
- **Impacto:** Contrato de API consistente y verificable. Cubierto por `auth_app/tests.py`.

---

## 📅 2026-09-27 — Mensaje de credenciales único y sin conteo de intentos
- **Decisión:** "Usuario inexistente" y "contraseña incorrecta" devuelven el mismo mensaje. En ningún caso se informa cuántos intentos le quedan al usuario.
- **Motivo:** Distinguir ambos casos permite **enumerar las cuentas del sistema**. Informar "te quedan 2 intentos" confirma que la cuenta existe y permite a un atacante calibrar un ataque de fuerza bruta. Se informa únicamente el bloqueo consumado, que ya implica que hubo 3 contraseñas reales verificadas para ese nombre.
- **Impacto:** Existe un compromiso consciente: revelar el bloqueo confirma la existencia de la cuenta, pero la alternativa (bloqueo silencioso) confunde al usuario legítimo. Documentado para la defensa.

---

## 📅 2026-09-27 — La complejidad de contraseña se valida al ESTABLECER, no al entrar
- **Decisión:** `users/password_validators.validar_contrasena()` ejecuta `AUTH_PASSWORD_VALIDATORS` y se usará en CU3 (crear usuario) y en el futuro reset de contraseña. **No** se invoca en el login.
- **Motivo:** Validar complejidad al iniciar sesión es un error de diseño: obligaría a que *toda* contraseña histórica cumpliera la política vigente, dejaría sin salida a un usuario cuya contraseña se creó con reglas más débiles y no podría corregirse sin intervención administrativa.
- **Impacto:** El login solo comprueba que la contraseña sea la correcta. Advertencia: `UserAttributeSimilarityValidator` rechazaría `Admin123!` para el usuario `admin`; el seed no lo detecta porque `create_user()` no valida, pero `createsuperuser` sí lo haría.

---

## 📅 2026-09-27 — La bitácora debe poder registrar eventos SIN usuario autenticado
- **Decisión:** `bitacora.id_usuario` pasó a `NULL` con `ON DELETE SET NULL`, y se agregó `nombre_usuario_intento` para conservar el nombre digitado en un intento fallido.
- **Motivo:** `Bitacora.registrar()` exigía `usuario.is_authenticated` y `id_usuario` era `NOT NULL`. Un intento de acceso fallido ocurre justamente cuando nadie está autenticado, así que la bitácora **descartaba en silencio** justo los eventos más importantes para detectar un ataque de fuerza bruta. Con `CASCADE` además, borrar un usuario borraba su historial.
- **Impacto:** CU26 gana trazabilidad real de accesos fallidos (`LOGIN_FALLIDO`, `ACCESO_BLOQUEADO`, `ACCESO_DENEGADO`), inclusos intentos contra usuarios inexistentes.

---

## 📅 2026-09-27 — El logout revoca el refresh token (lista negra)
- **Decisión:** Se instaló `rest_framework_simplejwt.token_blacklist`, se activó `BLACKLIST_AFTER_ROTATION: True` y `LogoutView` revoca el refresh token recibido (campo opcional). El frontend ahora envía el token en el body del logout.
- **Motivo:** `BLACKLIST_AFTER_ROTATION: False` ya estaba configurado pero `rest_framework_token_blacklist` **no estaba en `INSTALLED_APPS`**, así que el ajuste era inerte: el logout solo escribía en bitácora y el refresh token seguía siendo válido durante sus 7 días completos.
- **Impacto:** Cerrar sesión ahora invalida el token en el servidor. El token es opcional a propósito: si el navegador lo perdió, la sesión debe poder cerrarse igual.



---

## "5" 2026-09-27 -Se audita el metodo de seguridad de otro proyecto y se adopta lo mejor

**Contexto:** Se reviso `C:\Users\PERSONAL\Proyecto-SI1\backend\apps\Usuarios` (clinica de ojos) como referencia. Alli la seguridad vive en un sub-app `security/` con tres modelos: `ConfiguracionLoginSeguridad` (singleton pk=1), `BloqueoIntentoLogin` (tabla aparte claveada por el TEXTO que se digito en login) y `TokenRecuperacion` (codigo de 6 digitos en texto plano).

**Veredicto:** NO se cambia la arquitectura. Se conserva la nuestra (columnas de bloqueo en `usuario`, singleton con CHECK en base de datos, contrato de error plano, 31 pruebas). Se adoptan 4 puntos puntuales donde su codigo es mejor, y se rechazan 3 donde es peor.

### 1. `select_for_update` + `transaction.atomic()` para contar intentos
- **Decision:** `registrar_intento_fallido()` reescrito con un lock de fila.
- **Motivo:** Antes se usaba `F('intentos_fallidos') + 1` con un UPDATE atomico. Eso hacia atomico SOLO el incremento; la comparacion con el umbral (`if intentos >= max`) era una consulta aparte. Con dos contrasenas incorrectas simultaneas, ambas leian el mismo contador y ambas decidian "todavia no llego al umbral": **el bloqueo se atrasaba un intento**. `select_for_update()` pide a PostgreSQL `SELECT ... FOR UPDATE`, que vuelve indivisible el leer-modificar-escribir completo.
- **Impacto:** El bloqueo por intentos ahora es correcto ante concurrencia real.

### 2. HTTP 429 en lugar de HTTP 423 (CORRECCION DE UNA DECISION ANTERIOR)
- **Decision:** `CuentaBloqueadaError` (423 Locked) se reemplaza por `DemasiadosIntentosError` (429 Too Many Requests).
- **Motivo:** La eleccion del 423 fue un error. 423 pertenece a la familia WebDAV y describe un recurso bloqueado; lo que aqui se limita es la TASA de intentos, que es exactamente lo que significa 429. Ademas 429 es el estado que un proxy inverso o una libreria HTTP generica ya interpretan, y DRF convierte el atributo `wait` en la cabecera `Retry-After`. Con el 423, el frontend tenia que interpretar un codigo no estandar; con el 429 coincide ademas con el que ya emitia el throttling por IP, asi que ambos casos se tratan igual.
- **Impacto:** El `LoginPage` gana un contador regresivo real en vez del texto fijo "vuelve en 10 minutos".

### 3. `retry_after_seconds` como numero entero, no como cadena
- **Decision:** `DemasiadosIntentosError` arma su payload DESPUES de `super().__init__()`.
- **Motivo:** `APIException` pasa el detalle por `_get_error_details()`, que aplica `force_str()` a CADA valor. Si el dict completo pasara por ahi, `retry_after_seconds` saldria en el JSON como la cadena `"120"` y no como el numero `120`, obligando a coerciones implicitas en JavaScript y rompiendo el `setInterval` de la cuenta regresiva.
- **Impacto:** Verificado en PostgreSQL: `retry_after_seconds: 120` llega como `int`.

### 4. Redondeo hacia arriba de los segundos restantes
- **Decision:** Helper `_segundos_que_faltan()` con `math.ceil`.
- **Motivo:** Entre que se guarda `bloqueado_hasta` y se calcula el tiempo restante pasan microsegundos, asi que el real es 599.98 s. Un truncado informaria "reintenta en 599 s": el usuario reintentaria un segundo antes y recibiria otro 429 sin entender por que. Redondear hacia arriba nunca pide esperar de mas.
- **Impacto:** Se eliminaron 4 pruebas que fallaban exactamente por 599 != 600.

### 5. `AccionBitacora` como `TextChoices` (vocabulario controlado)
- **Decision:** Enum con `INICIO_SESION`, `LOGIN_FALLIDO`, `ACCESO_BLOQUEADO`, `ACCESO_DENEGADO`, `CIERRE_SESION`, `DESBLOQUEO_CUENTA`.
- **Motivo:** Las acciones se escribian como cadenas sueltas en cada vista. Una errata creaba una categoria nueva en lugar de fallar, dejando la bitacora repartida entre `LOGIN_FALLIDO` y `LOGIN_FALIDO` sin que ningun reporte las agrupara. Con el enum el error aparece al escribir el codigo.
- **Impacto:** El VALOR almacenado no cambia (sigue siendo `INICIO_SESION`), por lo que el DDL, los reportes y los datos existentes siguen validos. Los nuevos CU solo anaden miembros al enum.

### 6. La bitacora registra el `User-Agent`
- **Decision:** Nueva columna `agente_usuario` (varchar 255, truncada).
- **Motivo:** IP y User-Agent juntos separan a una persona de un bot que barre cuentas: el bot cambia de IP y trae un User-Agent generico o vacio; una tarjeta robada llega desde IPs distintas pero con el mismo navegador y version.
- **Impacto:** Migracion `bitacora.0003`.

### Lo que se RECHAZO copiar (y por que)
- **Codigo de recuperacion de 6 digitos en texto plano, sin limite de intentos:** 6 digitos son 1.000.000 de combinaciones y la tabla no tiene contador de intentos, asi que `buscar_token_recuperacion_valido()` se puede llamar un millon de veces. Ademas `token` estaba indexada en texto plano. Para CU2 se tomara su UX (codigo corto, 3 min, invalidar los anteriores) pero con hash y limite de intentos.
- **Tabla `bloqueo_intento_login` claveada por texto libre:** bloquearia tambien usuarios inexistentes (mas fuerte), pero un bot que pruebe 100.000 nombres inventados crearia 100.000 filas, y no hay purga de fallos. La version con columnas en `usuario` no crece y no necesita mantenimiento.
- **Singleton protegido solo en Python:** su `save()` fuerza `pk=1`, pero un `.update()` lo esquiva. El nuestro tiene `CHECK (id_configuracion = 1)` a nivel de base de datos.

### Nota de arquitectura
- El proyecto de la clinica tuvo que reparar su estructura con `SeparateDatabaseAndState` y renombrar el `label` de la app a `oftalmologia_security`, porque movio sus modelos de `users` a `security` DESPUES de migrar. Es la leccion de decidir la frontera de apps antes de escribir migraciones, que es justo lo que esta hecho aqui con `configuracion` como app propia desde el inicio.

---

## 6. 2026-09-27 - CU2: recuperacion de contrasena con token de enlace

**Contexto:** Dos pasos. El usuario pide un enlace; el sistema manda un correo; el usuario llega desde el enlace y elige contrasena nueva. Todo el backend queda en la sub-app `recuperacion`.

### 1. Token de 20 caracteres, no codigo de 6 digitos
- **Decision:** Alfabeto de 32 simbolos `23456789ABCDEFGHJKLMNPQRSTUVWXYZ`, longitud 20, generado con `secrets.choice()`. Se guardan 32 simbolos = 5 bits, o sea ~100 bits de entropia. Sin `0`/`1`/`I`/`O`/`L` para que no haya confusion al copiarlo a mano.
- **Motivo:** Es la version corregida de lo que se habia decidido rechazar de la clinica (ver seccion 5). Alli eran 6 digitos en texto plano, indexados, sin limite de intentos: 1.000.000 de combinaciones y la tabla se podia consultar un millon de veces. Aqui la combinacion es de ~10^30 y, sobre todo, **la base solo almacena el SHA-256**, asi que el robo de la tabla no permite reutilizar enlaces. Se conserva la buena UX del otro proyecto (vence rapido, se invalida el anterior, el enlace se puede copiar a mano).
- **Impacto:** `token_hash` es unico e indexado; la busqueda es por hash, nunca por el token en claro.

### 2. El token en claro solo existe en el correo
- **Decision:** `TokenRecuperacion` guarda `token_hash` (SHA-256 hexadecimal), `expira_en`, `usado_en`, `invalidado_en`, `intentos`, `ip_origen`, `agente_usuario` y `email_destino`.
- **Motivo:** Si alguien lee la tabla (un dump, un backup, una consulta del Administrador) no tiene nada que clicksar. El hash es suficiente porque el token es de alta entropia: no se necesita un salt por token ni un algoritmo lento, porque no hay diccionario que atacar. Con 6 digitos el hash no habria servido de nada, porque las 10^6 combinaciones serian trivialmente enumerables.
- **Impacto:** La bitacora y la tabla pueden auditar una recuperacion sin exponer el enlace.

### 3. Parametros del negocio en `ConfiguracionSeguridad`, no en `settings.py`
- **Decision:** `minutos_expiracion_token=15`, `max_intentos_token=5`, `max_solicitudes_por_hora=3`, con CHECK de rango en base de datos y editables desde el panel.
- **Motivo:** Mismo criterio que CU1. Si los limites vivieran en `settings.py` habria que reiniciar el servidor y tocar codigo para cambiar un valor que decide el Administrador. El CHECK evita que un valor fuera de rango llegue a production.
- **Impacto:** Cambiar la politica de recuperacion no requiere desplegar.

### 4. La cuota por cuenta NO devuelve 429 (correccion de una decision de esta misma sesion)
- **Decision:** Agotada `max_solicitudes_por_hora`, la respuesta sigue siendo **200 con el mismo cuerpo**, y simplemente no se envia el correo. El motivo queda solo en la bitacora.
- **Motivo:** La primera version de este CU devolvia 429 en ese caso, con el razonamiento de que "el 429 lo produce la IP, no la cuenta, asi que no confirma que la cuenta exista". **Ese razonamiento era falso.** La rama del 429 por cuota solo se alcanza cuando el usuario existe y esta activo, de modo que el 429 si confirma la existencia. Con `max_solicitudes_por_hora=3`, al cuarto intento las direcciones reales empiezan a devolver 429 y las inventadas 200: exactamente la lista de cuentas validas que el atacante buscaba. Devolver 200 en los dos casos es lo unico que cierra la puerta.
- **Impacto:** La proteccion del buzon NO se pierde: la cuota se sigue contando y no se manda el enlace. Quien se abuse de verdad se topa igual con el 429 **por IP**, que si es seguro porque depende de la IP del solicitante y no de la existencia de la cuenta. Se perdio el contador regresivo para el caso legitimo de "pedi tres veces y me equivoque de correo"; quedo registrado en `PruebasLimitesPorCuenta.test_la_respuesta_del_cuota_agotado_no_distingue_de_un_fantasma`.

### 5. El candado debe abarcar el cambio de contrasena, no solo la reserva del token
- **Decision:** `RecuperacionConfirmacionSerializer.save()` envuelve la reserva (`reclamar_token`) y la aplicacion (`aplicar_nueva_contrasena`) en un mismo `transaction.atomic()`.
- **Motivo:** `reclamar_token()` ya tenia su propio `@transaction.atomic` con `SELECT ... FOR UPDATE`, pero eso no cerraba la carrera: al retornar hacia **commit** y soltaba el lock, y recien despues se escribia la contrasena. Dos peticiones simultaneas con el mismo enlace podian ambas reservar el token y ambas cambiar la contrasena; la segunda pisaba la clave de la primera. Anidado en un `atomic` exterior, el interno se degrada a savepoint y el lock se mantiene hasta que la contrasena quedo escrita.
- **Impacto:** El enlace es de un solo uso aun bajo concurrencia real. **Pendiente:** esta correccion esta razonada pero NO verificada por una prueba automatizada; la suite corre sobre SQLite en memoria, donde cada hilo tiene su propia conexion, asi que una prueba de concurrencia real daria un falso positivo. Queda como revision manual sobre PostgreSQL.

### 6. Recuperar la contrasena levanta el bloqueo de cuenta
- **Decision:** Al restablecer, `intentos_fallidos=0`, `bloqueado_hasta=None`, `ultimo_intento_fallido=None`, y se revocan todos los refresh tokens vivos.
- **Motivo:** Sin esto, un usuario que se bloquea por olvidar la contrasena justo despues de varios intentos queda en un circulo sin salida: no entra y no puede recuperar. Y si alguien se metio con la contrasena vieja, conservar su sesion significaria que el atacante sigue adentro aunque la victima ya haya cambiado la clave.
- **Impacto:** La recuperacion es una recuperacion real y no un simple cambio de clave. Por eso usa las tablas de `token_blacklist`, ya instaladas por `BLACKLIST_AFTER_ROTATION` de CU1.

### 7. Una contrasena debil NO consume intento del token
- **Decision:** Si la contrasena falla la politica, se devuelve 400 y el token sigue con el mismo numero de intentos.
- **Motivo:** El contador de intentos frena a alguien que robo un enlace y prueba claves sin parar. Una contrasena corta no es un intento de adivinar, es un error de tecleo. Cobrarle el enlace al usuario por escribir mal le quitaria la mitad de las recuperaciones.
- **Impacto:** El limite protege contra el atacante y no castiga al usuario legitimo.

### 8. `Usuario.email` pasa a ser obligatorio y unico sin distinguir mayusculas
- **Decision:** `email` con `NOT NULL` y `UniqueConstraint(Lower('email'))`. Migracion `users.0004` con un `RunPython` previo que verifica nulos y duplicados y falla con mensaje claro si los hay.
- **Motivo:** El correo es el canal de recuperacion: sin el, el CU2 no tiene a donde enviar el enlace. Y si la unicidad fuera solo sobre `email`, `Persona@mail.com` y `persona@mail.com` serian dos cuentas distintas y la recuperacion quedaria ambigua.
- **Impacto:** El seed quedo con seis correos de prueba (`*.mail.com`, dominio reservado por RFC 2606) y el modelo quedo sin `null=True`. Los seis usuarios de desarrollo ya tienen correo.

### 9. Correccion de un bug preexistente en `validar_contrasena()`
- **Decision:** El import de `validate_password` de Django se aliasea como `validar_con_politica_de_django` y se invoca con el keyword `user=`.
- **Motivo:** La funcion se llamaba a si misma con `validate_password(contrasena, usuario=usuario)`. Como el nombre local tapaba al import, eso no era una llamada a Django sino una reentrada con un keyword inexistente: reventaba con `TypeError` en la primera invocacion. **La funcion nunca funciono desde que se escribio**, porque nadie la llamaba. CU2 es el primer caso que la invoca, y por eso el fallo salio a la luz.
- **Impacto:** Ademas de arreglar CU2, queda confirmado que la politica de contrasenas de CU3 es utilizable. Sin el alias, volver a escribir `validate_password(...)` con el nombre sin alias habria reintroducido el shadowing y la reentrada.

### 10. Correccion del contrato de error de `ContrasenaDebilError`
- **Decision:** El detalle va envuelto en `{'error': mensaje}`.
- **Motivo:** `APIException` con un `detail` de texto plano lo convierte DRF en `{"detail": ...}`, que es **otro** contrato y rompe el `setError()` del frontend igual que un `ValidationError`. El modulo de excepciones ya decia que todo error de autenticacion devuelve `{"error": "..."}`; esta excepcion se habia salido de esa norma.
- **Impacto:** Los dos endpoints de CU2 devuelven la misma forma de error que el login.

### 11. Correccion de un `AttributeError` en la auditoria de rechazos
- **Decision:** `auditar_token_rechazado()` construye la referencia al token con un condicional (`fila` es `None` cuando el token no existe).
- **Motivo:** Se usaba `fila.id_token` fuera del condicional que si protegia `fila.usuario` e `fila.intentos`. Con un token inexistente, un caso **esperado**, la peticion terminaba en 500 y el rechazo ni siquiera llegaba a bitacora.
- **Impacto:** Confirmar un token inventado responde 400 y queda auditado, en vez de reventar.

### 12. La FK a `usuario` declaraba CASCADE pero la base tenia NO ACTION
- **Decision:** Migracion `recuperacion/0002_fk_token_recuperacion_cascade`, escrita con `RunPython` y SQL explicito de PostgreSQL, que deja la constraint con `ON DELETE CASCADE` y con un nombre fijo.
- **Motivo:** El modelo y el archivo `0001_initial` decian `CASCADE`; la base tenia `NO ACTION` (`confdeltype = 'a'`). Nadie lo notaba por dos razones que conviene recordar: (1) `makemigrations` compara el modelo contra el ARCHIVO de migraciones, no contra el esquema real, asi que si el archivo se corrige despues de aplicado responde "No changes detected"; (2) una `AlterField` escrita a mano tambien se emite como **no-op**, porque para el editor de esquemas de Django `on_delete` es una preocupacion de Python y no un parametro de base de datos. Se confirmo con `sqlmigrate`, que devolvio `-- (no-op)`.
- **Impacto:** Antes, la cascada solo ocurria al borrar desde el ORM de Django, que borra los tokens relacionados en Python antes de emitir el `DELETE`. Un `DELETE` por SQL crudo fallaba con violacion de llave foranea, y un token huerfano podia reiniciar el reloj de un enlace viejo. Verificado sobre PostgreSQL: tras un `DELETE FROM usuario` por SQL crudo quedan 0 tokens huerfanos.
- **Nota operativa:** Es `RunPython` y no `RunSQL` porque el SQL es de PostgreSQL y la suite corre sobre SQLite, donde un `RunSQL` a secas reventaba con `near "DO": syntax error`. La funcion mira el `vendor` y no hace nada en otros motores. El trade-off aceptado: sobre otro motor, la cascada a nivel de base no existiria. El proyecto es PostgreSQL-only.

### 13. El rechazo por conflicto de token se audita FUERA de la transaccion
- **Decision:** El `if reservada is None: auditar(...); raise ...` quedo fuera del `with transaction.atomic()`, que ahora solo envuelve la reserva del token y el cambio de contraseña.
- **Motivo:** Un `raise` que sale de un bloque `atomic` descarta TODO lo que se escribio adentro, incluido el `INSERT` de bitácora del rechazo. Es decir: el sistema bloqueaba el ataque pero borraba la evidencia justo en el caso mas importante, que es cuando un mismo enlace se esta usando dos veces. El CU26 dejaba de registrar ese evento. Los otros tres caminos de rechazo (token inexistente, vencido, contraseña debil) si se auditaban bien porque ninguno esta dentro de una transaccion: este era el unico que perdia el rastro, y por eso el bug pasara desapercibido.
- **Como se verifico:** Dos conexiones reales de PostgreSQL confirmando el mismo token al mismo tiempo, con un retardo de 0.5s inyectado en el punto que el `atomic` protege y una barrera que fuerza la colision. Resultado con el `raise` adentro: `CONFIRMADA = 1`, `INVALIDADA = 0`. Con el `raise` afuera: `CONFIRMADA = 1`, `INVALIDADA = 1`. El candado en si ya funcionaba en ambos casos; lo que faltaba era el registro.
- **Impacto:** Sin cambio de comportamiento observable para el usuario (mismo 400, misma contraseña intacta) y con la garantia de que el intento rechazado queda en bitacora. Cubierto por `PruebasAuditoriaAnteConflicto`, que corre en cualquier motor, y por `PruebasConcurrenciaReal`, que exige PostgreSQL.

## 📅 2026-09-28 — Frontend del CU2 y reemplazo de Celery por un comando de gestión

### 14. La purga de tokens vencidos es un comando de gestion, no una cola de Celery
- **Decision:** Se creo `manage.py purgar_tokens_vencidos` (con `--dry-run` y `-v`) en vez de incorporar Celery. La automatizacion se resuelve con el **Programador de tareas de Windows**.
- **Motivo:** Indicacion explicita del usuario de no instalar Celery, y ladecision tecnicamente correcta ademas: la purga es un `UPDATE` que corre una vez por hora y del que nadie espera respuesta. Celery obligaria a agregar Redis, un worker en segundo plano, un modulo de tareas y un despliegue mas, a cambio de resolver un problema que no existe.
- **Alcance que hay que tener claro al defenderlo:** el comando es **higiene de tabla, no un control de seguridad**. La expiracion ya la aplica `buscar_por_token()` en cada confirmacion, asi que un token vencido no sirve aunque su fila siga en la base. Que el comando existe no agrega ninguna garantia de seguridad; lo que agrega es que la tabla no crezca sin limite y que el panel del Administrador no muestre tokens muertos.
- **Cuando si valdria la pena Celery:** trabajo asincrono real con reintentos y efecto observable, por ejemplo generar PDF pesados de reportes o reintentar el envio de correo cuando el SMTP falla. Eso es una decision de arquitectura para el Ciclo 4, no parte del CU2.

### 15. El token de recuperacion se borra de la barra de direcciones
- **Decision:** `ResetPasswordPage` lee el token del query string una sola vez en un `useEffect` de montaje y de inmediato reescribe la URL con `window.history.replaceState(null, '', window.location.pathname)`.
- **Motivo:** El token es una credencial. Si queda en la barra de direcciones queda en el historial del navegador (y sobrevive al cerrar la pestana) y puede filtrarse por la cabecera `Referer` a cualquier recurso externo que se cargue despues. El token en claro solo deberia existir en el correo y en la memoria de la pestana.
- **Consecuencia asumida:** recargar la pagina **no** reintenta el envio; cae en un estado "enlace incompleto" que explica que el codigo se borra a proposito y ofrece pedir uno nuevo. Es el comportamiento correcto, pero hay que dejarlo escrito porque a primera vista parece un bug.
- **Detalle de implementacion:** el efecto deja `searchParams` fuera de su array de dependencias **a proposito**, con el `eslint-disable` de `exhaustive-deps` y un comentario al lado. La limpieza de la URL cambia `searchParams`; si fuera dependencia, el efecto se volveria a disparar en bucle.

### 16. `ForgotPasswordPage` redirige si hay sesion; `ResetPasswordPage` no
- **Decision:** Solo el paso 1 manda a `/dashboard` cuando ya hay sesion activa. El paso 2 acepta trabajar con sesion abierta.
- **Motivo:** En el paso 1, si la persona ya entro no hay contrasena que olvidar, asi que la pantalla no aporta nada. En el paso 2 la persona llega por el enlace del correo y **puede tener sesion abierta en ese mismo navegador** (se recupera desde el equipo propio, por ejemplo); bloquearla seria tonto. Ademas el token del enlace ya prueba que es duena del buzon, y al confirmar el backend le revoca las sesiones, que es justo lo que se busca si alguien mas las tenia abiertas.
- **Impacto:** Evita un caso de soporte ("me mando el enlace y me echa al dashboard") y mantiene la garantia del CU2: revocar sesiones sigue pasando igual.

### 17. El checklist de contrasenas del frontend declara que NO es toda la politica
- **Decision:** `PasswordRequirements` muestra solo las cuatro reglas de `ComplexPasswordValidator` (largo, mayuscula, numero, simbolo) y, cuando se cumplen todas, dice explicitamente que el servidor ademas rechaza contrasenas muy comunes y las parecidas al nombre de usuario.
- **Motivo:** `AUTH_PASSWORD_VALIDATORS` tiene **cuatro** validadores. `CommonPasswordValidator` y `UserAttributeSimilarityValidator` dependen de datos que el navegador no tiene (una lista de ~20.000 contrasenas filtradas, y el nombre de usuario que solo el servidor conoce). Mostrar un "contraseña valida" con un check verde seria mentir: el backend seguia rechazando y la persona no entenderia por que.
- **Impacto:** El componente es util sin ser la fuente de verdad. Se verifico que el conjunto de simbolos del regex del frontend (`!@#$%^&*(),.?":{}|<>=_+\-/[]`) es identico al de `ComplexPasswordValidator` en `users/password_validators.py`. Si alguna vez se desincronizan, lo que se rompe es la experiencia, no la seguridad.

### 18. El panel de cuentas demo se condiciona a `import.meta.env.DEV`
- **Decision:** El panel de credenciales de prueba del `LoginPage` quedo dentro de `{import.meta.env.DEV && (...)}`.
- **Motivo:** Publicaba usuarios del seed y la contrasena real `Admin123!` en pantalla, en cualquier entorno. Era una puerta abierta para cualquiera que llegara a `/login` en un despliegue real.
- **Impacto:** Vite reemplaza la expresion por `false` al compilar y elimina el bloque del bundle, asi que no queda ni el texto. La prueba de que funciona es que `npm run build` deje de exponerlo; todavia no se corrio un build para comprobarlo.

### 19. Rutas: el paso 2 se declara antes del catch-all
- **Decision:** `/recuperar-password` y `/recuperar-password/nueva` van como `<Route>` publicos explicitos en `AppRoutes.tsx`, y **fuera** de `ProtectedRoute`.
- **Motivo:** Dos razones. Una: quien llega del correo puede no tener sesion, y `ProtectedRoute` lo botaria al login. Dos: `/recuperar-password/nueva` tiene que declararse antes de la ruta `*`, porque esa wildcard manda a `/dashboard`; sin la ruta explicita el enlace del correo caeria en el redirect y la recuperacion no existiria como funcionalidad.
- **Nota de organizacion:** los archivos van en `src/apps/auth/`, pero los contratos en `src/types/` y los servicios en `src/services/`, que son compartidos por toda la SPA. Los paths que se anotaron al abrir el CU2 (`src/apps/auth/types/`, `src/apps/auth/services/`, `src/apps/auth/AppRoutes.tsx`) no existen: ese proyecto tiene un solo `types/` y un solo `services/`.

---

# 📅 2026-09-28 — CU3: Gestionar usuarios (backend)

### 20. El núcleo del CU3 es registro, edición, activación e inactivación; el reset y el desbloqueo son extensión
- **Decisión:** Se implementan los cuatro endpoints del núcleo más dos extensiones: `POST /api/usuarios/<id>/restablecer-contrasena/` y `POST /api/usuarios/<id>/desbloquear/`. `GET /api/usuarios/roles/` se expone aquí y no en `roles/`.
- **Motivo:** `backend/apps/PACKAGE_CU_MAP.md` define CU3 como "registro, edición, activación e inactivación" y el actor es el Administrador. Las dos extensiones existen porque el diagrama de clases declara `cambiarContrasena()` en `Usuario` y porque CU1 dejó `politica_bloqueo.desbloquear_usuario()` escrito, con el comentario explícito de que el dashboard lo consumiría. `roles/` se expone en este ViewSet para no publicar la matriz de permisos, que es CU4, antes de que ese CU exista.
- **Impacto:** La frontera queda escrita acá para que la revisión vea con precisión qué es núcleo del caso de uso y qué es administración de cuentas. Si la docente exige alcance estricto, quitar las dos extensiones es borrar dos `@action` y sus pruebas, sin tocar el modelo ni las migraciones.

### 21. CU3 no tiene borrado: la baja es `activo = false` y `DELETE` responde 405
- **Decisión:** No se declara `destroy`. El ViewSet excluye `delete` de `http_method_names`, y `activo = false` es la baja.
- **Motivo:** El caso de uso enumera "activación e inactivación", y el diagrama define `activar()` e `inactivar()` pero no `eliminar()`. Además, `usuario` es referenciado por `bitacora`, `token_recuperacion`, `pedido`, `venta`, `compra`, `produccion` y `movimiento_economico`: un DELETE físico destruiría el historial económico de la panadería y dejaría la auditoría sin autor, que es justo lo que la bitácora existe para evitar.
- **Impacto:** Se eligió **405** y no 404 de forma deliberada. 404 diría "esta ruta no existe"; 405 dice "el borrado está en la API y está prohibido por diseño", que es la información que un cliente necesita. La exclusión se hace por `http_method_names` y no con un `perform_destroy` que aborte, porque el router sigue declarando la ruta y el 405 sale del mecanismo estándar de DRF.

### 22. Tres guardas de auto-destrucción, en el servicio y no en el frontend
- **Decisión:** `users/services/usuarios.py` bloquea tres operaciones: un Administrador no se inactiva a sí mismo, no se quita su propio rol, y no se puede dejar el sistema sin ningún Administrador activo (ni por inactivación ni por cambio de rol).
- **Motivo:** Ninguna de las tres es un descuido del usuario final: las tres son consecuencias previsibles de una operación legítima. Se bloquean en el servicio porque ocultar un botón es usabilidad, no seguridad: la API tiene que rechazar el intento aunque llegue por `curl`. La guarda "último Administrador" se evalúa **solo si la cuenta ya era un Administrador activo**, porque si no, desactivar a un vendedor en una panadería que ya se quedó sin administradores también sería rechazado.
- **Impacto:** Las guardas preguntan por el ROL DE NEGOCIO y no por `is_superuser`. Son dos conceptos distintos en este proyecto: el superusuario existe para el panel técnico de Django, y `EsAdministrador` documenta explícitamente que un Administrador de negocio NO entra a `/admin/` salvo que además tenga `is_staff`.

### 23. Cambiar rol, inactivar o restablecer la contraseña revoca las sesiones abiertas
- **Decisión:** Las tres operaciones llaman a `recuperacion.services.confirmacion.revocar_sesiones()`, el mismo servicio que ya usa CU2.
- **Motivo:** El JWT lleva `rol` y `permisos` como *claims*, de modo que un access token válido sigue afirmando el rol anterior durante toda su vida, que por defecto es de 60 minutos. Sin revocación, inactivar a un usuario o cambiarle el rol no surte efecto hasta que el token caduque. Se reutiliza el servicio en vez de escribir uno nuevo porque revocar es revocar, y dos copias garantizan que un día divergan.
- **Impacto:** `restablecer_contrasena` y `desbloquear_cuenta` levantan también el bloqueo por intentos fallidos. Restablecer la clave de una cuenta bloqueada y dejarla bloqueada sería un callejón sin salida: clave nueva que no se puede usar. Es el mismo criterio que ya aplica CU2.

### 24. El permiso de DRF se lee de la TABLA, y se instancia en `get_permissions()`
- **Decisión:** `users/permissions.py` define `TienePermiso(nombre_permiso)`, y `UsuarioViewSet` sobreescribe `get_permissions()` en vez de escribir `permission_classes = [TienePermiso('gestionar_usuarios')]`.
- **Motivo:** Dos cosas. La primera es que hasta CU1 el control de acceso no existía: todo se protegía con `IsAuthenticated`, que responde "¿hay sesión?" y no "¿qué te permite tu rol?". Un `Personal de Ventas` llegaba autenticado igual. La segunda es técnica: `APIView.get_permissions()` hace `permission()` sobre cada elemento de `permission_classes`, o sea que vuelve a instanciar lo que encuentra en la lista; poner ahí una instancia ya construida lanza `TypeError: 'TienePermiso' object is not callable`. Solo se descubre al ejecutar.
- **Impacto:** El nombre del permiso vive en una sola constante, `UsuarioViewSet.PERMISO_REQUERIDO`, y se lee del mismo `Usuario.get_permisos_nombres()` que viaja como claim `permisos` en el JWT. Que backend y frontend lean la misma fuente es lo que evita que la pantalla muestre un botón que el servidor va a rechazar.

### 25. Unicidad real del nombre de usuario: índice sobre `Lower(...)` y el `unique=True` se queda
- **Decisión:** Se agrega la restricción `usuario_username_unico_ci` sobre `Lower("nombre_usuario")` (migración `users/0005`), y el `unique=True` de la columna **se conserva**.
- **Motivo:** En PostgreSQL, `unique=True` significa "único Y DISTINTO DE MAYÚSCULAS". Con solo eso, `Admin` y `admin` coexistían como dos cuentas válidas y, como el login resuelve por coincidencia exacta (`nombre_usuario = ...`), una de las dos quedaba permanentemente inaccesible. El índice sobre `Lower()` es el que cierra eso, y es la misma regla que el serializer valida con `__iexact`.
- **Por qué no se quita el `unique=True`:** Django lo exige por contrato (`auth.E003`) para el campo `USERNAME_FIELD` de un modelo de usuario. Quitarlo funciona a nivel de tabla pero rompe el sistema de autenticación, y silenciar la verificación con `SILENCED_SYSTEM_CHECKS` sería tapar un problema real en vez de resolverlo. El índice de columna queda como el índice de búsqueda del login; el de `Lower()` es el que decide si dos cuentas pueden llamarse igual.
- **Impacto:** La migración lleva un `RunPython` **antes** del `AddConstraint` que busca duplicados por mayúsculas y aborta con un mensaje que nombra las cuentas involucradas. `AddConstraint` sobre datos duplicados fallaría con el error crudo de PostgreSQL, que no dice qué filas son las culpables. No se corrigen los datos automáticamente: renombrar cuentas es una decisión de negocio, no una tarea que un script deba tomar solo.

### 26. DRF entrega la INSTANCIA del relacionado, no su clave primaria
- **Decisión:** `users/services/usuarios.py` normaliza con `_pk_de_rol()`, que acepta `Rol`, entero o `None`.
- **Motivo:** Para un `ForeignKey`, DRF mete en `validated_data` el objeto relacionado, no el id. Por eso `Usuario(id_rol_id=<Rol: Personal de Ventas>)` fallaba con `TypeError: int() argument must be ... not 'Rol'`. El mismo descuido hacía que `editar_usuario` comparara un `Rol` contra un entero en la guarda "no dejes el sistema sin Administradores", con lo que la guarda se disparaba en cada edición de una cuenta que sí tenía rol. Ninguno de los dos se ve leyendo el código.
- **Impacto:** `editar_usuario` asigna por `id_rol_id` y no por `id_rol` para forzar que Django descarte el objeto cacheado; si asignara la instancia, `usuario.rol_nombre` seguiría devolviendo el nombre del rol ANTERIOR y la bitácora escribiría el valor viejo.

### 27. Paginación y filtro de estado por parámetro de URL, sin `django-filter`
- **Decisión:** Se activa `PageNumberPagination` con `PAGE_SIZE = 10` de forma GLOBAL, y los filtros `activo` e `id_rol` se resuelven a mano en `get_queryset()`. La búsqueda y el orden usan `SearchFilter` y `OrderingFilter` de DRF.
- **Motivo:** El default de DRF es `PaginationDisabled`: `GET /api/usuarios/` devolvería todas las cuentas en un solo JSON. Hoy son seis y no se nota; con doscientos la pantalla se vuelve lenta y el navegador recibe algo que no sabe renderizar. Se declara global y no en la vista para que cualquier listado futuro herede la protección. `django-filter` no está en `requirements.txt` y agregar una dependencia para dos filtros no se justifica.
- **Nota:** `SearchFilter` se declara en el ViewSet y no en `DEFAULT_FILTER_BACKENDS` porque los `filter_backends` alcanzan a cualquier `GenericAPIView` con `get_queryset`, y `TokenObtainPairView` de CU1/CU2 lo es. Un ajuste global haría depender el login de la configuración de la API de usuarios.
- **Limitación conocida:** el buscador usa `icontains`, que en PostgreSQL **no ignora los acentos**: buscar `Maria` no encuentra `María`. No es un bug del filtro, y la prueba lo documenta a propósito.

### 28. Deriva entre el DDL y el modelo en `rol_permiso`: se documenta, no se corrige en CU3
- **Decisión:** No se toca ni `roles/migrations/0001_initial.py` ni el DDL. La divergencia queda escrita en el DDL con un comentario explícito.
- **Motivo:** El modelo Django `RolPermiso` declara la tabla con clave primaria IMPLÍCITA (`id`), por ser el default de un modelo con dos `ForeignKey` y ningún `id` declarado. El DDL usa clave primaria COMPUESTA `PRIMARY KEY (id_rol, id_permiso)`. La base que corre no sufre el problema, porque el índice único que creó la migración cubre la misma regla, pero DDL y código no dicen lo mismo.
- **Impacto:** La corrección pertenece a CU4, que es el caso de uso dueño de la matriz de roles y permisos. Lo único que se hace en CU3 es dejar la deriva escrita, que es la forma de que no vuelva a aparecer como si fuera un error nuevo.

---

# 📅 2026-09-28 — CU3: Gestionar usuarios (frontend)

### 29. Arquitectura de componentes, accesibilidad WCAG y ciclo de vida de modales
- **Decisión:** 
  1. La UI del CU3 se organiza en `src/apps/dashboard/usuarios/` con subcomponentes locales en `components/`. El diálogo base `Modal.tsx` se coloca en `src/apps/dashboard/components/` por ser compartido exclusivamente por el dashboard, reservando `src/components/` para futuros componentes globales de toda la SPA.
  2. Los tres modales (`ModalUsuario`, `ModalEstado`, `ModalRestablecerContrasena`) se inicializan con lazy state (`useState(() => ...)`) y son montados con `key` dependiente del id del usuario en vez de resetear el estado con `useEffect`.
  3. Tras una edición exitosa, la tabla vuelve a pedir la página al servidor con `trasEdicion()` en lugar de mutar la fila en el cliente, respetando el ordenamiento alfabético y el filtrado por `icontains` de PostgreSQL.
  4. Los estilos de campos se modularizan en `estilosFormulario.ts` y los predicados de contraseñas en `politicaContrasena.ts` para cumplir estrictamente con el Fast Refresh de Vite (`react-refresh/only-export-components`).
  5. Se implementa accesibilidad WCAG 2.2 AA integral: foco inicial en el primer control, trampa de foco (Tab / Shift+Tab) dentro del diálogo, restauración de foco al elemento disparador al cerrar, cierre con tecla Escape, bloqueo del scroll del body, `role="dialog"`, `aria-modal="true"`, `aria-labelledby` con `useId()` de React 19, resumen de errores enfocado por teclado tras fallos de red y mensajes de error inline vinculados por `aria-describedby`.
- **Motivo:** Evitar parpadeos visuales al abrir formularios, eliminar las advertencias y errores de ESLint (`react-hooks/set-state-in-effect`), garantizar soporte total para tecnologías de asistencia y teclado sin ratón, y evitar que el cliente contradiga el ordenamiento o las reglas de coincidencia del backend.
- **Impacto:** Código robusto, modular y 100% libre de advertencias y errores tanto en `tsc -b` como en `eslint`, listo para producción.

---

# 📅 2026-09-28 — CU4: Asignar roles y permisos (backend)

### 30. Nombre del permiso `asignar_permisos` y categorización `permiso.modulo`
- **Decisión:** Se reserva y aplica el permiso `asignar_permisos` (ID 12) para el CU4, tal como se mapeó en `PACKAGE_CU_MAP.md` y en las reservas de ruta. Se incorpora el campo `modulo` (`ModuloPermiso.TextChoices`) en el modelo `Permiso` para clasificar los permisos según los 5 paquetes del sistema.
- **Motivo:** Facilita la presentación agrupada de la matriz de checkboxes en el cliente y garantiza trazabilidad con la arquitectura modular.
- **Impacto:** Migración `permisos/0002_permiso_modulo_alter_permiso_nombre_and_more.py` aplicada limpiamente y DDL documentado con `-- MODIFICADA (CU4)`.

### 31. Resolución definitiva de la deriva de `rol_permiso` en el DDL
- **Decisión:** Se resuelve la discrepancia detectada en CU3 alineando el DDL a la convención estándar de Django: clave primaria subrogada `id` y restricción `UNIQUE ("id_rol", "id_permiso")`.
- **Motivo:** La migración con clave primaria compuesta experimental resultaba en un *no-op* en Django y rompía la reversibilidad de migraciones. La restricción `UniqueConstraint(fields=['rol', 'permiso'], name='rol_permiso_unico')` ofrece exactamente la misma garantía matemática de unicidad física en PostgreSQL.
- **Impacto:** Código ORM estándar, compatible con `ManyToManyField(through=...)`, sin fragilidad de `RunPython` ni hacks en el esquema.

### 32. Inmutabilidad de roles base y guardas anti-autobloqueo en la capa de servicios
- **Decisión:** La lógica reside en `roles/services/matriz.py` bajo `@transaction.atomic`. Se imponen 4 guardas: (1) Sin DELETE (405), (2) Roles base (`Administrador`, `Propietario`, `Personal de Ventas`, `Personal de Producción`) no pueden cambiar de nombre, (3) El rol `Administrador` nunca puede perder `asignar_permisos`, y (4) Ningún usuario autenticado puede quitar `asignar_permisos` de su propio rol activo.
- **Motivo:** Prevenir escaladas de privilegios y callejones sin salida donde el sistema se queda sin ningún usuario o rol capaz de administrar permisos.
- **Impacto:** Operaciones seguras tanto si se invocan vía API como desde scripts o consola.

### 33. Endpoints REST granulares y coherentes con UML
- **Decisión:** Se implementa `RolViewSet` con soporte de matriz masiva (`PUT /api/roles/<id>/permisos/`) y métodos puntuales correspondientes a `Rol.asignarPermiso()` (`POST /api/roles/<id>/permisos/asignar/`) y `Rol.quitarPermiso()` (`POST /api/roles/<id>/permisos/quitar/`).
- **Motivo:** Cumplir al 100% con la especificación de métodos del diagrama de clases UML `database_panaderia_con_funciones.puml`.
- **Impacto:** Cada mutación registra su diff exacto en `Bitacora` (`ALTA_ROL`, `EDICION_ROL`, `ASIGNAR_PERMISO_ROL`, `REVOCAR_PERMISO_ROL`, `ACTUALIZACION_MATRIZ_PERMISOS`).

---

# 📅 2026-09-28 — CU4: Asignar roles y permisos (frontend)

### 34. Navegación en pestañas bajo `/dashboard/usuarios`, sincronización con URL y matriz de permisos por módulos
- **Decisión:** 
  1. CU4 no crea una nueva ruta de primer nivel en el menú principal; se integra como pestaña "Roles y permisos" dentro del módulo unificado de *Usuarios y Seguridad* (`/dashboard/usuarios`).
  2. `ProtectedRoute` y `AppRoutes.tsx` se ampliaron para aceptar `requiredPermission?: string | string[]` con semántica *any-of*, permitiendo el acceso tanto con `gestionar_usuarios` como con `asignar_permisos`.
  3. La pestaña activa se sincroniza bidireccionalmente con la URL mediante `useSearchParams` (`?tab=roles` vs `?tab=usuarios`), preservando el estado en recargas, historial y navegación directa.
  4. La edición de la matriz (`MatrizPermisosModal`) se diseñó sin scrollbars anidadas dobles, agrupando los 12 permisos por los 5 módulos funcionales del sistema con acciones por lote ("Marcar/Desmarcar módulo"), buscador de permisos reactivo y contador de cambios pendientes.
  5. La guarda contra auto-bloqueo del Administrador se refleja visualmente en el cliente: el checkbox de `asignar_permisos` permanece bloqueado, deshabilitado y acompañado de un callout explicativo de seguridad.
  6. Tarjetas de roles (`TarjetaRol`) con identidad visual del personal de panadería (Administrador, Cajero, Panadero, Pastelero), barras de cobertura con `role="progressbar"` y KPI summary bar en `RolesTab`.
- **Motivo:** Evitar fragmentar el menú lateral con ventanas redundantes para el mismo dominio de seguridad, permitir deep linking directo a roles, y garantizar accesibilidad WCAG 2.2 AA sin romper *Fast Refresh* de Vite.
- **Impacto:** Experiencia de usuario coherente y fluida; verificación de tipos y bundling con `tsc -b && vite build` completada con 0 errores y 0 warnings.

---

# 📅 2026-10-09 — Dockerización del Entorno y Compatibilidad de Dependencias

### 35. Compatibilidad de `psycopg2-binary` con Python 3.14 en Windows
- **Decisión:** Modificar la restricción en `backend/requirements.txt` de `psycopg2-binary==2.9.9` a `psycopg2-binary>=2.9.9`.
- **Motivo:** La versión 2.9.9 carece de ruedas precompiladas (`.whl`) para Python 3.14 en Windows, lo que provocaba un fallo de compilación exigiendo *Microsoft Visual C++ 14.0 Build Tools*. Versiones recientes (>=2.9.10 / 2.9.13) incluyen binarios oficiales precompilados.
- **Impacto:** El backend se instala limpiamente sin exigir herramientas de compilación C++ en la máquina anfitriona y mantiene retrocompatibilidad total con Python 3.12+.

### 36. Dockerización Completa con Docker Compose (Backend, Frontend, DB y Mailpit)
- **Decisión:** Implementar orquestación mediante `docker-compose.yml`, `backend/Dockerfile` (Python 3.12-slim) y `frontend/Dockerfile` (Node 20-alpine), unificando los 4 servicios en una sola red virtual interna y volúmenes de persistencia.
- **Motivo:** Reducir la fricción operativa de tener que abrir y coordinar 3 a 4 terminales locales para levantar el sistema (Mailpit, Django, Vite y PostgreSQL local), eliminando inconsistencias entre sistemas operativos de los miembros del equipo y preparando el proyecto para despliegue en la nube (Railway, Render, Google Cloud Run o Vercel).
- **Impacto:** Un único comando (`docker compose up`) levanta todo el ecosistema con recarga en caliente (hot reload) tanto en Python como en Vite.

### 37. Hot Module Replacement (HMR) de Vite con Polling en Docker
- **Decisión:** Configurar `server: { host: '0.0.0.0', port: 5173, watch: { usePolling: true } }` en `frontend/vite.config.ts`.
- **Motivo:** Las notificaciones del sistema de archivos entre Windows (NTFS) y el subsistema de contenedores Linux (WSL2/Docker) a menudo no propagan eventos de *inotify*, lo que impediría la actualización automática en el navegador al modificar código en VS Code.
- **Impacto:** Los cambios en archivos `.tsx`, `.ts` y `.css` se reflejan instantáneamente en el navegador sin necesidad de reiniciar el contenedor ni recargar manualmente la página.

---

# 📅 2026-10-10 — Rediseño Institucional de Autenticación y Frontend de Producción

### 38. Tipografía Sugo, Layout Split-Screen y Tarjeta Centrada en Flujos de Autenticación
- **Decisión:**
  1. Integrar localmente la tipografía corporativa `Sugo Regular` (`sugo.regular.otf`) en `src/assets/fonts/` y registrarla mediante `@font-face` en `src/index.css` (`.font-sugo`), asegurando carga inmediata offline y consistencia visual con la identidad de marca de Panadería Santiago.
  2. Implementar layout *Split-Screen* (50% fotografía editorial `photo-bakery.jpg` con gradiente oscuro y 50% formulario) en `LoginPage` y `ForgotPasswordPage`, con adaptación responsive que oculta la foto en pantallas móviles (`hidden lg:flex`) y contención vertical para evitar barras de desplazamiento en resolución estándar (100% viewport fit).
  3. Reemplazar emojis de demostración por iconos vectoriales Lucide temáticos (`ShieldCheck`, `Briefcase`, `ShoppingBag`, `ChefHat`) y estandarizar el logo circular oficial en formato SVG sin ornamentos externos.
  4. Preservar intencionalmente el formato de tarjeta centrada en `ResetPasswordPage` (sin foto de panadería), focalizando la atención del usuario en los requisitos de complejidad de su nueva contraseña (`PasswordRequirements`) y el borrado seguro del token de la URL mediante `replaceState`.
- **Motivo:** Alinear el portal con el prototipo visual de Figma aprobado, transmitir seriedad institucional y mejorar la ergonomía y accesibilidad para todos los perfiles de usuario.
- **Impacto:** Experiencia visual de alta gama, libre de desbordamientos visuales, con compilación y tipos 100% en verde.

### 39. Arquitectura Frontend de Producción Diaria (CU10/CU11) con Fallback Mock
- **Decisión:** Desarrollar los contratos tipados de producción (`LoteProduccion`, `DetalleProduccionInsumo`, etc.) y conectar `produccionService.ts` con una arquitectura híbrida de fallback automático a datos simulados realistas ante respuestas 404 o indisponibilidad del servidor.
- **Motivo:** Desacoplar el avance de la interfaz de usuario respecto al desarrollo de los modelos ORM en el backend, permitiendo validar flujos de interacción, cálculo de balance de materia prima y tablas de lotes de forma inmediata.
- **Impacto:** Pestaña "Producción diaria" lista y operativa en `ProductosPage.tsx?tab=produccion` para pruebas de usuario y revisión de diseño antes del backend definitivo.

