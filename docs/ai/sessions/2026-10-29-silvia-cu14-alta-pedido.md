# Sesión de Desarrollo: CU14 — alta de pedido

- **Fecha:** 2026-10-29
- **Autor / Integrante:** Silvia
- **Paquete / Módulo:** `apps.comercializacion.pedidos`
- **Casos de Uso abordados:** CU14
- **Ciclo:** Ciclo 3

---

## 1. 🎯 Objetivo de la sesión

Segundo corte del CU14: registrar un pedido en estado `pendiente` por API, sin pantalla, sin venta y sin descontar stock.

## 2. 🛠️ Cambios realizados

- **Backend:**
  - `ALTA_PEDIDO` en `AccionBitacora` y migración `bitacora.0012`.
  - Servicio `registrar_pedido`: cliente nuevo o existente, precio del catálogo, total en el servidor, bitácora.
  - `POST /api/pedidos/` y `GET /api/pedidos/<id>/`, permiso `registrar_pedidos`.
  - Cinco pruebas en `apps.comercializacion.pedidos.tests`.
- **Frontend:** sin cambios.

## 3. 🧠 Decisiones técnicas tomadas

- `CAMBIAR_ESTADO_PEDIDO` no se agregó. El cambio de estado es el corte 4.
- El método de pago queda guardado como intención. No se llama a Stripe.
- Si el producto está inactivo, la transacción no deja cliente ni pedido.

## 4. ⚠️ Pendientes o siguientes pasos

- Corte 3: pantalla en `/dashboard/comercializacion/pedidos`.
- Corte 4: estados hasta `listo` y `cancelado`.
- Corte 5: entrega, `venta.id_pedido` y descuento de stock reutilizando el CU13.
- Aplicar `pedidos.0001_initial` y `bitacora.0012` en PostgreSQL cuando Docker esté disponible.

## 5. 🧪 Cómo probar lo implementado

```powershell
$env:DB_ENGINE='django.db.backends.sqlite3'
python manage.py test apps.comercializacion.pedidos
```

Resultado de esta sesión: 5 pruebas OK. Con María (`mgonzales`) y `seed_productos`, un `POST /api/pedidos/` debe responder 201 y `estado: pendiente`.

---

## Corte 3 — pantalla de alta (misma fecha, segunda entrada)

- **Frontend:**
  - Ruta `/dashboard/comercializacion/pedidos` protegida con `registrar_pedidos`.
  - Enlace «Registrar pedido» en `ComercializacionPage.tsx`, junto a «Abrir mostrador».
  - `pedidos/pedidoService.ts` hace `POST /pedidos/` sin enviar precio ni total.
  - `pedidos/RegistrarPedidoPage.tsx` arma cliente, fecha, método previsto y líneas.
- El mostrador, la venta y el stock no se modifican.
- `npx tsc -b` en `frontend` terminó sin errores.
- Comprobado después: `panaderia_frontend` responde en `http://localhost:5173` (HTTP 200) y el archivo de la pantalla está montado en el contenedor.
- Pendiente de verificar en el navegador: iniciar sesión como María, abrir «Registrar pedido» y guardar un pedido.

---

## Corte 4 — cambio de estado, sin entrega (misma fecha, tercera entrada)

- **Backend:**
  - `CAMBIAR_ESTADO_PEDIDO` en `AccionBitacora` y migración `bitacora.0013`.
  - Servicio `cambiar_estado_pedido`: pendiente → en_preparacion|cancelado; en_preparacion → listo|cancelado; listo → cancelado. `entregado` responde error.
  - `GET /api/pedidos/` lista los abiertos. `PATCH /api/pedidos/<id>/` cambia el estado. Mismo permiso `registrar_pedidos`.
- **Frontend:** la pantalla lista los pedidos abiertos y muestra Preparar, Marcar listo o Cancelar según el estado.
- **Pruebas:** `python manage.py test apps.comercializacion.pedidos` con SQLite: 10 pruebas OK.
- **PostgreSQL (Docker):** se aplicaron `pedidos.0001_initial`, `bitacora.0012` y `bitacora.0013`. Al migrar pedidos, Django también aplicó migraciones de compras, proveedores, materia prima y producción que estaban pendientes porque el pedido depende de ellas.
- **Navegador, verificado:** María entró, abrió Registrar pedido, guardó el pedido 1 de Hotel Cortez Prueba (10 marraquetas, Bs 6.00, pendiente), pasó a en preparación y luego a listo. En listo solo queda Cancelar y el texto de que entregar todavía no está habilitado. La última venta en la base es del 13 de octubre. Desde las 06:20 UTC no hay movimientos de stock. La bitácora del pedido tiene `ALTA_PEDIDO` y dos `CAMBIAR_ESTADO_PEDIDO`.

---

## Corte 5 — entregar el pedido (misma fecha, cuarta entrada)

- **Backend:**
  - `venta.id_pedido` es uno a uno y puede quedar vacío en una venta de mostrador. Migración `ventas.0002`.
  - `movimiento_producto_terminado.id_pedido` puede quedar vacío. Migración `productos_terminados.0003`.
  - `entregar_pedido` solo desde `listo`. Crea una venta con el precio congelado del detalle, llama a `descontar_por_venta` y escribe `ALTA_VENTA`.
  - Efectivo no llama a Stripe. Tarjeta sin datos responde 400 y no cambia el estado.
- **Frontend:** en `listo` aparecen Entregar y Cancelar. Si el método previsto es tarjeta, la pantalla pide número, vencimiento y CVC.
- **Pruebas:** `apps.comercializacion.pedidos` y `apps.comercializacion.ventas` en SQLite: 28 OK. La entrega deja el stock en 30 (había 40 y se pidieron 10), una sola venta de Bs 6.00 aunque el catálogo ya valga Bs 5.00, y el kardex guarda el pedido.
- **PostgreSQL:** aplicadas `ventas.0002_venta_id_pedido` y `productos_terminados.0003_movimientoproductoterminado_id_pedido`.
- **Navegador:** con María, el pedido 1 (listo, efectivo, Bs 6.00) muestra el botón Entregar. No se pulsó: eso descontaría 10 marraquetas del stock real (hoy 33).
