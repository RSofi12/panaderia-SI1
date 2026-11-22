# Resumen de Entrega y Continuidad (HANDOFF LATEST)

## 📌 Proyecto: Sistema de Información Web - Panadería Santiago (SI-1)
- **Fecha:** 2026-10-22
- **Estado del Ciclo:** Ciclo 1 consolidado (CU1–CU6, CU26) + **Ciclo 2 consolidado** (CU7–CU12) + **Ciclo 3 en progreso (CU13 consolidado 🟢)**
- **Entorno:** Docker Compose (Recomendado: 1 comando para db, mailpit, backend y frontend) o Local directo

---

## 📊 1. Estado real por caso de uso

| CU | Nombre | Estado | Dónde está |
|---|---|:---:|---|
| CU1 | Iniciar sesión | 🟢 Completo end-to-end | `auth_app/` + `LoginPage.tsx` (Split-Screen, Sugo font, iconos Lucide) |
| CU2 | Recuperar contraseña | 🟢 Completo end-to-end | `recuperacion/` + `ForgotPasswordPage.tsx` + `ResetPasswordPage.tsx` |
| CU3 | Gestionar usuarios | 🟢 Completo end-to-end | `users/` + `src/apps/dashboard/usuarios/` |
| CU4 | Asignar roles y permisos | 🟢 Completo end-to-end | `roles/` + `permisos/` + `src/apps/dashboard/usuarios/roles/` |
| CU5 | Gestionar productos (catálogo) | 🟢 Completo end-to-end | `productos/` + `src/apps/dashboard/productos/` |
| CU6 | Gestionar proveedores | 🟢 Completo end-to-end | `compras/` + `src/apps/dashboard/proveedores/` |
| CU26 | Gestionar bitácora | 🟢 Completo end-to-end | `bitacora/` + `src/apps/dashboard/usuarios/bitacora/` |
| CU7 | Registrar compra de materia prima | 🟢 Completo end-to-end | `compra_materia_prima/` + `src/apps/dashboard/compras/` |
| CU8 | Gestionar materia prima (CRUD+Stock) | 🟢 Completo end-to-end | `materia_prima/` + `src/apps/dashboard/productos/inventario/` |
| CU9 | Consultar alertas de bajo stock | 🟢 Completo y refinado | Regla <= compartida CU08, acceso y contador desde InventarioTab, KPI por unidad y búsqueda, precarga editable CU07 bajo registrar_compras |
| CU10 | Registrar producción diaria | 🟢 Completo end-to-end | `produccion/` + `RegistrarProduccionModal.tsx` |
| CU11 | Consultar historial de producción | 🟢 Completo end-to-end | `produccion/` + `src/apps/dashboard/productos/produccion/` |
| CU12 | Consultar existencias de pan | 🟢 Completo end-to-end | `productos_terminados/` + `src/apps/dashboard/productos/existencias/` |
| CU13 | Registrar venta en mostrador | 🟢 Completo end-to-end | `apps.comercializacion.ventas` + `src/apps/dashboard/comercializacion/ventas/` |

