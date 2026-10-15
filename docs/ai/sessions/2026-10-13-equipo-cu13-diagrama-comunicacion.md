# Sesión de Desarrollo: Diagrama de comunicación CU13

- **Fecha:** 2026-10-13
- **Autor / Integrante:** Equipo Panadería Santiago
- **Paquete / Módulo:** `apps.comercializacion.ventas` / documentación
- **Casos de Uso abordados:** CU13
- **Ciclo:** Ciclo 3

---

## 1. 🎯 Objetivo de la sesión
Dejar el diagrama de comunicación UML del CU13 (Registrar venta) en formato draw.io, con el mismo estilo del diagrama del CU07.

## 2. 🛠️ Cambios realizados
- **Documentación:**
  - `docs/informes/CU13_diagrama_comunicacion.drawio`: actor `:PersonalVentas`, fronteras `:RegistrarVentaPageView` y `:PasarelaStripe`, control `:VentaController` y entidades Producto, InventarioProductoTerminado, Venta, DetalleVenta, MovimientoProductoTerminado y Bitacora.
  - Flujos: 1 consultar ventas del día, 2 cobro con tarjeta (intención de pago y `confirmCardPayment`), 3 registrar venta (cotizar, confirmar cobro, bloquear stock, crear venta y detalles, descontar stock, kardex, total, bitácora, anulación del cobro si falla).
  - `docs/informes/CU13_diagrama_analisis_clases.drawio` (nuevo): diagrama de análisis de clases con el mismo formato que `CU07_diagrama_analisis_clases.drawio`. Actor Personal de Ventas, `<<Interface>>` UI Registrar Venta, `<<Interface>>` Pasarela Stripe (sistema externo, unida a la UI por `confirmCardPayment` y al controlador por PaymentIntent y reembolso), `<<Controller>>` Venta Controller (permiso `registrar_ventas`), entidades Venta, DetalleVenta, Producto, InventarioProductoTerminado, MovimientoProductoTerminado, Bitacora y Usuario, y enums MetodoPago y TipoMovimiento.
- **Backend:** sin cambios.
- **Frontend:** sin cambios.

## 3. 🧠 Decisiones técnicas tomadas
- El control agrupa `VentaListCreateView`, `IntencionStripeView` y el servicio `registrar_venta`.
- Stripe se modela como frontera porque es un sistema externo.
- Las iteraciones por línea de venta usan la notación `*[∀ línea]`; los mensajes condicionados usan guardas (`[stripe]`, `[error ∧ stripe]`).

## 4. ⚠️ Pendientes o siguientes pasos
- Exportar a imagen e insertar en el informe del CU13.
- Ajustar a mano en draw.io cualquier etiqueta que quede encima de una línea.

## 5. 🧪 Cómo probar lo implementado
- Abrir `docs/informes/CU13_diagrama_comunicacion.drawio` en diagrams.net.
- Comparar el orden del flujo 3 con `backend/apps/comercializacion/ventas/services/registrar_venta.py`.
- Abrir `docs/informes/CU13_diagrama_analisis_clases.drawio` y revisar multiplicidades: venta 1 a 1..* detalles, producto 1 a 1 inventario, venta 0..1 a 0..* movimientos (`id_venta` es opcional porque también hay movimientos de producción y mermas).
