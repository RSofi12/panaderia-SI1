# Sesión: Implementación Backend CU10 — Registrar Producción Diaria

- **Fecha:** 2026-10-13
- **Ciclo:** Ciclo 2
- **Caso de Uso:** **CU10 — Registrar producción diaria** (`apps.productos_inventario.produccion`)
- **Estado:** 🟢 Backend completado y probado al 100% (16/16 tests específicos en verde, 45/45 en módulo global).

---

## 🎯 1. Objetivos de la Sesión
1. Modelar la receta / explosión de materiales (BOM) en base a la tabla `producto_materia_prima` del DDL.
2. Incorporar la clave foránea `id_produccion` en `MovimientoMateriaPrima` para trazabilidad de salidas de insumos por producción.
3. Desarrollar la capa de servicios transaccionales en `backend/apps/productos_inventario/produccion/services.py` con:
   - Bloqueo pesimista mediante `select_for_update()`.
   - Validación atómica de suficiencia de materias primas.
   - Cálculo dinámico de costo unitario a partir de insumos y precios históricos de compra.
   - Descuento automático de materia prima (`MovimientoMateriaPrima` salida).
   - Incremento automático de pan terminado en mostrador (`MovimientoProductoTerminado` entrada).
   - Auditoría en `Bitacora` (CU26).
4. Exponer endpoints en `/api/produccion/`: `POST /` (registro), `POST /simular/` (balance en vivo) y `GET /recetas/`.
5. Crear el comando de seeder `seed_recetas` para las 12 recetas oficiales de `Poblacion_4_Dias_Panaderia_Santiago.sql`.
6. Diseñar y ejecutar suite exhaustiva de 16 pruebas automatizadas.

---

## 🛠️ 2. Archivos Creados o Modificados

### Backend
1. `backend/apps/productos_inventario/productos/models.py`:
   - Modelo `ProductoMateriaPrima` (`db_table = 'producto_materia_prima'`) con constraint única `(id_producto, id_materia_prima)`.
2. `backend/apps/productos_inventario/materia_prima/models.py`:
   - FK diferida `id_produccion` en `MovimientoMateriaPrima`.
3. `backend/apps/usuarios_seguridad/bitacora/models.py`:
   - Acción `REGISTRO_PRODUCCION` en `AccionBitacora`.
4. `backend/apps/productos_inventario/produccion/models.py`:
   - Adición del choice `UNICA = 'unica', 'Jornada Única'` a `JornadaProduccion`.
5. `backend/apps/productos_inventario/produccion/permissions.py`:
   - Clase RBAC `PuedeRegistrarProduccion` para Personal de Producción, Administrador, Propietario y superusuarios.
6. `backend/apps/productos_inventario/produccion/services.py` (Nuevo):
   - `simular_consumo_produccion`: Cálculo y balance reactivo de existencias.
   - `calcular_costo_unitario_producto`: Sumatoria de insumos por precio histórico.
   - `registrar_produccion_diaria`: Transacción atómica integral.
7. `backend/apps/productos_inventario/produccion/serializers.py`:
   - `RegistrarProduccionInputSerializer`, `SimularConsumoInputSerializer`, `RecetaProductoSerializer` y consumos en `ProduccionSerializer`.
8. `backend/apps/productos_inventario/produccion/views.py`:
   - `ProduccionListView` (POST para CU10 y GET para CU11), `ProduccionSimularView` y `RecetasListView`.
9. `backend/apps/productos_inventario/produccion/urls.py` & `productos/urls.py`:
   - Rutas `/api/produccion/`, `/api/produccion/simular/` y `/api/produccion/recetas/`.
10. `backend/apps/productos_inventario/produccion/management/commands/seed_recetas.py` (Nuevo):
    - Seeder para los 12 tipos de pan y 37 relaciones de ingredientes de `Poblacion_4_Dias_Panaderia_Santiago.sql`.
11. `backend/apps/productos_inventario/produccion/tests.py`:
    - 16 pruebas unitarias y de integración que cubren camino feliz, falta de stock, atomicidad de rollback, permisos y seeder.

---

## 🧪 3. Verificaciones de Calidad

- **Pruebas de la sub-app `produccion`:**
  `python manage.py test apps.productos_inventario.produccion.tests`
  -> **16/16 tests OK (2.9s)**
- **Pruebas de todo el módulo `productos_inventario`:**
  `python manage.py test apps.productos_inventario`
  -> **45/45 tests OK (4.6s)**
- **Django Check:**
  `python manage.py check`
  -> **0 issues identificados**