Detalle completo por caso de uso: [`CURRENT_STATE.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/CURRENT_STATE.md)  
Registro de decisiones: [`DECISIONS_LOG.md`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/ai/DECISIONS_LOG.md)  

---

## 📦 2. Lo entregado en esta sesión

### Implementación Completa de CU13 (Registrar Venta con Efectivo y Stripe)
- **Backend (`apps.comercializacion.ventas`):**
  - Registro transaccional atómico de venta con descuento en `InventarioProductoTerminado` y creación de movimientos de salida en Kardex.
  - Métodos soportados: `efectivo` y `stripe`.
  - Pasarela Stripe: Endpoint `GET /api/ventas/stripe/config/` (`StripeConfigView`) para exponer la `publishable_key`.
  - Cobro seguro vía `PaymentIntent`, control de monto mínimo en BOB y auto-reembolso atómico (`Refund.create`) en caso de inconsistencia de stock.
  - Auditoría en `Bitacora` bajo la acción `REGISTRO_VENTA`.
  - 16 pruebas unitarias específicas pasando al 100% en verde.
- **Frontend (`src/apps/dashboard/comercializacion/ventas/`):**
  - Integración oficial de `@stripe/react-stripe-js` y `@stripe/stripe-js`.
  - Modal oficial responsivo (`ModalPagoTarjeta.tsx`) con `<CardElement>`.
  - Formato modal estándar de Stripe (con verificación oficial, conexión cifrada y soporte nativo para Link en HTTPS).
  - Ingreso manual de tarjeta de prueba (`4242...`) con validación nativa de Stripe y diseño limpio sin credenciales en la UI.
  - Variables de entorno unificadas en `frontend/.env` (`VITE_STRIPE_PUBLISHABLE_KEY`) y `backend/.env`.

---

## 🧪 3. Verificación ejecutada

| Verificación | Entorno | Resultado |
|---|---|---|
| Suite de pruebas `apps.comercializacion.ventas` | Backend Django / SQLite | ✅ **Exitoso (16/16 tests OK en verde)** |
| Endpoint configuración Stripe (`/api/ventas/stripe/config/`) | Backend Django dev server | ✅ **Exitoso (HTTP 200 con publishable_key)** |
| Build de producción Frontend (`npm run build`) | Vite / TypeScript | ✅ **Exitoso (0 errores de tipado, 0 lints)** |
| Hot Module Replacement y Vite dev server | Frontend dev server | ✅ **Exitoso (puerto 5173 activo)** |

---

## 🔜 4. Punto exacto de reanudación

**Siguiente paso (Ciclo 3):**
1. **CU14: Registrar pedido:** Flujo de reservas anticipadas con fecha y abono/adelanto.
2. **CU16: Generar comprobante de venta:** Generación e impresión/descarga en PDF de factura/ticket de venta para CU13.

---

## ⚙️ 5. Comandos de verificación y ejecución

### Opción 1: Docker Compose (Recomendado — 1 sola terminal)
```powershell
# Iniciar los 4 servicios (db, mailpit, backend, frontend)
docker compose up -d

# Migrar y sembrar datos iniciales en la base de datos de Docker
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_usuarios
docker compose exec backend python manage.py seed_productos
docker compose exec backend python manage.py seed_proveedores

# Ver estado de los contenedores
docker compose ps
```

### Opción 2: Local directo
```powershell
# Frontend
cd frontend
npm run build
npm run dev

# Backend
cd ..\backend
.\venv\Scripts\python.exe manage.py check
```

### Refinamientos CU09 — 2026-10-13
- Comprar abre el formulario CU07 existente con ID/cantidad editables y catálogo activo; exige registrar_compras y no registra automáticamente.
- CU08/CU09 comparten selector stock_actual <= stock_minimo con inventario ausente como cero; igualdad genera faltante cero.
- Acceso movido a Stock de materia prima, con contador del mismo endpoint CU09. Permisos personalizados CU09 conservan acceso de consulta; edición sigue exigiendo gestionar_materias_primas. CU12 y demás pestañas/rutas intactas.
- KPI total/agotados/mayor faltante por unidad y buscador; estados carga/error/vacío/sin resultados/actualizar. Unidades heterogéneas no se suman ni comparan.
- Verificación: 28 pruebas CU07/CU08/CU09 en SQLite memoria y PostgreSQL temporal aprobadas; check, build, lint de archivos modificados y diff check aprobados. 26 comprobaciones Chrome con API simulada sin excepciones JavaScript.
- No se modificaron bases existentes ni se aplicaron migraciones locales. Base temporal eliminada. Sin modelos/migraciones nuevos ni dependencias añadidas a manifests; stash intacto, sin commit/push/merge.
- Límite previo: compra CU07 rechaza un insumo sin inventario; este refinamiento no cambia ese servicio. Chrome y Vite de prueba cerrados; perfiles temporales externos conservados porque la revisión automática rechazó eliminarlos (blocked by policy).
- Bitácora: docs/ai/sessions/2026-10-13-codex-cu09-refinamientos.md. Informe: docs/informes/CU09_mejoras_pendientes.md.

### Preparación CU19 — 2026-10-22 (solo análisis)

- Copia de trabajo: `C:\Users\vacaa\Downloads\panaderia-SI1-main-actualizado`; main local actualizado por fast-forward y rama nueva `feature/cu19-historial-precios` desde `origin/main` `7a5031baaeb4b4ad109eaf22218584ddfcfdf3ff`.
- La copia antigua, sus cambios de CU09, archivos personales y stash se conservaron. Los archivos de entorno y herramientas locales de la copia preparada no se modificaron.
- Hallazgo de alcance: el mapa oficial define CU19 como historial de precios de venta de productos, mientras la solicitud también trata materias primas y proveedores. `HistorialPrecioProducto` y `HistorialPrecioMateriaPrima` ya existen; no hay API/pantalla CU19. Ningún historial guarda compra o proveedor; para precios pagados con proveedor la fuente inequívoca es `DetalleCompra → Compra → Proveedor`.
- Propuesta mínima documentada: consulta paginada de lectura en `productos`, protección de rol Propietario y permiso explícito, tabla y filtros sin nueva tabla ni cambios de CU07/CU08/CU09. La variante de compras y la posibilidad de un permiso granular son propuestas pendientes de decisión, no implementaciones.
- No se ejecutaron aplicaciones, pruebas funcionales, migraciones o seeders ni se conectaron bases locales/Render en esta etapa. Sin cambios de código, commits o pushes.
- Siguiente paso: revisar el [informe CU19](../informes/CU19_analisis_tecnico.md), resolver alcance/actores/permiso y obtener autorización para implementar. Mantener la pestaña `historial` existente como CU11, sin reutilizar su ruta para precios.
- Bitácora: [2026-10-22-codex-cu19-analisis.md](sessions/2026-10-22-codex-cu19-analisis.md).

### Implementación CU19 — 2026-10-22

- El usuario aprobó implementar exclusivamente historial de precios de venta de productos, para Propietario con `gestionar_productos`, sin acceso implícito de Administrador/superusuario. La discrepancia registrada en el análisis quedó resuelta sin ampliar a materias primas o proveedores.
- API: `GET /api/productos/historial-precios/`, filtros `id_producto`, `fecha_desde`, `fecha_hasta`, `page`; páginas de 10, precio decimal como string, fechas inclusivas del negocio y orden fecha/ID descendentes. Incluye productos inactivos y no modifica datos al consultar.
- Pantalla: `/dashboard/productos/historial-precios`, acceso desde Productos solo con rol y permiso aprobados, tabla y filtros, carga/error/vacíos/reintentos/paginación. CU11 conserva su pestaña `historial`.
- Sin modelos, migraciones, bibliotecas, permisos nuevos ni modificaciones de configuración local o escritores anteriores.
- Pruebas: 61 aprobadas en PostgreSQL temporal: CU19 28, CU05 5, CU07 8 y CU08/CU09 20. Se detectó y corrigió el tratamiento de parámetros vacíos de QueryDict sin eliminar pruebas.
- `manage.py check`, comprobación de migraciones, build y lint de archivos modificados correctos. Lint global conserva 14 errores y 1 advertencia en archivos ajenos a CU19.
- Implementación revisada independientemente sin hallazgos abiertos; pruebas de navegador aisladas documentadas en la entrega técnica.
- No hacer commit/push/merge hasta la revisión final del usuario. Informe y lista exacta de archivos: [CU19_implementacion_tecnica.md](../informes/CU19_implementacion_tecnica.md). Bitácora: [sesión de implementación](sessions/2026-10-22-codex-cu19-implementacion.md).
