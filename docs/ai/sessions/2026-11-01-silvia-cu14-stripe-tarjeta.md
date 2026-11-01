# Sesión de Desarrollo: CU14 — tarjeta Stripe al entregar

- **Fecha:** 2026-11-01
- **Autor / Integrante:** Silvia
- **Paquete / Módulo:** `apps.comercializacion.pedidos` | `frontend`
- **Casos de Uso abordados:** CU14
- **Ciclo:** Ciclo 3

---

## 1. 🎯 Objetivo de la sesión

Quitar el pago «QR» del registro de pedido y cobrar con el mismo formulario de tarjeta de Stripe que usa el mostrador. Al cancelar, conservar el aviso anterior y agregar que no hay devolución del dinero.

## 2. 🛠️ Cambios realizados

- **Backend:**
  - `GET /api/pedidos/stripe/config/` devuelve la clave pública.
  - `POST /api/pedidos/<id>/stripe/intencion/` crea el PaymentIntent con el total congelado del pedido listo. No entrega ni descuenta stock.
  - `crear_intencion` acepta `origen`. El pedido usa `cu14-pedido`. La venta de mostrador sigue en `cu13-mostrador`.
  - La entrega sigue confirmando el id de Stripe que devuelve el formulario.
- **Frontend:**
  - En `RegistrarPedidoPage.tsx` el método previsto dice Tarjeta / Stripe.
  - Al entregar un pedido con tarjeta se abre `ModalPagoTarjeta` (CardElement). Se quitaron los campos de número, mes, año y CVC.
  - El diálogo de cancelación agrega: «Al cancelar el pedido no habrá devolución del dinero.»

## 3. 🧠 Decisiones técnicas tomadas

- El cobro sigue ocurriendo al entregar, no al guardar el pedido. Guardar solo deja el método previsto.
- La intención del pedido usa el total ya guardado. Si el catálogo cambió de precio, Stripe cobra el precio congelado del detalle.
- El formulario de tarjeta es el mismo del CU13. El pedido le pasa su propia intención y su propia clave pública, porque quien registra pedidos no necesita el permiso `registrar_ventas`.

## Corte 2 — la pasarela se abre al cobrar la tarjeta

- **Problema:** elegir Tarjeta y pulsar Guardar no abría Stripe. La ventana solo existía al entregar un pedido ya listo, y sin claves la pasarela no puede dibujar la tarjeta.
- **Frontend:** con Tarjeta, el botón pasa a «Pagar … con tarjeta» y abre `ModalPagoTarjeta` en ese momento, igual que el mostrador.
- **Backend:** `POST /api/pedidos/stripe/intencion/` cotiza el carrito y crea el PaymentIntent sin guardar el pedido. Si el cobro queda confirmado, el alta guarda `pedido.id_transaccion_stripe`. Al entregar se reutiliza ese id y no se pide la tarjeta otra vez.
- **Migración:** `pedidos.0002_pedido_id_transaccion_stripe`, aplicada en el Postgres de Docker.
- **Pruebas:** 19 OK en SQLite.
- **Sigue pendiente:** `backend/.env` no tiene `STRIPE_SECRET_KEY` ni `STRIPE_PUBLISHABLE_KEY`. Sin esas claves de prueba la ventana se abre, pero Stripe no muestra el formulario de la tarjeta.

## Corte 3 — aviso al guardar

- **Frontend:** al guardar en efectivo o después de cobrar con tarjeta, aparece el diálogo «El pedido ha sido guardado», con el número, el cliente y el total. El ticket se vacía para armar otro pedido.

## 4. ⚠️ Pendientes o siguientes pasos

- No se pulsó Entregar con una tarjeta real de prueba en el navegador.
- CU15 y CU16 siguen fuera.

## 5. 🧪 Cómo probar lo implementado

- `python manage.py test apps.comercializacion.pedidos` con SQLite: 17 pruebas en verde.
- En la pantalla: elegir Tarjeta, guardar, avanzar hasta listo y pulsar Entregar. Debe abrirse «Pagar con tarjeta» con el campo de Stripe, no un QR.
- Cancelar debe mostrar el texto anterior y, al final, que no habrá devolución del dinero.
