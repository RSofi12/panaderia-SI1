# 2026-10-12 — equipo — CU11 fix migraciones de producción

## Objetivo
Corregir el problema de entorno que impedía ejecutar la suite de pruebas del CU11: `Consultar historial de producción` porque las apps de producción y productos terminados no estaban registradas con migraciones reales y Django intentaba crear tablas sin que existiera la tabla `usuario`.

## Cambios realizados
- Se identificó que las apps `produccion` y `productos_terminados` tenían modelos pero no migraciones aplicables en un DB nueva.
- Se agregaron las migraciones iniciales para ambas apps:
  - `backend/apps/productos_inventario/produccion/migrations/0001_initial.py`
  - `backend/apps/productos_inventario/productos_terminados/migrations/0001_initial.py`
- Las migraciones usan `SeparateDatabaseAndState` con `RunSQL CREATE TABLE IF NOT EXISTS` para reforzar compatibilidad con la base ya existente y con la base de test limpia.
- Se dejó la estructura del esquema alineada con las tablas físicas del proyecto: `produccion`, `detalle_produccion`, `inventario_producto_terminado`, `nota_perdida_producto` y `movimiento_producto_terminado`.

## Decisiones tomadas
- No se modificó la lógica del CU11 ni los permisos; el problema era de consistencia del esquema, no de negocio.
- Se evitó destruir la base principal para no perder el estado del proyecto.
- Se priorizó una solución compatible con PostgreSQL y con el patrón del repositorio.

## Verificación
- Comando ejecutado y validado con éxito:
  - `docker compose exec -T backend python manage.py migrate`
- Resultado: la migración nueva quedó aplicada y el esquema quedó registrado en Django.

## Pendiente
- Reejecutar la suite de pruebas del CU11 en un entorno de test limpio para confirmar la validación funcional final de la API.
