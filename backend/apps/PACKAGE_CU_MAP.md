# Mapa de paquetes y casos de uso (backend)
**Proyecto:** Sistema de Información Web para la Gestión de Ventas, Producción, Inventario y Control Administrativo — Panadería Santiago

Este documento organiza los 26 casos de uso definidos para el proyecto según dos criterios:
1. **Paquete (Django app)** — a qué módulo del backend pertenece cada CU.
2. **Ciclo de desarrollo (PUDS iterativo-incremental)** — en qué iteración se implementa.

Convención de nombres: en el **código** los paquetes usan su nombre corto (sin "Gestión de"), para mantener rutas y nombres de app cortos. En la **documentación** se usa el nombre completo del módulo.

---

## Gestión de Usuarios y Seguridad (CU1, CU2, CU3, CU4, CU26)

- CU1 Iniciar sesión -> `apps.usuarios_seguridad` (Ciclo 1)
  Autenticación de usuarios mediante usuario y contraseña, validando credenciales y generando la sesión de acceso al sistema.
- CU2 Recuperar contraseña -> `apps.usuarios_seguridad` (Ciclo 1)
  Permite a un usuario restablecer su contraseña cuando la ha olvidado, mediante un mecanismo de verificación (token temporal).
- CU3 Gestionar usuarios -> `apps.usuarios_seguridad` (Ciclo 1)
  Registro, edición, activación e inactivación de las cuentas de usuario del sistema.
- CU4 Asignar roles y permisos -> `apps.usuarios_seguridad` (Ciclo 1)
  Asociación de roles a usuarios y definición de los permisos que cada rol tiene sobre los módulos del sistema.
- CU26 Gestionar bitácora -> `apps.usuarios_seguridad` (Ciclo 1)
  Consulta del historial de acciones (creación, modificación, eliminación) realizadas por los usuarios, con fecha, hora y responsable. Se implementa desde el Ciclo 1 en versión simple y se amplía en ciclos posteriores conforme aumenta la complejidad de los datos a auditar.

Alias lógico: `apps/UsuariosSeguridad/*`

---

## Gestión de Productos e Inventario (CU5, CU8, CU9, CU10, CU11, CU12, CU18, CU19)

- CU5 Gestionar productos -> `apps.productos_inventario` (Ciclo 1)
  Registro, edición, consulta e inactivación de los productos de panadería, junto con su categoría y precio de venta.
- CU8 Consultar stock de materia prima -> `apps.productos_inventario` (Ciclo 2)
  Consulta de las existencias actuales de cada insumo (harina, azúcar, levadura, sal, huevos, leche, mantequilla) disponibles para producción.
- CU9 Consultar alertas de bajo stock -> `apps.productos_inventario` (Ciclo 2)
  Identificación de las materias primas cuyo stock actual está por debajo del stock mínimo definido, para gestionar oportunamente su reposición.
- CU10 Registrar producción diaria -> `apps.productos_inventario` (Ciclo 2)
  Registro de las cantidades producidas de cada tipo de pan por jornada; descuenta automáticamente las materias primas consumidas e incrementa el stock de productos terminados.
- CU11 Consultar historial de producción -> `apps.productos_inventario` (Ciclo 2)
  Consulta de las producciones registradas por fecha o por producto, para comparar lo producido con lo vendido.
- CU12 Consultar existencias de productos terminados -> `apps.productos_inventario` (Ciclo 2)
  Consulta del stock disponible de cada tipo de pan listo para la venta.
- CU18 Registrar baja de productos terminados -> `apps.productos_inventario` (Ciclo 3)
  Registro de mermas o pérdidas de productos terminados que no llegaron a venderse, descontando el inventario correspondiente.
- CU19 Consultar historial de precios -> `apps.productos_inventario` (Ciclo 3)
  Consulta de los cambios históricos en el precio de venta de un producto a lo largo del tiempo.

Alias lógico: `apps/ProductosInventario/*`

---

## Gestión de Compras y Proveedores (CU6, CU7, CU20)

- CU6 Gestionar proveedores -> `apps.compras` (Ciclo 1)
  Registro y edición de los datos de los proveedores de materias primas e insumos.
- CU7 Registrar compra de materia prima -> `apps.compras` (Ciclo 2)
  Registro de una compra a un proveedor; actualiza automáticamente el inventario de materia prima y el historial de precios de los insumos.
