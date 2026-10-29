# Sesión de Desarrollo: CU14 — modelos de pedido

- **Fecha:** 2026-10-28
- **Autor / Integrante:** Silvia
- **Paquete / Módulo:** `apps.comercializacion.pedidos`
- **Casos de Uso abordados:** CU14
- **Ciclo:** Ciclo 3

---

## 1. 🎯 Objetivo de la sesión

Primer corte del CU14: dejar persistibles el cliente, el pedido y el detalle, sin API, sin pantalla y sin tocar la venta ni el stock.

## 2. 🛠️ Cambios realizados

- **Backend:**
  - Sub-app nueva `backend/apps/comercializacion/pedidos/` con `Cliente`, `Pedido` y `DetallePedido`.
  - `PedidosConfig` registrada en `INSTALLED_APPS`.
  - Migración `pedidos.0001_initial`.
  - Admin de solo consulta para revisar las tablas.
- **Frontend:** sin cambios.
- **Base de datos:** la migración está escrita. No se aplicó en PostgreSQL en esta sesión (Docker no estaba levantado y el historial local de migraciones está inconsistente).

## 3. 🧠 Decisiones técnicas tomadas

- El pedido nace en `pendiente`. `fecha_entrega` admite NULL, como el DDL. El servicio del corte 2 la exigirá.
- `metodo_pago` reutiliza `MetodoPago` del CU13 y puede quedar vacío (pedido cancelado).
- Se agregó `pedido_estado_valido`. El DDL no trae ese CHECK; la población solo usa los cinco estados.
- La relación 0..1 con `venta` no entra en este corte.

## 4. ⚠️ Pendientes o siguientes pasos

- Corte 2: `ALTA_PEDIDO`, servicio de alta y `POST /api/pedidos/`.
- Aplicar `pedidos.0001_initial` cuando la base de Docker esté disponible.

## 5. 🧪 Cómo probar lo implementado

1. `python manage.py check`
2. Con la base sana: `python manage.py migrate pedidos`
3. Confirmar que existen `cliente`, `pedido` y `detalle_pedido`, y que un pedido nuevo queda en `pendiente`.
