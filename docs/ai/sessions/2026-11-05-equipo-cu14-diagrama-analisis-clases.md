# Sesión: CU14 — diagrama análisis de clases (cardinalidades y generalización)

## Objetivo
Completar el diagrama de análisis de clases del CU14 con flechas de asociación etiquetadas (como CU03) y relaciones de generalización donde aplica.

## Cambios
- **Documentación / UML:** `docs/informes/CU14_diagrama_analisis_clases.drawio` reescrito **alineado al código**.
  - Frontera `RegistrarPedidoPage`, controlador `PedidoController` (vistas DRF + servicios `registrar_pedido`, `pagar_pedido`, `cambiar_estado_pedido`, `entregar_pedido`).
  - Atributos en snake_case según modelos Django; sin `ci_nit`; `pagado` en `Pedido`.
  - Enums del repo: `EstadoPedido`, `MetodoPago`, `AccionBitacora` (valores CU14), `TipoMovimientoProductoTerminado`.
  - Composición Pedido–DetallePedido y Venta–DetalleVenta; `Pedido`–`Venta` 0..1 (OneToOneField); `Producto`–`Inventario` 1–0..1 (OneToOne).
  - Eliminada generalización `DetalleLinea` (no existe en Django).

## Decisiones
- Sin herencia entre modelos: refleja la implementación real.
- Dependencias punteadas controlador → entidades; asociaciones solo entre entidades/enums con cardinalidad.

## Cómo probar
- Abrir `docs/informes/CU14_diagrama_analisis_clases.drawio` en diagrams.net y verificar flechas + etiquetas `1`, `0..*`, `1..*`, `0..1` y flechas de generalización hacia `DetalleLinea`.
