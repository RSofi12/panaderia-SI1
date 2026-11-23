# Caso de Uso — CU28 Consultar Dashboard

| Elemento | Detalle |
|---|---|
| **Nombre de CU** | **CU28. Consultar Dashboard** |
| **Propósito** | Proveer una visión integral, en tiempo real y ejecutiva del desempeño financiero, comercial, operativo y de seguridad de la Panadería Santiago mediante indicadores clave (KPIs), métricas agregadas y gráficos interactivos. |
| **Resumen** | El Propietario (o Administrador según su rol) ingresa al módulo de Dashboard / Panel de Control. El sistema consulta y consolida métricas clave en tiempo real (ingresos por ventas, egresos por compras y gastos, resultado económico neto, margen operativo, alertas de bajo stock, rotación de productos más vendidos, y métricas operativas/seguridad). El usuario puede filtrar la información por rango temporal (Hoy, Esta semana, Este mes), alternar perspectivas y acceder directamente a los reportes detallados o acciones operativas asociadas. |
| **Actores** | Propietario (principal), Administrador (secundario) |
| **Actor iniciador** | Propietario / Administrador |
| **Precondición** | CU01. Iniciar sesión con una cuenta de usuario autenticada con rol Propietario o Administrador (permiso `generar_reportes` o `consultar_bitacora`). Deben existir registros en el sistema (ventas, compras, insumos, productos o bitácora). |
| **Flujo principal** | 1. El Propietario accede a la opción "Dashboard" desde el menú lateral (`/dashboard/kpis`).<br>2. El sistema verifica los permisos del usuario activo y determina la perspectiva predeterminada (Visión Ejecutiva de Negocio para Propietario; Visión de Seguridad y Auditoría para Administrador).<br>3. El sistema carga de forma asíncrona y sintetiza las métricas del periodo temporal seleccionado (Hoy, Esta semana, Este mes): ingresos por ventas, egresos operativos acumulados (compras CU07 + gastos e inversiones CU20), balance neto, stock valorizado y alertas críticas.<br>4. El sistema presenta las tarjetas de KPIs principales (Ingresos, Egresos, Resultado Neto, Margen) con sus respectivas tendencias visuales y deltas porcentuales.<br>5. El sistema renderiza los gráficos analíticos interactivos:<br>&nbsp;&nbsp;&nbsp;&nbsp;a) Gráfico circular (Donut) de distribución de flujos financieros (Ventas Cobradas vs Compras de Insumos vs Gastos Operativos).<br>&nbsp;&nbsp;&nbsp;&nbsp;b) Gráfico de columnas verticales con el Top 5 de productos con mayor rotación/demanda.<br>6. El sistema exhibe los indicadores tácticos operacionales:<br>&nbsp;&nbsp;&nbsp;&nbsp;a) Ticket promedio de compra en Bs.<br>&nbsp;&nbsp;&nbsp;&nbsp;b) Proporción de métodos de pago (% digital con QR/Stripe vs efectivo).<br>&nbsp;&nbsp;&nbsp;&nbsp;c) Conteo de pedidos pendientes de entrega.<br>&nbsp;&nbsp;&nbsp;&nbsp;d) Valorización total del stock de pan listo para la venta.<br>7. El usuario puede alternar el filtro temporal (Hoy, Esta semana, Este mes) o alternar perspectivas; el sistema recalcula y actualiza la visualización de inmediato sin recarga de página (`useTransition`).<br>8. El usuario puede pulsar en cualquier tarjeta de alerta o reporte rápido para navegar directamente al módulo correspondiente (CU07, CU21, CU22, CU23, CU24, CU25). |
| **Postcondición** | Se visualizan los indicadores consolidados actualizados en pantalla para la toma de decisiones estratégicas, sin alterar el estado de la base de datos (operación de solo lectura). |
| **Excepción** | • **Sin sesión o sin permisos requeridos (`generar_reportes` / `consultar_bitacora`):** Acceso denegado; el sistema redirige al login o restringe la vista.<br>• **Indisponibilidad de servicios o fallo de red:** El sistema muestra una alerta de advertencia y opción de reintento manteniendo la interfaz accesible con valores neutros y datos en fallback seguro.<br>• **Período sin movimientos registrados:** El sistema visualiza las métricas en cero sin romper los gráficos ni generar desbordamientos visuales. |

---

## Trazabilidad Técnica e Implementación

### 1. Arquitectura en Capas
- **Frontend:**
  - Componente de página: `frontend/src/apps/dashboard/kpis/KpiDashboardPage.tsx`
  - Vista Propietario: `frontend/src/apps/dashboard/kpis/OwnerDashboardView.tsx`
  - Vista Administrador: `frontend/src/apps/dashboard/kpis/AdminDashboardView.tsx`
  - Tarjeta modular: `frontend/src/apps/dashboard/kpis/components/KpiCard.tsx`
  - Gráficos interactivos: `DonutChart.tsx` y `ColumnBarChart.tsx`
  - Servicio agregador: `frontend/src/services/kpiDashboardService.ts`
  - Tipos: `frontend/src/types/kpiDashboard.ts`
  - Ruta protegida: `/dashboard/kpis` en `AppRoutes.tsx`
- **Backend:**
  - Consumo y agregación de servicios de `apps.comercializacion` (`/api/reportes/ventas/`), `apps.compras` (`/api/compras/`, `/api/gastos/`), `apps.productos_inventario` (`/api/inventario/materias-primas/`, `/api/productos/`), `apps.usuarios_seguridad` (`/api/usuarios/`, `/api/bitacora/`).
- **Base de datos:** Operación 100% de solo lectura y agregación, sin cambios de esquema DDL.
