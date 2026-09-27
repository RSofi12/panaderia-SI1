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

