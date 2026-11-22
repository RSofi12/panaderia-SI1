# Sesión de Desarrollo: CU22 — Generar reporte de producción

- **Fecha:** 2026-11-22
- **Autor / Integrante:** silvia + Cursor
- **Paquete / Módulo:** `apps.reportes` | `frontend`
- **Casos de Uso abordados:** CU22
- **Ciclo:** Ciclo 4

---

## 1. 🎯 Objetivo de la sesión

Implementar el reporte gerencial de producción (CU22) en el paquete `reportes`,
reutilizando la UI del CU21 (período, KPIs, tabla, columnas, PDF/CSV/Excel) y
agregando la comparativa producción física vs ventas del mismo rango.

---

## 2. 🛠️ Cambios realizados

- **Backend:**
  - `services/reporte_produccion.py`: agregación OLAP de jornadas, unidades, costo y
    comparativa vs `DetalleVenta` del mismo `desde`–`hasta`.
  - `services/exportar_reporte_produccion.py`: CSV UTF-8-sig y PDF con membrete.
  - Endpoints `GET /api/reportes/produccion/`, `/csv/` y `/pdf/` (permiso `generar_reportes`).
  - Serializers CU22; filtro opcional `jornada`.
  - Voz: `MODULOS_DISPONIBLES` incluye CU22; `exportar_produccion` en el análisis.
  - Pruebas en `tests_produccion.py` (12 en verde).
- **Frontend:**
  - `ReporteProduccionView.tsx` calcada del CU21 (día/semana/mes, KPIs, tabla, columnas).
  - Pestaña CU22 en `ReportesPage.tsx` y cableado del asistente de voz.
- **BD:** sin migración nueva (solo lectura de `produccion`, `detalle_produccion`, `venta`).

---

## 3. 🧠 Decisiones técnicas tomadas

- El filtro extra equivalente a método de pago del CU21 es **jornada**.
- Las ventas se cruzan por producto en el mismo rango de fechas; no se filtran por
  turno porque `Venta` no tiene jornada.
- No se hace `select_related` del modelo `Producto` completo: en PostgreSQL local
  puede faltar la columna `detalle`. Se leen solo `id_producto` y `nombre`.

---

## 4. ⚠️ Pendientes o siguientes pasos

- CU22 vacío en la captura (Mes noviembre + Solo mañana) era **falta de jornadas**, no un bug de API: había 266 unidades vendidas y 0 lotes de horno en noviembre.
- Se aplicó la migración pendiente `productos.0003_producto_detalle` (la columna `detalle` no existía en PostgreSQL).
- `seed_noviembre_demo --solo-produccion` ahora crea jornadas Mañana del 1 al 22 de noviembre si faltan, sin duplicar ventas. Quedaron 22 lotes y 5728 unidades producidas.

---

## 5. 🧪 Cómo probar lo implementado

1. Login como Propietario (`csantiago`) → **Reportes**.
2. Pestaña **CU22: Reporte de Producción**.
3. Período **Mes = noviembre 2026** y jornada **Solo mañana** (o **Todas**) → **Actualizar Reporte**.
   Alternativa: **Mes = septiembre 2026** (ahí estaban las 3 jornadas históricas del `seed_historial_demo`).
4. Deben verse KPIs (unidades, jornadas, vendidas, costo), tabla de lotes y
   **Ver productos** (producidas vs vendidas).
5. Descargar CSV / Excel / PDF.
6. Backend: `docker compose exec backend python manage.py test apps.reportes.tests_produccion`
