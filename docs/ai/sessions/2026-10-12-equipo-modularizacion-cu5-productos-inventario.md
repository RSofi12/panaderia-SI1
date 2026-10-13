# Sesión de Desarrollo: Modularización del CU5 e Insumos en Sub-apps de `productos_inventario`

- **Fecha:** 2026-10-12
- **Autor / Integrante:** Equipo Panadería Santiago (Pair Programming con Asistente IA)
- **Paquete / Módulo:** `apps.productos_inventario` -> `apps.productos_inventario.productos` & `apps.productos_inventario.materia_prima`
- **Casos de Uso abordados:** CU05 (Gestionar productos), soporte de CU07 (Catálogo compras), base de CU08 / CU09 (Stock y alertas de insumos)
- **Ciclo:** Ciclo 1 & Ciclo 2

---

## 1. 🎯 Objetivo de la sesión
Reorganizar la arquitectura del paquete `backend/apps/productos_inventario/` para desacoplar el caso de uso **CU05 (Gestionar productos)** en una sub-app dedicada denominada `productos`, y el catálogo e inventario de insumos en una sub-app dedicada `materia_prima`. Esto consolida el patrón de arquitectura limpia por sub-apps en todos los módulos del backend (`usuarios_seguridad`, `compras` y ahora `productos_inventario`).

Se preservó estrictamente toda la lógica del equipo (cálculo automático de precio sugerido, histórico de precios de productos, filtros de categorías, toggle de activo y registro en bitácora), asegurando la integridad física en PostgreSQL mediante migraciones con `SeparateDatabaseAndState`.

---

## 2. 🛠️ Cambios realizados

### Backend
1. **Creación de la sub-app `apps.productos_inventario.productos` (CU05):**
   - `apps.py`: Define `name = 'apps.productos_inventario.productos'` con label `productos`.
   - `models.py`: Clases `CategoriaProducto` (`db_table = 'categoria_producto'`), `Producto` (`db_table = 'producto'`) con método `calcular_precio_sugerido()`, y `HistorialPrecioProducto` (`db_table = 'historial_precio_producto'`).
   - `permissions.py`: Clase de permiso `PuedeGestionarProductos` (RBAC con permiso `gestionar_productos`).
   - `serializers.py`: `CategoriaProductoSerializer` y `ProductoSerializer` con validaciones de costo, porcentaje de ganancia y precio de venta.
   - `views.py`: Vistas `CategoriaProductoListView`, `ProductoListCreateView`, `ProductoDetailView` y `ProductoToggleActivoView` con trazabilidad completa en `Bitacora`.
   - `urls.py`: Rutas `categorias-producto/`, `productos/`, `productos/<int:pk>/`, `productos/<int:pk>/toggle-activo/`.
   - `admin.py`: `CategoriaProductoAdmin`, `ProductoAdmin`, `HistorialPrecioProductoAdmin`.
   - `management/commands/seed_productos.py`: Seeder idempotente de categorías y catálogo de panes.
   - `tests.py`: Suite de 3 pruebas unitarias (listado con filtros, creación con cálculo de precio sugerido y bitácora, y toggle activo).

2. **Creación de la sub-app `apps.productos_inventario.materia_prima` (Insumos / Inventario):**
   - `apps.py`: Define `name = 'apps.productos_inventario.materia_prima'` con label `materia_prima`.
   - `models.py`: Clases `MateriaPrima`, `InventarioMateriaPrima`, `HistorialPrecioMateriaPrima`, `MovimientoMateriaPrima` (con FK a `'compra_materia_prima.Compra'`).
   - `serializers.py`: `MateriaPrimaSerializer` con cálculo de stock actual y precio de última compra.
   - `views.py`: `MateriaPrimaListView` (GET `/api/materias-primas/`).
   - `urls.py`: Ruta `materias-primas/`.
   - `admin.py`: Registro de insumos, stock, precios y movimientos.
   - `management/commands/seed_materias_primas.py`: Seeder de insumos base con inventario inicial.
   - `tests.py`: Prueba de consulta de catálogo de materias primas con stock y precios.

3. **Creación de la sub-app `apps.productos_inventario.produccion` (CU10, CU11):**
   - `apps.py`: Define `name = 'apps.productos_inventario.produccion'` con label `produccion`.
   - `models.py`: Estructura ORM base de elaboración de pan:
     - `Produccion` (CU10, CU11): Cabecera de jornada/lote con fecha, jornada y responsable.
     - `DetalleProduccion` (CU10, CU11): Cantidad de pan producido y costo unitario.
   - `admin.py`, `serializers.py`, `views.py`, `urls.py`: Scaffolding base limpio para `/api/produccion/`.

4. **Creación de la sub-app `apps.productos_inventario.productos_terminados` (CU12, CU18):**
   - `apps.py`: Define `name = 'apps.productos_inventario.productos_terminados'` con label `productos_terminados`.
   - `models.py`: Estructura ORM de existencias y mermas:
     - `InventarioProductoTerminado` (CU12): Existencias de pan terminado listo para venta.
     - `MovimientoProductoTerminado`: Kardex de entradas (producción) y salidas (ventas, mermas).
     - `NotaPerdidaProducto` (CU18): Registro de mermas de pan no vendido.
   - `admin.py`, `serializers.py`, `views.py`, `urls.py`: Scaffolding base limpio para `/api/productos-terminados/existencias/` y `/api/productos-terminados/mermas/`.

