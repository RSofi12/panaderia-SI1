# Sesión de Desarrollo: Diagrama de comunicación CU14

- **Fecha:** 2026-11-01
- **Autor / Integrante:** Equipo Panadería Santiago
- **Paquete / Módulo:** `apps.comercializacion.pedidos` / documentación
- **Casos de Uso abordados:** CU14
- **Ciclo:** Ciclo 3

---

## 1. 🎯 Objetivo de la sesión

Dejar los diagramas de comunicación del CU14 (Registrar pedido) con el mismo criterio del ejemplo de CU11: actor, frontera, control y entidades, mensajes numerados con funciones reales y sin parámetros. El retorno de una entidad hacia el controlador queda implícito.

## 2. 🛠️ Cambios realizados

- **Documentación:**
  - `docs/informes/CU14_diagrama_comunicacion.drawio`: siete páginas, una por flujo del código.
  - `docs/informes/CU14_diagrama_comunicacion.puml`: los mismos siete diagramas en PlantUML.
- **Backend:** sin cambios.
- **Frontend:** sin cambios.

Páginas y de dónde sale cada flujo:

1. Consultar pedidos abiertos — `listarAbiertos()` / `listar_pedidos_abiertos()`.
2. Registrar en efectivo — `guardar()` → `registrar_pedido()`. El pedido nace pendiente y pagado. No hay Stripe, venta ni stock.
3. Registrar con tarjeta — `abrirPasarela()`, `crearIntencionDeLineas()`, `confirmCardPayment()`, `confirmar_cobro_tarjeta()`, y `anular_cobro_tarjeta()` si el alta falla.
4. Pagar en efectivo un pedido que seguía sin cobrar — `pagar_pedido()`.
5. Pagar con tarjeta un pedido ya guardado — `crearIntencion()` con el total congelado y `pagar_pedido()`.
6. Cambiar estado — `cambiar_estado_pedido()` para preparar, listo o cancelar. Sin venta y sin stock.
7. Entregar — `entregar_pedido()`: líneas congeladas, venta, detalle, `descontar_por_venta()` y kardex.

## 3. 🧠 Decisiones técnicas tomadas

- Un diagrama por flujo. Juntar alta, cobro, estado y entrega en una sola hoja deja los mensajes ilegibles.
- `:PedidoController` agrupa las vistas `PedidoCreateView`, `PedidoDetailView`, `PedidoPagoView` y `PedidoStripe*` más los servicios `registrar_pedido`, `pagar_pedido`, `cambiar_estado_pedido` y `entregar_pedido`.
- `:PasarelaStripe` es frontera (sistema externo), igual que en el CU13. El modal habla con `confirmCardPayment()`; el controlador habla con `crear_intencion`, `confirmar_cobro_tarjeta` y `anular_cobro_tarjeta`.
- El catálogo de panes que carga la pantalla (`productoService.listar`) es del CU5 y no entra en estos diagramas.
- La numeración vuelve a empezar en 1 en cada página porque cada página es un diagrama distinto.

## 4. ⚠️ Pendientes o siguientes pasos

- Exportar cada página a imagen e insertarla en el informe del CU14.
- En diagrams.net, correr las etiquetas si alguna queda encima de una flecha larga.

## 5. 🧪 Cómo probar lo implementado

- Abrir `docs/informes/CU14_diagrama_comunicacion.drawio` en diagrams.net.
- Comparar la página 2 con `backend/apps/comercializacion/pedidos/services/registrar_pedido.py`.
- Comparar la página 3 con `preparar_cobro_tarjeta`, `ModalPagoTarjeta` y `guardarConTarjeta`.
- Comparar la página 7 con `entregar_pedido.py` y `descontar_por_venta`.

---

## Corte 2 — mismo dibujo que el CU06

El primer corte dejó siete páginas con las flechas sueltas, debajo de los símbolos. La referencia del equipo (CU06. Gestionar proveedores) es otra: un solo diagrama, símbolos en fila, una línea entre cada par, los pedidos arriba con flecha a la derecha y las respuestas abajo con flecha punteada a la izquierda. Las entidades son círculos a la derecha y el control se abre en ramas.

Quedó así en `docs/informes/CU14_diagrama_comunicacion.drawio` (una página, «CU14. Registrar pedido») y en el `.puml` del mismo nombre.

Los siete recorridos comparten los enlaces, numerados del 1 al 7:

1. Consultar abiertos.
2. Guardar en efectivo.
3. Abrir la pasarela y registrar con tarjeta. `confirmCardPayment()` sale de la frontera hacia `:PasarelaStripe` por arriba, porque el modal lo llama directo y no pasa por el controlador.
4. Pagar en efectivo un pedido que seguía sin cobrar.
5. Pagar con tarjeta un pedido ya guardado.
6. `mover()` para preparar, listo o cancelar.
7. Entregar: ahí aparecen venta, detalle, inventario y movimiento.

`:PedidoController` sigue agrupando las vistas y los servicios del pedido. Las entidades no devuelven flecha; quien responde a la pantalla es el controlador.
