# Sesión de Desarrollo: CU18 Atributos de Mermas (motivo y observaciones) y Población Realista (Agosto a Noviembre 2026)

- **Fecha:** 2026-11-24
- **Autor / Integrante:** Antigravity (AI Assistant) & Equipo Panadería Santiago
- **Paquete / Módulo:** `apps.productos_inventario` (productos terminados), `apps.comercializacion` (ventas/seeders), `apps.reportes` (CU22, CU25, Asistente IA/Voz) y `frontend`
- **Casos de Uso abordados:** CU18 (Registrar baja de productos terminados / mermas), CU22 (Reporte dinámico de producción), CU25 (Reporte de resultados económicos), Asistente IA / Voz
- **Ciclo:** Ciclo 2, Ciclo 3 y Ciclo 4

---

## 1. 🎯 Objetivo de la sesión
1. Incorporar formalmente los atributos `motivo` y `observaciones` en el modelo y tabla `nota_perdida_producto` (CU18) para tipificar la merma de panadería (ej. pan sobrante al cierre vs. panes defectuosos de horneado) en lugar de perderlos en texto plano de bitácora.
2. Reflejar las mermas y su impacto en los reportes:
   - **CU22 (Producción):** Comparar unidades horneadas vs. vendidas vs. mermadas.
   - **CU25 (Resultados Económicos):** Deducir mermas valorizadas como costo directo en el estado de resultados.
   - **Asistente IA / Reporte de Voz:** Enriquecer el contexto semántico entregado a Gemini y el análisis local para responder consultas por voz sobre panes sobrantes y pérdidas.
3. Ajustar los seeders operativos (`seed_mes_operativo.py` y `seed_noviembre_demo.py`) con una distribución diaria coherente de mermas (1.5% a 2.5% de la producción diaria) para Julio, Agosto, Septiembre, Octubre y Noviembre 2026, evitando errores de clave foránea protegida en redeploy con Render.

---

## 2. 🛠️ Cambios realizados

### Backend:
- **`apps.productos_inventario.productos_terminados.models` (`NotaPerdidaProducto`):**
  - Añadido campo `motivo`: `CharField(max_length=100, default='Sobrante de mostrador al cierre')`.
  - Añadido campo `observaciones`: `CharField(max_length=255, blank=True, default='')`.
- **Migración creada:** `backend/apps/productos_inventario/productos_terminados/migrations/0004_notaperdidaproducto_motivo_observaciones.py`.
- **`apps.productos_inventario.productos_terminados.services.registrar_baja`:**
  - Persistencia directa de `motivo` y `observaciones` al instanciar `NotaPerdidaProducto`.
- **`apps.productos_inventario.productos_terminados.serializers`:**
  - `NotaPerdidaProductoSerializer` expone `motivo` y `observaciones` en las respuestas JSON.
- **`apps.reportes.services.reporte_produccion`:**
  - Agregación de `NotaPerdidaProducto` por producto y totales en el período (`unidades_mermadas`, `costo_mermas`, desglose por fila de producto).
- **`apps.reportes.services.analisis_ia` & `interprete_voz`:**
  - Implementada función `_contexto_economico` para enlazar consultas económicas a `reporte_resultados_economicos`.
  - Inyectadas métricas de mermas en `_contexto_produccion` y `_analisis_local`.
  - Añadidas intenciones por voz para `'sobrante'`, `'perdida'`, `'pérdida'`.
- **Seeders:**
  - `seed_mes_operativo.py`: Limpieza en orden estricto de dependencias (`MovimientoProductoTerminado` -> `NotaPerdidaProducto` -> `DetalleProduccion` -> `Produccion`) para evitar `ProtectedError`. Generación diaria de mermas por sobrante de mostrador (18:15 hrs) y defectos de horneado cada 2 días (08:30 hrs).
  - `seed_noviembre_demo.py`: Población coherente de mermas diarias de noviembre con motivos y observaciones.
- **Exportación PDF/CSV (`exportar_reporte_produccion.py`):**
  - Añadida tarjeta KPI `Mermas (CU18)` en la cabecera del PDF formal.
  - Añadida columna `Mermas` en la tabla de Producción vs Ventas por Producto.
  - Incorporada nueva sección tabular `Detalle de mermas y pérdidas de producto (CU18)` con fecha, producto, cantidad, motivo, costo total y responsable.
  - Sincronizado el archivo CSV para incluir el resumen y detalle completo de mermas.

### Frontend:
- **`src/types/existencias.ts` & `src/types/reporteProduccion.ts`:**
  - Actualizadas interfaces con `motivo`, `observaciones`, `unidades_mermadas`, `costo_mermas` y entidad `MermaProduccion`.
- **`ReporteProduccionView.tsx`:**
  - Añadida tarjeta KPI `Mermas (CU18)` y columna `Mermas` en la tabla de productos producidos vs vendidos.
- **`src/apps/dashboard/productos/existencias/components/HistorialMermasModal.tsx`:**
  - Visualización del `motivo` y `observaciones` en cada fila del historial de mermas.

---

## 3. 🧠 Decisiones técnicas tomadas
- **Valorización de Mermas a Costo de Producción:** Las mermas no se valorizan al precio de venta al público (PVP) sino al costo de producción unitario (`costo_produccion` o costo del lote de horneado), garantizando un estado de resultados contablemente exacto en CU25.
- **Valores por defecto en el modelo:** Al asignar defaults para `motivo` y `observaciones`, no se requiere reescribir tests anteriores ni se quiebra la compatibilidad con registros existentes en PostgreSQL.

---

## 4. ⚠️ Pendientes o siguientes pasos
- Al desplegar en Render (`bakery2` / `prueba`), el build ejecutará automáticamente las migraciones (`migrate`) y el seeder maestro (`seed_all`) aplicará las poblaciones sin errores de llaves protegidas.

---

## 5. 🧪 Cómo probar lo implementado
```bash
# 1. Ejecutar pruebas unitarias de productos terminados (16 tests)
python manage.py test apps.productos_inventario.productos_terminados

# 2. Ejecutar pruebas de resultados económicos (5 tests)
python manage.py test apps.reportes.tests.PruebasReporteResultadosEconomicos

# 3. Consultar mermas vía API
GET /api/productos-terminados/mermas/
```
