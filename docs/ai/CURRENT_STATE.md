# Estado Actual del Proyecto (CURRENT STATE)

## 📌 Proyecto: Sistema de Información Web — Panadería Santiago (SI-1)
**Fecha de última actualización:** 2026-09-26  
**Fase PUDS actual:** Fase de Construcción — **Ciclo 1**

---

## 📊 1. Resumen Ejecutivo de Avance

- **Arquitectura Base:** 100% Definida (Backend modular en 5 Django apps, Frontend React/TypeScript en Vite, Base de datos PostgreSQL normalizada).
- **Documentación de Ingeniería:** 100% Actualizada (Perfil, DDL de base de datos, memoria de IA en `docs/ai/`, bitácora de sesiones).
- **Backend:** Estructura de carpetas creada para los 5 paquetes en `backend/apps/`. Preparado para la implementación de modelos ORM y endpoints del Ciclo 1.
- **Frontend:** Estructura base inicializada con Vite + React + TypeScript + Tailwind CSS.
- **Base de Datos:** Script DDL completo documentado en [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql).

---

## 🚦 2. Semáforo de Casos de Uso (26 Casos de Uso)

### 🟢 = Completado | 🟡 = En progreso / Siguiente a implementar | ⚪ = Planificado

### 📌 Ciclo 1 (7 Casos de Uso) — *Iteración Actual*
| CU | Nombre del Caso de Uso | Paquete Backend | Estado | Detalle |
|---|---|---|:---:|---|
| **CU1** | Iniciar sesión | `apps.usuarios_seguridad` | 🟡 | En preparación de modelos y SimpleJWT |
| **CU2** | Recuperar contraseña | `apps.usuarios_seguridad` | 🟡 | En preparación de servicio de tokens |
| **CU3** | Gestionar usuarios | `apps.usuarios_seguridad` | 🟡 | En preparación de CRUD y hash de contraseñas |
| **CU4** | Asignar roles y permisos | `apps.usuarios_seguridad` | 🟡 | En preparación de tablas RBAC |
| **CU26**| Gestionar bitácora (versión simple) | `apps.usuarios_seguridad` | 🟡 | En preparación de modelo de auditoría |
| **CU5** | Gestionar productos (catálogo base) | `apps.productos_inventario`| 🟡 | En preparación de modelo Producto y Categoría |
| **CU6** | Gestionar proveedores (catálogo base)| `apps.compras` | 🟡 | En preparación de modelo Proveedor |

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
1. Definir modelos ORM en `backend/apps/usuarios_seguridad/models.py` (`Rol`, `Permiso`, `RolPermiso`, `Usuario`, `Bitacora`).
2. Configurar endpoints de autenticación JWT (`/api/auth/login/`, `/api/auth/refresh/`).
3. Crear serializers y ViewSets con permisos RBAC en `usuarios_seguridad`.
4. Implementar modelos base de `productos_inventario` (CU5) y `compras` (CU6).
5. Crear pantalla de Login y Dashboard inicial en el frontend React.
