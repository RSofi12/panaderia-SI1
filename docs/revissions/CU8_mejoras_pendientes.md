# Diagnóstico y Mejoras Pendientes — CU08: Gestionar Materia Prima

- **Fecha:** 2026-10-13
- **Módulo / Componente:** `frontend/src/apps/dashboard/productos/inventario/InventarioTab.tsx`
- **Backend:** `backend/apps/productos_inventario/materia_prima/`
- **Referencia Arquitectónica:** `backend/apps/PACKAGE_CU_MAP.md` (Ciclo 2)

---

## 🔍 1. Diagnóstico: ¿Por qué no aparecen los botones de "Nueva materia prima", "Editar" ni "Inactivar"?

Al revisar la captura de pantalla compartida por el usuario:
- El usuario en sesión es **Miguel Ángel Rojas (`@mrojas`)**, cuyo rol es **Personal de Producción**.
- En el código de `InventarioTab.tsx`, los controles de mutación están protegidos por:
  ```tsx
  const { hasPermission } = useAuth();
  const puedeGestionar = hasPermission('gestionar_materias_primas');
  ```
  - **Línea 224:** El botón `Nueva materia prima` solo se renderiza si `puedeGestionar === true`.
  - **Líneas 270 y 301:** La columna `Acciones` (con los botones `Editar` y `Inactivar / Activar`) solo se renderiza si `puedeGestionar === true`.

### Causa Raíz en la Matriz RBAC:
De acuerdo con la definición formal del PUDS y `PACKAGE_CU_MAP.md`:
1. **Actores del CRUD (crear, editar, inactivar):** *Administrador* y *Propietario*. Cuentan con el permiso `gestionar_materias_primas`.
2. **Actor de consulta de existencias:** *Personal de Producción*. Cuenta con el permiso `registrar_produccion` y `gestionar_inventario`. **No cuenta con `gestionar_materias_primas`**.

> **Conclusión:** Las funcionalidades CRUD sí están implementadas en el frontend y backend, pero están correctamente ocultas para el rol de Producción para evitar modificaciones no autorizadas en el maestro de insumos.  
> **Comprobación rápida:** Si inicias sesión con una cuenta de **Administrador** (`cgonzales` / `admin.global@mail.com`) o **Propietario** (`ptorrez` / `propietario@mail.com`), el botón verde/ámbar de `Nueva materia prima` y las opciones de edición aparecen en la pantalla inmediatamente.

---

## 🛠️ 2. Mejoras Recomendadas para CU08 (Backlog para el Equipo)

A continuación se listan las mejoras que el equipo debe implementar para perfeccionar este caso de uso:

### Mejora 1: Callout Informativo de Solo Consulta para Personal de Producción (UX)
- **Problema actual:** Cuando entra el Personal de Producción, la ausencia total de botones le hace pensar que el sistema falló o que el CRUD no está hecho.
- **Solución propuesta:**
  - Agregar un banner informativo sutil cuando `!puedeGestionar` (igual al que ya se implementó en `ProductosPage.tsx` para el catálogo de panes):
  ```tsx
  {!puedeGestionar && (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
      Estás visualizando el stock en modo de solo lectura. Para crear, editar o inactivar materias primas se requiere el rol de <span className="font-semibold text-slate-800">Administrador</span> o <span className="font-semibold text-slate-800">Propietario</span> (<code className="rounded bg-slate-200 px-1 py-0.5">gestionar_materias_primas</code>).
    </div>
  )}
  ```

### Mejora 2: Si el Negocio Define que Producción SÍ Debe Crear/Editar Insumos
- **Situación:** En algunas panaderías pequeñas, el maestro panadero necesita dar de alta un insumo nuevo que compró de urgencia.
- **Solución propuesta:**
  - No romper el código: simplemente asignar el permiso `gestionar_materias_primas` al rol `Personal de Producción` desde la matriz de permisos en `/dashboard/usuarios?tab=roles` (CU04) o actualizar el mapeo en `seed_usuarios.py`.

### Mejora 3: Drawer o Modal de Historial de Precios y Proveedores
- **Problema actual:** La tabla solo muestra `stock_actual` y `stock_minimo`. No se puede ver el último precio pagado ni qué proveedores surten ese insumo.
- **Solución propuesta:**
  - Al hacer clic sobre el nombre de la materia prima, desplegar un modal lateral con la información de `HistorialPrecioMateriaPrima` y la fecha de la última compra registrada (CU7).

### Mejora 4: Paginación y Filtro por Rango de Stock
- **Problema actual:** Se cargan todas las materias primas en una sola lista continua.
- **Solución propuesta:**
  - Añadir paginación de 10 o 15 filas por página.
  - Añadir filtro numérico por insumos con stock menor a un umbral personalizado.

### Mejora 5: Exportación de Inventario (Excel / PDF)
- **Problema actual:** Para hacer inventario físico en almacén, el panadero no tiene una hoja impresa de cotejo.
- **Solución propuesta:**
  - Añadir un botón "Exportar inventario" para imprimir o descargar en PDF/CSV las existencias actuales con casillas en blanco para el conteo físico.