5. **Ampliación de alcance de CU08: «Gestionar materia prima» (CRUD + Inventario):**
   - Se resolvió el vacío funcional del MRP donde ningún caso de uso creaba ni editaba insumos.
   - CU08 pasa de ser solo «Consultar stock de materia prima» a **«Gestionar materia prima»** (alta, edición de nombre/unidad/stock mínimo, baja lógica e inventario actual), permitiendo configurar el `stock_minimo` del cual depende la alerta de **CU09**.
   - Se mantiene la matriz de 26 Casos de Uso del PUDS sin alterar la planificación ni crear un CU27 artificial.
   - Se articuló la receta (`producto_materia_prima`) entre CU05 y CU10 en el Ciclo 2.

6. **Integración con otros módulos:**
   - `config/settings.py`: Registradas `'apps.productos_inventario.productos'`, `'apps.productos_inventario.materia_prima'`, `'apps.productos_inventario.produccion'` y `'apps.productos_inventario.productos_terminados'` en `INSTALLED_APPS`.
   - `apps.compras.compra_materia_prima`:
     - `models.py`: `DetalleCompra.id_materia_prima` actualizado a `'materia_prima.MateriaPrima'`.
     - `services/registrar_compra.py`: Imports actualizados a `apps.productos_inventario.materia_prima.models`.
     - `management/commands/seed_compras.py`: Import actualizado a `apps.productos_inventario.materia_prima.models`.
     - `tests.py`: Imports actualizados a `apps.productos_inventario.materia_prima.models`.

6. **Depuración de la raíz `apps.productos_inventario`:**
   - Se eliminaron todos los archivos sueltos y redundantes de la raíz (`models.py`, `views.py`, `serializers.py`, `permissions.py`, `admin.py`, `tests.py`, `management/`).
   - `urls.py`: Actúa como router paraguas que incluye las rutas de `productos`, `materia_prima` y `produccion` sin modificar las URLs públicas de la API.

7. **Migraciones con preservación física de datos:**
   - `productos/migrations/0001_initial.py`: Registra modelos en estado de Django usando `SeparateDatabaseAndState` con `database_operations=[]`.
   - `materia_prima/migrations/0001_initial.py`: Registra modelos de insumos en estado de Django usando `SeparateDatabaseAndState`.
   - `compra_materia_prima/migrations/0003_alter_detallecompra_id_materia_prima.py`: Actualiza la relación FK en estado de Django usando `SeparateDatabaseAndState`.
   - `productos_inventario/migrations/0007_remove_producto_id_categoria_and_more.py`: Desvincula los modelos del estado de la app raíz usando `SeparateDatabaseAndState` sin emitir `DROP TABLE`.

8. **Sincronización del Diagrama de Clases PlantUML (`database_panaderia_con_funciones.puml`):**
   - Se actualizó el diagrama de clases para que refleje con total fidelidad el DDL físico de PostgreSQL (`Database_Panaderia_Santiago.sql`).
   - Se incorporaron las entidades de seguridad avanzada: `ConfiguracionSeguridad` (singleton CU1, CU2) y `TokenRecuperacion` (CU2), con sus atributos de bloqueo, expiración y SHA-256.
   - Se formalizó la entidad asociativa `RolPermiso` y el atributo `modulo` en `Permiso`.
   - Se completaron los atributos de `Usuario` (`email`, `isStaff`, `isSuperuser`, `intentosFallidos`, `bloqueadoHasta`, etc.) y métodos de desbloqueo/recuperación.
   - Se añadió la entidad `NotaPerdidaProducto` (CU18 - mermas de panadería) con relaciones a `DetalleProduccion`, `Usuario` y `MovimientoProductoTerminado`.
   - Se ajustaron las multiplicidades de movimientos (de 0..1 a 0..*) para compras, producción y mermas.

---


## 3. 🧠 Decisiones técnicas tomadas
- **Incolumidad de la Base de Datos:** Cero pérdida de datos. Las tablas físicas `categoria_producto`, `producto`, `historial_precio_producto`, `materia_prima`, `inventario_materia_prima`, `historial_precio_materia_prima` y `movimiento_materia_prima` permanecen intactas en PostgreSQL.
- **Transparencia en el Frontend:** Las rutas `/api/productos/`, `/api/categorias-producto/` y `/api/materias-primas/` conservan exactamente los mismos contratos JSON y nombres de endpoints.
- **Consistencia Arquitectónica:** Todos los paquetes del proyecto (`usuarios_seguridad`, `compras`, `productos_inventario`) siguen exactamente el mismo estándar de sub-apps.

---

## 4. 🧪 Pruebas y verificación
```powershell
# 1. Django check
.\venv\Scripts\python.exe manage.py check
# Resultado: System check identified no issues (0 silenced).

# 2. Migraciones
.\venv\Scripts\python.exe manage.py migrate
# Resultado:
#   Applying materia_prima.0001_initial... OK
#   Applying compra_materia_prima.0003_alter_detallecompra_id_materia_prima... OK
#   Applying productos.0001_initial... OK
#   Applying productos_inventario.0007_remove_producto_id_categoria_and_more... OK

# 3. Suite completa de tests unitarios (15 pruebas en total)
.\venv\Scripts\python.exe manage.py test apps.productos_inventario.productos.tests apps.productos_inventario.materia_prima.tests apps.compras.proveedores.tests apps.compras.compra_materia_prima.tests
# Resultado: Ran 15 tests in 4.914s — OK

# 4. Seeders
.\venv\Scripts\python.exe manage.py seed_productos
.\venv\Scripts\python.exe manage.py seed_materias_primas
.\venv\Scripts\python.exe manage.py seed_compras
# Resultado: Todos ejecutados con éxito.
```
