# Sesión de Desarrollo: CU13 Registrar venta

- **Fecha:** 2026-10-13
- **Autor / Integrante:** Equipo
- **Paquete / Módulo:** `apps.comercializacion.ventas` | `frontend`
- **Casos de Uso abordados:** CU13
- **Ciclo:** Ciclo 3

---

## 1. 🎯 Objetivo de la sesión

Registrar una venta de mostrador que calcule el total, descuente el stock de producto terminado y cobre solo en efectivo o con Stripe.

## 2. 🛠️ Cambios realizados

- **Backend:**
  - Sub-app nueva `backend/apps/comercializacion/ventas/` (modelos, servicio, Stripe, vistas, urls, pruebas).
  - `POST /api/ventas/`, `GET /api/ventas/`, `GET /api/ventas/<id>/`, `POST /api/ventas/stripe/intencion/`.
  - Descuento de stock en `productos_terminados/services/descontar_stock.py`.
  - Columna `id_venta` en el kardex de producto terminado.
  - Acción de bitácora `ALTA_VENTA` (migración `bitacora.0011`).
- **Frontend:**
  - Pantalla `frontend/src/apps/dashboard/comercializacion/ventas/`.
  - Ruta `/dashboard/comercializacion/ventas`, permiso `registrar_ventas`.
- **Base de datos documentada:**
  - `Database_Panaderia_Santiago.sql`: métodos `efectivo` y `stripe`.
  - `Poblacion_4_Dias_Panaderia_Santiago.sql`: el método que decía `qr` pasó a `stripe`.

## 3. 🧠 Decisiones técnicas tomadas

- El mostrador no contempla otro método. Efectivo guarda `id_transaccion_stripe` en NULL. Stripe exige el id del PaymentIntent confirmado.
- El precio sale del catálogo. El navegador no envía el total.
- Si Stripe ya cobró y el stock no alcanza, se pide el reembolso y no queda la venta.
- `id_pedido` queda para el CU14.

## 4. ⚠️ Pendientes o siguientes pasos

- Pegar `STRIPE_SECRET_KEY` y `VITE_STRIPE_PUBLISHABLE_KEY` de la cuenta de prueba.
- Si Stripe no acepta `bob`, cambiar `STRIPE_CURRENCY`.
- CU14 a CU17 siguen planificados.
- En Docker ya se aplicaron `ventas.0001`, `productos_terminados.0001` y `0002`, `produccion.0001`, `productos.0001` (solo estado) y `bitacora.0010`–`0011`.
- Quedó una venta de prueba: comprobante 1, 2 marraquetas en efectivo, total Bs 1.20; el stock de Marraqueta pasó de 40 a 38.
- Si se recrea la imagen de Docker, hay que volver a construir frontend y backend para que `@stripe/*` y el paquete `stripe` queden dentro de la imagen (`requirements.txt` y `package.json` ya los declaran).

## 5. 🧪 Cómo probar lo implementado

1. `python manage.py migrate`
2. `python manage.py test apps.comercializacion.ventas`
3. Entrar con un usuario que tenga `registrar_ventas` y abrir `/dashboard/comercializacion/ventas`.
4. Cobrar en efectivo y revisar que el stock del CU12 bajó y la bitácora tiene `ALTA_VENTA`.

## 6. 🎨 Rediseño del frontend (misma fecha, segunda entrada)

- **Objetivo:** que Comercialización muestre solo lo implementado (CU13) y que el mostrador sea cómodo para el cajero.
- **`ComercializacionPage.tsx`:** se quitaron las tarjetas planificadas de CU14–CU17. Queda un bloque «Mostrador» con el botón «Abrir mostrador», el resumen del día (vendido, efectivo, tarjeta) y las últimas 5 ventas. Sin `registrar_ventas` se muestra un aviso en lugar del botón.
- **`ventas/RegistrarVentaPage.tsx`:** buscador y filtro por categoría; tarjetas de pan con precio, «Quedan N» y contador de lo que ya está en el ticket; ticket lateral fijo con botones −/+, «Vaciar» y total grande; selector Efectivo / Tarjeta; en efectivo, monto recibido opcional con billetes rápidos (Exacto, 10, 20, 50, 100, 200) y cálculo del cambio; diálogo de venta registrada con comprobante, detalle y cambio (Esc o «Nueva venta» lo cierran); tabla «Ventas de hoy» con hora, método y cajero.
- **`ventas/FormularioStripe.tsx`:** botón «Cobrar Bs X con tarjeta» y error de tarjeta en línea.
- **`ventas/ChipMetodo.tsx`:** etiqueta Efectivo/Tarjeta compartida por las dos pantallas.
- **`index.css`:** animaciones de entrada y borde dentado de ticket; respetan `prefers-reduced-motion`.
- **Decisión:** el monto recibido y el cambio son solo ayuda en pantalla; no se envían al backend ni cambian el modelo `Venta`. El total válido sigue siendo el que calcula el servidor.
- **Verificado en el navegador** con María: 3 marraquetas + 1 tortilla = Bs 3.55; con Bs 10 el cambio fue Bs 6.45; se registró el comprobante 4 y la tabla del día se actualizó. Tarjeta sin clave muestra el aviso de configuración. `tsc -b` y `eslint` sin errores.

Verificación del 13-10-2026 en Docker: `POST /api/ventas/` con María (`mgonzales`) en efectivo respondió 201, comprobante 1, total 1.20 y stock 38. `qr` respondió 400, Stripe sin clave respondió 400 y Producción (`mrojas`) respondió 403. Vite compiló `RegistrarVentaPage.tsx` (el paquete de Stripe ya resuelve dentro del contenedor). La pantalla pide sesión: sin login redirige a `/login`.
