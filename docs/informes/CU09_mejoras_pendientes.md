# Informe de Revisión y Mejoras Pendientes — CU09: Consultar Alertas de Bajo Stock

- **Fecha de Evaluación:** 2026-10-13
- **Paquete / Sub-app:** `backend/apps/productos_inventario/materia_prima/`
- **Frontend:** `frontend/src/apps/dashboard/inventario/AlertasBajoStockPage.tsx`
- **Referencia de Arquitectura:** `backend/apps/PACKAGE_CU_MAP.md` (Ciclo 2)

---

## 1. Veredicto General

> **Estado Actual:** 🟢 **Las cuatro mejoras de refinamiento están implementadas.**
> El caso de uso mantiene DRF + React/Vite y el esquema relacional existente. Verificación integrada: 28 pruebas de CU07/CU08/CU09 aprobadas tanto en SQLite en memoria como en PostgreSQL temporal; build y lint de archivos modificados aprobados.

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
> *"Identificación de las materias primas activas cuyo stock actual está en el mínimo o por debajo del stock mínimo definido (stock_actual <= stock_minimo), para gestionar oportunamente su reposición."*

- ✅ **Identifica insumos en alerta:** Filtra automáticamente los insumos activos cuyo stock actual es menor o igual al mínimo. Alcanzar el mínimo genera alerta con faltante `0.000`; sin inventario se mantiene stock cero, incluido mínimo cero.
- ✅ **Calcula el faltante:** Calcula `faltante = stock_minimo - stock_actual` con precisión de 3 decimales para saber exactamente cuánto pedir.
- ✅ **Excluye insumos inactivos:** No genera falsas alarmas con insumos dados de baja.
- ✅ **Respeto a los actores:** Vista protegida tanto en backend como por la ruta de frontend (`/dashboard/inventario/alertas-bajo-stock`).

---

## 4. Mejoras del Equipo — Implementadas el 2026-10-13

A continuación se conservan los antecedentes de las cuatro mejoras y se documenta la solución aplicada:

### Mejora 1: Enlace directo al CU7 (Registrar Compra / Reposición) — *Flujo de negocio circular*
- **Antecedente:** La tabla mostraba faltantes sin un acceso directo al formulario de compras.
- **Solución propuesta:**
  - En la tabla de alertas, añadir una columna de acción rápida por fila con un botón **"Comprar"** o **"Solicitar reposición"**.
  - Implementado: navega a `/dashboard/compras?tab=compras&reposicion_materia_prima=<id>&reposicion_cantidad=<faltante>`. CU07 abre su modal existente, valida el insumo en el catálogo activo y precarga la cantidad editable y el último precio conocido. El nombre y la unidad provienen del catálogo por ID.
  - La acción y la apertura del modal requieren `registrar_compras`, igual que el permiso real del backend CU07. Consultar alertas no concede permisos de compra ni envía POST.
  - La URL se valida y se limpia al cerrar/guardar. Si el faltante es cero, se conserva la propuesta cero y el usuario debe elegir una cantidad mayor a cero para registrar una compra.

### Mejora 2: Armonización del Criterio de Alerta (`<` vs `<=`)
- **Antecedente:**
  - En CU8 (`InventarioTab`), un insumo entra en semáforo `bajo_minimo` si `stock <= stock_minimo`.
  - En CU9 (`selectors.py`), la alerta se dispara estrictamente con `stock < stock_minimo` (si `stock == stock_minimo`, no alerta).
- **Solución propuesta:**
  - Unificar el criterio en `selectors.py` a `stock_para_alerta__lte=F('stock_minimo')`.
  - Implementado mediante `filtrar_materias_primas_bajo_minimo`, compartido por el selector CU09 y el filtro CU08. `Coalesce` mantiene stock cero para inventario ausente; se conservan los filtros existentes de CU08.
  - En una panadería, alcanzar exactamente el stock de seguridad ya amerita emitir una orden de compra preventiva antes de quedarse desabastecido.

### Mejora 3: Integración Visual y Ubicación del Acceso en `ProductosPage.tsx`
- **Antecedente:** El enlace estaba aislado sobre el título de ProductosPage.
- **Solución propuesta:**
  - Integrar el botón o banner de advertencia dentro de la pestaña **"Stock de materia prima" (`InventarioTab.tsx`)** al lado de la barra de acciones o los filtros.
  - Opcional: Mostrar un badge contador de alertas activas en la pestaña "Stock de materia prima" (ej. `Stock de materia prima (2)`).
  - Implementado en la barra de acciones de `InventarioTab`, con contador global obtenido del endpoint CU09 mediante el mismo hook usado por la página. No depende de filtros o búsqueda CU08. Se actualiza al refrescar o modificar el catálogo desde la pestaña.
  - Permiso y roles CU09 se conservan. La pestaña también admite usuarios autorizados CU09 para consulta; editar, crear o inactivar sigue exigiendo el permiso CU08. CU12 y las demás pestañas permanecen disponibles bajo sus controles anteriores.

### Mejora 4: Tarjetas KPI y buscador en `AlertasBajoStockPage.tsx`
- **Antecedente:** La pantalla mostraba una tabla sin métricas agregadas ni buscador.
- **Solución propuesta:**
  - Añadir 3 tarjetas KPI superiores:
    1. *Total de materias primas en alerta crítica*.
    2. *Insumos agotados (stock = 0)*.
    3. *Mayor faltante por unidad*, identificado con nombre del insumo y su unidad. No se compara ni suma kg, litros y unidades entre sí.
  - Añadir un campo de búsqueda reactiva por nombre para localizar rápidamente un insumo específico cuando el inventario crezca.
  - Implementado: búsqueda sin distinguir mayúsculas ni tildes. Los KPI consideran todas las alertas y la búsqueda solo filtra la tabla. Estados de carga, error, sin alertas, búsqueda sin resultados y actualización manual diferenciados.

## 5. Validación y límites
- 15 pruebas CU09, 5 CU08 y 8 CU07: 28 aprobadas en SQLite en memoria y PostgreSQL temporal. Se comprobó la ausencia de la base temporal antes de crearla y se eliminó únicamente la creada en esta ejecución.
- Django check, build React/TypeScript, lint de archivos modificados y diff check aprobados. Sin modelos o migraciones nuevos, ni cambios en bases existentes o permisos CU07.
- La regla inclusiva es una decisión expresa del equipo. Estar en el mínimo sigue siendo alerta aunque el faltante calculado sea cero.
- Limitación previa CU07: una materia prima sin registro de inventario puede consultarse como stock cero, pero su compra mantiene el rechazo existente del servicio. Este refinamiento no crea inventarios al consultar ni cambia el backend de compras.
- Bitácora: `docs/ai/sessions/2026-10-13-codex-cu09-refinamientos.md`.
- Chrome real con perfil aislado: 26 comprobaciones de interfaz aprobadas, sin excepciones JavaScript. La API fue simulada para evitar escrituras en bases locales; se verificó que abrir la precarga no envía compras y que el único POST de prueba se produce tras guardar intencionalmente.
