# Sesión de Desarrollo: Botón de descarga en Producción diaria

- **Fecha:** 2026-11-02
- **Autor / Integrante:** agente
- **Paquete / Módulo:** `apps.productos_inventario` | `frontend`
- **Casos de Uso abordados:** CU10, CU11
- **Ciclo:** Ciclo 2

---

## 1. Objetivo de la sesión

Agregar en Producción diaria un botón Descargar (PDF y CSV) que use la jornada y el rango de fechas ya presentes en esa pantalla. No es un caso de uso nuevo: es una salida del historial de CU11.

## 2. Cambios realizados

- **Backend:**
  - `consulta.py`: una sola lectura de `fecha_desde`, `fecha_hasta`, `jornada` e `id_producto`, compartida por el listado y la descarga.
  - `exportar_produccion.py`: arma las tres cifras de las tarjetas y las filas de la tabla, en CSV (punto y coma) y PDF.
  - `GET /api/produccion/csv/` y `GET /api/produccion/pdf/`, con el mismo permiso de consulta del historial.
- **Frontend:**
  - Botón Descargar en la barra de filtros de `ProduccionTab`, con menú Formato PDF / Formato CSV.
  - El servicio manda los mismos parámetros que el listado, incluida la traducción de jornada (`manana` → `Mañana`).

## 3. Decisiones técnicas tomadas

- El archivo se vuelve a calcular al descargarlo. No se guarda un cierre.
- El botón queda junto a Actualizar y repite en el menú el filtro activo, para que se vea qué corte se va a bajar.
- El icono es decorativo; el nombre accesible es el texto "Descargar". Objetivo táctil de 44px y anillo de foco visible.
- El exportador no se metió en `services.py` porque ese archivo ya es el módulo de registro de producción.

## 4. Pendientes o siguientes pasos

- Probar en el navegador con la sesión de Carlos o del panadero: filtrar una jornada y confirmar que el CSV solo trae esas filas.

## 5. Cómo probar lo implementado

1. Entrar a Productos e Inventario → Producción diaria.
2. Elegir jornada y fechas. Abrir Descargar y leer la línea "Este archivo usa: …".
3. Bajar CSV y PDF. Las tres cifras y las filas deben coincidir con las tarjetas y la tabla.
4. Pruebas: `py -3 manage.py test apps.productos_inventario.produccion.tests.PruebasBaseProduccion.test_descarga_csv_respeta_jornada_y_fechas` con `DB_ENGINE=django.db.backends.sqlite3`.

---

## 6. Mismo botón en el historial (CU11)

El historial aplica fecha, jornada y producto solo al pulsar **Aplicar filtros**. El botón Descargar de `HistorialProduccionPage` recibe `filtrosAplicados`, no lo que está escrito en el formulario si todavía no se aplicó. Así el archivo coincide con las tarjetas y la tabla.

El menú nombra también el producto. El CSV y el PDF agregan la fila o la línea `producto`. Si no hay producto elegido, dicen `todas`.

## 7. Membrete del PDF

Los dos PDF del sistema (producción diaria y cierre de ventas) comparten `apps/comun/pdf_reporte.py`. El logo es el sello circular, copiado a `backend/apps/comun/assets/` porque el contenedor del backend no ve `frontend/`.

El título va en naranja `#C2410C` (se lee sobre blanco con contraste suficiente). El resto usa el marrón del sello `#92400E` y la crema `#FEF3C7`: franja superior, tres o cuatro tarjetas, tabla con encabezado marrón y filas alternas. En la página siguiente se repite el título y el encabezado de la tabla, sin volver a dibujar el logo grande.

El título de producción es «Reporte de producción diaria». El del cierre es «Reporte de cierre de ventas». El CSV no cambia. Las cifras siguen saliendo del mismo filtro de la pantalla.

## 8. CSV legible

El CSV sigue siendo texto, sin logo ni colores. `apps/comun/csv_reporte.py` lo ordena como el reporte: nombre de la panadería, título, filtro, bloque Resumen y tabla con encabezados en español. Las fechas van en día/mes/año y los montos usan coma decimal para que Excel en español los tome como números. Producción y ventas comparten ese formato. El PDF no cambia.
