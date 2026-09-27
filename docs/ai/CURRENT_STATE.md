# Estado Actual del Proyecto (CURRENT STATE)

## 📌 Proyecto: Sistema de Información Web — Panadería Santiago (SI-1)
**Fecha de última actualización:** 2026-09-27  
**Fase PUDS actual:** Fase de Construcción — **Ciclo 1**

---

## 📊 1. Resumen Ejecutivo de Avance

- **Arquitectura Base:** 100% Definida (Backend modular en 5 Django apps, Frontend React/TypeScript en Vite organizado por pantallas, Base de datos PostgreSQL normalizada).
- **Documentación de Ingeniería:** 100% Actualizada (Perfil, DDL de base de datos, memoria de IA en `docs/ai/`, bitácora de sesiones).
- **Backend:** Estructura de carpetas creada para los 5 paquetes en `backend/apps/`. Preparado para la implementación de modelos ORM y endpoints del Ciclo 1.
- **Frontend:** Estructura base inicializada con Vite + React 19 + TypeScript + Tailwind CSS v4, **organizada por ventanas/pantallas** en `frontend/src/apps/`. Contiene la pantalla de Login (CU1) y el **shell del dashboard** (`DashboardLayout` + `Sidebar` + `Topbar` + `DashboardHome`) con menú único filtrado por permisos RBAC. Cliente Axios con interceptores JWT, `AuthContext`/`AuthProvider` y rutas protegidas. `npm run lint` y `npm run build` en verde.
- **Base de Datos:** Script DDL completo documentado en [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql).

---

## 🚦 2. Semáforo de Casos de Uso (26 Casos de Uso)

### 🟢 = Completado | 🟡 = En progreso / Siguiente a implementar | ⚪ = Planificado

### 📌 Ciclo 1 (7 Casos de Uso) — *Iteración Actual*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado | Detalle |
|---|---|---|:---:|---|
| **CU1** | Iniciar sesión | `apps.usuarios_seguridad` | 🟢 | **Completo end-to-end.** Backend: endpoints `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/me/`, `/api/auth/logout/` con JWT y claims de roles/permisos. Frontend: `src/apps/auth/LoginPage.tsx`, `AuthProvider` con persistencia en `localStorage`, refresco automático de token ante `401`, `ProtectedRoute` como guardia de sesión, redirección a `/dashboard` si ya hay sesión, y `DashboardLayout`/`DashboardHome` como destino post-login. |
| **CU2** | Recuperar contraseña | `apps.usuarios_seguridad` | 🟡 | Backend en preparación de servicio de tokens temporales. Frontend pendiente: crear `src/apps/auth/ForgotPasswordPage.tsx` y enlazarlo (el "¿Olvidaste tu contraseña?" del login sigue siendo un `<span>` sin `onClick`). |
| **CU3** | Gestionar usuarios | `apps.usuarios_seguridad` | 🟡 | Sub-app `users` lista con modelo `Usuario` y comando de seed data. |
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
1. **Crear `src/apps/dashboard/usuarios/`** (CU3, CU4, CU26): es el primer módulo real y el que desbloquea el Ciclo 1. Al crearlo, poner `implemented: true` en su entrada de `navigation.ts` y registrar la ruta anidada en `AppRoutes.tsx`.
2. **Extraer el panel de cuentas demo** de `LoginPage.tsx` a un componente reutilizable (ej. `src/apps/auth/components/DemoCredentialsPanel.tsx`) y condicionarlo con `import.meta.env.DEV`, ya que hoy expone contraseñas del seed en cualquier entorno.
3. **Convertir "¿Olvidaste tu contraseña?" en enlace real** a `src/apps/auth/ForgotPasswordPage.tsx` (CU2).
4. **Alinear el seed con la matriz de actores**: `seed_usuarios` da `generar_reportes` al Personal de Ventas, pero `PACKAGE_CU_MAP.md` asigna CU21–CU25 solo al Propietario. Decidir antes del Ciclo 4.
5. **Crear `src/components/`** con los primeros átomos compartidos: `Button`, `Input`, `Modal`, `DataTable`, `Badge`. `UserAvatar` ya existe en `apps/dashboard/components/` y conviene promoverlo cuando lo use una segunda pantalla.
6. **Implementar modelos base** de `productos_inventario` (CU5) y `compras` (CU6) en el backend.

### ⚠️ Deuda técnica conocida

- `LoginPage.tsx` — credenciales de prueba visibles en producción (ver paso 2).
- `LoginPage.tsx` — "¿Olvidaste tu contraseña?" es un `<span>` sin `onClick`, no navega a ninguna parte (ver paso 3).
- `seed_usuarios` vs `PACKAGE_CU_MAP.md` — desacuerdo sobre quién tiene `generar_reportes` (ver paso 4).
- `AuthProvider.hasPermission` — atajo de cliente `if (user.rol === 'Administrador') return true;`. Es válido como UX, pero el backend sigue siendo la autoridad; conviene recordarlo al implementar los permisos de DRF.
- Sin suite de tests automatizados en el frontend (el backend tiene `tests.py` planificado en el Paso 9 del flujo de implementación).

### ✅ Deuda técnica resuelta

- ~~`ProtectedRoute.tsx` — doble retorno en conflicto~~ → Corregido: cada rama tiene un `return` único; la de permiso denegado renderiza `AccessDenied` con botón "Volver al panel" en vez de redirigir a ciegas.
- ~~Texto de política de contraseña visible desde el primer render~~ → Corregido: solo aparece tras un intento fallido (estado `showPasswordPolicy`).
- ~~Usuario autenticado podía volver a ver `/login`~~ → Corregido: `LoginPage` redirige a `/dashboard` si `isAuthenticated`.
