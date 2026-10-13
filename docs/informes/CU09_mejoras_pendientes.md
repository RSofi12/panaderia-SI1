# Informe de Revisión y Mejoras Pendientes — CU09: Consultar Alertas de Bajo Stock

- **Fecha de Evaluación:** 2026-10-13
- **Paquete / Sub-app:** `backend/apps/productos_inventario/materia_prima/`
- **Frontend:** `frontend/src/apps/dashboard/inventario/AlertasBajoStockPage.tsx`
- **Referencia de Arquitectura:** `backend/apps/PACKAGE_CU_MAP.md` (Ciclo 2)

---

## 1. Veredicto General

> **Estado Actual:** 🟢 **Bien implementado y funcionalmente sólido.**  
> El caso de uso respeta los patrones arquitectónicos del sistema (DRF + Vite/React), no alteró el esquema relacional, no generó deuda técnica y cuenta con una cobertura de pruebas exhaustiva (12 pruebas unitarias pasando en verde).

---

## 2. Cumplimiento de la Arquitectura del Proyecto

| Criterio | Evaluación | Detalle |
|---|:---:|---|
| **Ubicación en Paquetes** | 🟢 Cumple al 100% | Ubicado dentro de `apps.productos_inventario.materia_prima/`, cumpliendo la simetría de 4 sub-apps (2 CU por sub-app: CU8 y CU9 en `materia_prima`). |
| **Separación por Capas** | 🟢 Cumple al 100% | Lógica de consulta desacoplada en `selectors.py` (`obtener_materias_primas_bajo_stock`), serialización limpia en `serializers.py` (`AlertaBajoStockSerializer`) y control de acceso en `permissions.py` (`EsRolAutorizadoCU09`). |
| **Control de Acceso (RBAC)** | 🟢 Cumple al 100% | Aplica doble guarda: permiso `gestionar_inventario` + `EsRolAutorizadoCU09`. Autoriza a **Personal de Producción**, **Propietario** y **Administrador**, y bloquea expresamente a **Personal de Ventas** (403 Forbidden). |
| **Rendimiento de Base de Datos** | 🟢 Cumple al 100% | Consulta optimizada mediante un solo query SQL con `.annotate()` y `Coalesce`, evitando problemas N+1 y manejando insumos nuevos sin registro de inventario como stock `0.000`. |
| **Accesibilidad (a11y)** | 🟢 Cumple | La página `AlertasBajoStockPage.tsx` incluye roles semánticos (`role="status"`, `role="alert"`, `scope="col"`, `scope="row"` y `caption` con `.sr-only`). |

---

## 3. Cumplimiento Funcional del CU9

Según `backend/apps/PACKAGE_CU_MAP.md`:
> *"Identificación de las materias primas cuyo stock actual está por debajo del stock mínimo definido, para gestionar oportunamente su reposición. Actor(es): Personal de Producción, Propietario (y Administrador)."*

- ✅ **Identifica insumos críticos:** Filtra automáticamente los insumos activos cuyo stock actual es menor al stock mínimo.
- ✅ **Calcula el faltante:** Calcula `faltante = stock_minimo - stock_actual` con precisión de 3 decimales para saber exactamente cuánto pedir.
- ✅ **Excluye insumos inactivos:** No genera falsas alarmas con insumos dados de baja.
- ✅ **Respeto a los actores:** Vista protegida tanto en backend como por la ruta de frontend (`/dashboard/inventario/alertas-bajo-stock`).

---

## 4. Mejoras Propuestas para el Equipo (Backlog de Refinamiento)

A continuación se detallan las 4 mejoras identificadas para delegar e implementar en el siguiente ciclo o sprint:

### Mejora 1: Enlace directo al CU7 (Registrar Compra / Reposición) — *Flujo de negocio circular*
- **Problema actual:** La tabla muestra los faltantes, pero el usuario debe salir manualmente de la vista e ir al módulo de compras para reponer insumos.
- **Solución propuesta:**
  - En la tabla de alertas, añadir una columna de acción rápida por fila con un botón **"Comprar"** o **"Solicitar reposición"**.
  - Este botón debe navegar a `/dashboard/compras` o abrir el modal de compra precargando la materia prima y sugiriendo como cantidad la cifra del faltante.

### Mejora 2: Armonización del Criterio de Alerta (`<` vs `<=`)
- **Problema actual:**
  - En CU8 (`InventarioTab`), un insumo entra en semáforo `bajo_minimo` si `stock <= stock_minimo`.
  - En CU9 (`selectors.py`), la alerta se dispara estrictamente con `stock < stock_minimo` (si `stock == stock_minimo`, no alerta).
- **Solución propuesta:**
  - Unificar el criterio en `selectors.py` a `stock_para_alerta__lte=F('stock_minimo')`.
  - En una panadería, alcanzar exactamente el stock de seguridad ya amerita emitir una orden de compra preventiva antes de quedarse desabastecido.

### Mejora 3: Integración Visual y Ubicación del Acceso en `ProductosPage.tsx`
- **Problema actual:** El botón `<Link to="/dashboard/inventario/alertas-bajo-stock">` se ubicó de manera aislada por encima del título principal de `ProductosPage.tsx`.
- **Solución propuesta:**
  - Integrar el botón o banner de advertencia dentro de la pestaña **"Stock de materia prima" (`InventarioTab.tsx`)** al lado de la barra de acciones o los filtros.
  - Opcional: Mostrar un badge contador de alertas activas en la pestaña "Stock de materia prima" (ej. `Stock de materia prima (2)`).

### Mejora 4: Tarjetas KPI y buscador en `AlertasBajoStockPage.tsx`
- **Problema actual:** La pantalla solo renderiza una tabla básica sin métricas agregadas ni buscador.
- **Solución propuesta:**
  - Añadir 3 tarjetas KPI superiores:
    1. *Total de materias primas en alerta crítica*.
    2. *Insumos agotados (stock = 0)*.
    3. *Mayor faltante en volumen*.
  - Añadir un campo de búsqueda reactiva por nombre para localizar rápidamente un insumo específico cuando el inventario crezca.
