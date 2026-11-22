# Sesión de Desarrollo: CU21 — reporte mensual de ventas

- **Fecha:** 2026-11-01
- **Autor / Integrante:** Silvia
- **Paquete / Módulo:** `apps.reportes` | `frontend`
- **Casos de Uso abordados:** CU21
- **Ciclo:** Ciclo 4

---

## 1. 🎯 Objetivo de la sesión

Mostrar el reporte de ventas de un mes sin ampliar la base de datos.

## 2. 🛠️ Cambios realizados

- **Backend:** `GET /api/reportes/ventas/?desde=&hasta=` suma `venta` en ese rango y agrupa el detalle por producto. Permiso `generar_reportes`. No hay migración.
- **Frontend:** en Reportes, el CU21 pide un mes, lo convierte en día 1 y último día, y muestra total, efectivo, tarjeta y productos.

## 3. 🧠 Decisiones técnicas tomadas

- Un mes no es una tabla. Es `fecha_hora` entre dos fechas.
- La suma vive en el servidor. La pantalla solo elige el mes y muestra la respuesta.
- El cierre estático queda para después.

## 4. ⚠️ Pendientes o siguientes pasos

- Cargar septiembre, octubre y noviembre con efectivo y tarjeta para la demostración.
- CU22 a CU25 siguen planificados.

## Corte 2 — reporte dinámico y cierre estático

El mismo cálculo ahora tiene dos salidas.

- **Dinámico:** día, semana o mes, y filtro de método de pago. `GET /api/reportes/ventas/` vuelve a sumar `venta`.
- **Estático:** `POST /api/reportes/ventas/cierres/` guarda totales y productos en `cierre_reporte_ventas` y `linea_cierre_reporte_ventas`. Esa copia no se recalcula. Migración `reportes.0001` y bitácora `0015` (`CIERRE_REPORTE_VENTAS`).
- El nombre del producto se copia en la línea del cierre para que un cambio posterior del catálogo no reescriba el cierre.

## Corte 3 — CSV dinámico y PDF del cierre

- `GET /api/reportes/ventas/csv/` vuelve a sumar y devuelve el archivo. Separador `;` y UTF-8 con BOM para Excel.
- `GET /api/reportes/ventas/cierres/<id>/pdf/` dibuja el PDF desde la fila guardada. Dependencia `reportlab`.
- En la pantalla, Descargar CSV está en el dinámico y Descargar PDF en el cierre abierto.

## Corte 4 — ventas de tres meses para la demostración

El docente pidió datos de tres meses. No hubo tabla nueva.

- Comando `seed_ventas_demo`: 30 ventas de María, de septiembre a noviembre de 2026, en varios días, efectivo y tarjeta.
- Las 15 ventas anteriores se conservan. El comando no descuenta stock y no se vuelve a ejecutar si ya existe el marcador `pi_demo_cu21_`.
- Los cierres estáticos guardados antes siguen con sus totales viejos. El dinámico de esos meses ahora suma también las ventas nuevas.

## Corte 5 — el paquete de reportes queda solo para el Propietario

CU21 a CU25 tienen un solo actor en la matriz: el Propietario. El permiso `generar_reportes` se lo había llevado también el Administrador y Personal de Ventas, y el menú además abría Reportes a quien tuviera `gestionar_usuarios`.

- El seed deja el permiso 10 únicamente en el rol Propietario y borra esa asignación en los otros roles. `get_or_create` no quitaba filas viejas; el `delete` sí.
- El menú y la ruta `/dashboard/reportes` piden solo `generar_reportes`.
- La API ya rechazaba a quien no tiene ese permiso. No se cambió la regla del servidor: se alineó quién lo recibe.

Hay que volver a entrar. El menú lee los permisos del perfil cargado al iniciar sesión.

## 5. 🧪 Cómo probar lo implementado

- `python manage.py test apps.reportes` con SQLite.
- En Reportes, consultar 2026-10 (Bs 25.85) y 2026-11 (Bs 9.70) con un usuario que tenga `generar_reportes`.