- CU20 Registrar gasto/inversión -> `apps.compras` (Ciclo 4)
  Registro de los gastos e inversiones realizados por el negocio, distintos a la compra de materia prima (alquiler, mantenimiento, equipos, etc.).

Alias lógico: `apps/Compras/*`

---

## Comercialización (CU13, CU14, CU15, CU16, CU17)

- CU13 Registrar venta -> `apps.comercializacion` (Ciclo 3)
  Registro de una venta directa en mostrador; calcula el importe total y descuenta automáticamente el inventario de productos terminados.
- CU14 Registrar pedido -> `apps.comercializacion` (Ciclo 3)
  Registro de una solicitud anticipada de un cliente, especificando productos, cantidades y fecha de entrega prevista.
- CU15 Consultar estado de pedido -> `apps.comercializacion` (Ciclo 3)
  Consulta del estado actual de un pedido (pendiente, en preparación, listo, entregado o cancelado).
- CU16 Generar comprobante de venta -> `apps.comercializacion` (Ciclo 3)
  Generación del comprobante correspondiente a una venta o a la entrega de un pedido, indicando productos, cantidades, importe y método de pago.
- CU17 Consultar disponibilidad de productos -> `apps.comercializacion` (Ciclo 3)
  Consulta rápida de los productos disponibles para la venta al momento de atender a un cliente.

Alias lógico: `apps/Comercializacion/*`

---

## Reportes (CU21, CU22, CU23, CU24, CU25)

- CU21 Generar reporte de ventas -> `apps.reportes` (Ciclo 4)
  Reporte de las ventas realizadas en un periodo (diario, semanal o mensual), por producto o por método de pago.
- CU22 Generar reporte de producción -> `apps.reportes` (Ciclo 4)
  Reporte de las cantidades producidas en un periodo, permitiendo comparar producción y ventas.
- CU23 Generar reporte de existencias -> `apps.reportes` (Ciclo 4)
  Reporte del estado de las existencias de materias primas y productos terminados en un momento dado.
- CU24 Generar reporte de compras y gastos -> `apps.reportes` (Ciclo 4)
  Reporte de las compras a proveedores y de los gastos e inversiones realizados en un periodo.
- CU25 Generar reporte de resultados económicos -> `apps.reportes` (Ciclo 4)
  Reporte que relaciona los ingresos por ventas con los egresos por compras y gastos, mostrando el resultado económico del periodo. Es la base sobre la que a futuro se construirán los reportes dinámicos (ej. relación entre pérdidas, producción y ventas por periodo).

Alias lógico: `apps/Reportes/*`

---

## Resumen cruzado: paquete x ciclo

| Paquete | Ciclo 1 | Ciclo 2 | Ciclo 3 | Ciclo 4 | Total CU |
|---|---|---|---|---|---|
| Usuarios y Seguridad | CU1, CU2, CU3, CU4, CU26 | — | — | — | 5 |
| Productos e Inventario | CU5 | CU8, CU9, CU10, CU11, CU12 | CU18, CU19 | — | 8 |
| Compras y Proveedores | CU6 | CU7 | — | CU20 | 3 |
| Comercialización | — | — | CU13, CU14, CU15, CU16, CU17 | — | 5 |
| Reportes | — | — | — | CU21, CU22, CU23, CU24, CU25 | 5 |
| **Total por ciclo** | **7** | **6** | **7** | **6** | **26** |

---

## Nota técnica importante

Esta organización refleja **5 paquetes decididos por el equipo** (Usuarios y Seguridad, Productos e Inventario, Compras y Proveedores, Comercialización, Reportes). Si la docente pide mayor granularidad más adelante, el paquete `productos_inventario` es el candidato natural a dividirse en dos (`catalogo` + `inventario_produccion`), ya que fue una fusión hecha para llegar a 5 paquetes en vez de 6.

El Ciclo 1, que es el que se presenta actualmente, solo requiere los paquetes `apps.usuarios_seguridad` (CU1-CU4, CU26) además de la base de `apps.productos_inventario` (CU5) y `apps.compras` (CU6) para el registro inicial de catálogos.

---

## Fuentes usadas
- Perfil Proyecto SI-1 Grupo 3.md, punto **1.7** (alcance y módulos funcionales)
- `BASE_DE_DATOS_FISICO_final` — tablas y llaves foráneas usadas para verificar la pertenencia de cada CU a su paquete
- Decisiones acordadas en conversación: lista final de 26 CU, división en 4 ciclos, y elección de los 5 paquetes del backend
