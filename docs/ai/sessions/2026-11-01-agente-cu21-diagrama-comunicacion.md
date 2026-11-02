# Sesión de Desarrollo: Diagrama de comunicación CU21

- **Fecha:** 2026-11-01
- **Autor / Integrante:** Agente
- **Paquete / Módulo:** `apps.reportes` / documentación
- **Casos de Uso abordados:** CU21
- **Ciclo:** Ciclo 4

---

## 1. Objetivo de la sesión

Dejar el diagrama de comunicación del CU21 (Generar reporte de ventas) con el mismo criterio del ejemplo de CU11: actor, frontera, control y entidades, mensajes numerados con funciones del código y sin parámetros. El retorno de una entidad hacia el controlador queda implícito.

## 2. Cambios realizados

- **Documentación:**
  - `docs/informes/CU21_diagrama_comunicacion.puml`
  - `docs/informes/CU21_diagrama_comunicacion.drawio` (XML de diagrams.net)
- **Backend:** sin cambios.
- **Frontend:** sin cambios.

Un solo diagrama, cinco recorridos:

1. Consultar el dinámico — `consultar()` / `consultarReporteVentas()` / `reporte_ventas()`.
2. Descargar CSV — otra vez `reporte_ventas()` y `csv_reporte()` dentro del controlador.
3. Guardar el cierre — `guardar_cierre()`: crea el cierre, las líneas y `Bitacora.registrar`.
4. Ver cierres — `listarCierresVentas()` al pasar al modo estático. Lee la copia, no suma `venta`.
5. Descargar PDF — `pdf_cierre()` sobre el cierre ya guardado.

## 3. Decisiones técnicas tomadas

- `:ReporteVentasController` agrupa `ReporteVentasView`, `ReporteVentasCsvView`, `CierresReporteVentasView` y `CierreReporteVentasPdfView`, más los servicios `reporte_ventas`, `guardar_cierre`, `listar_cierres`, `cierre_como_reporte`, `csv_reporte` y `pdf_cierre`.
- `obtenerNombreProducto()` es el join `id_producto__nombre` dentro de la consulta de `DetalleVenta`. No hay un método Python aparte.
- `obtenerNombreUsuario()` es `cierre.id_usuario.nombre_usuario` al armar la respuesta del cierre.
- El GET de un cierre por id existe en la API y la pantalla no lo llama: al elegir un cierre usa la lista que ya bajó. Por eso no hay un sexto recorrido.
- El 5 no toca `:Venta` ni `:Producto`. Esa es la diferencia entre el PDF estático y el CSV dinámico.

## 4. Pendientes o siguientes pasos

- Exportar la hoja a imagen e insertarla en el informe del CU21.
- En diagrams.net, correr una etiqueta si queda encima de una flecha.

## 5. Cómo probar lo implementado

- Abrir `docs/informes/CU21_diagrama_comunicacion.drawio` en diagrams.net, o pegar el `.puml` en el editor de PlantUML.
- Comparar el recorrido 1 con `reporte_ventas` y `consultar()` en `ReportesPage`.
- Comparar el recorrido 3 con `guardar_cierre`.
- Comparar el recorrido 5 con `CierreReporteVentasPdfView`: no debe aparecer `:Venta`.
