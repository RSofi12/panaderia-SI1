# Sesión de Desarrollo: Modularización del Paquete Compras en Sub-apps (`proveedores` y `compra_materia_prima`)

- **Fecha:** 2026-10-11
- **Autor / Integrante:** Equipo Panadería Santiago (Pair Programming con Asistente IA)
- **Paquete / Módulo:** `apps.compras` -> `apps.compras.proveedores` & `apps.compras.compra_materia_prima`
- **Casos de Uso abordados:** CU06 (Gestionar proveedores) & CU07 (Registrar compra de materia prima)
- **Ciclo:** Ciclo 1 (CU06) & Ciclo 2 (CU07)

---

## 1. 🎯 Objetivo de la sesión
Reorganizar la arquitectura del paquete `backend/apps/compras/` para desacoplar sus casos de uso en dos sub-apps dedicadas:
1. **`proveedores` (CU06):** Catálogo de proveedores con validaciones y bajas lógicas.
2. **`compra_materia_prima` (CU07):** Registro transaccional de compras a proveedores con impacto automático en stock y bitácora.

Siguiendo el estándar arquitectónico modular ya establecido en `apps.usuarios_seguridad`, se mantuvo estrictamente la lógica de negocio construida por el equipo, garantizando la no pérdida de datos en PostgreSQL mediante migraciones con `SeparateDatabaseAndState`.

---

## 2. 🛠️ Cambios realizados

### Sub-app `apps.compras.proveedores` (CU06)
- **`apps.py`:** Define `name = 'apps.compras.proveedores'` con label `proveedores`.
- **`models.py`:** Modelo `Proveedor` trasladado con `db_table = 'proveedor'` y constraint de unicidad `proveedor_nombre_unico_ci` sobre `Lower('nombre')`.
- **`permissions.py`:** Clases de permisos `PuedeGestionarProveedores` y tupla `PERMISOS_LECTURA` (`gestionar_proveedores`, `registrar_compras`).
- **`serializers.py`:** `ProveedorSerializer`, validación y normalización `normalizar_telefono` con regex `TELEFONO_LIMPIO`.
- **`views.py`:** Vistas `ProveedorListCreateView` (listado y alta con bitácora), `ProveedorDetailView` (detalle y actualización con bitácora) y `ProveedorToggleActivoView` (soft-delete / activación con bitácora).
- **`urls.py`:** Enrutamiento modular namespaced (`''`, `'<int:pk>/'`, `'<int:pk>/toggle-activo/'`).
- **`admin.py`:** Registro en Django Admin con `ProveedorAdmin`.
- **`management/commands/seed_proveedores.py`:** Seeder idempotente de proveedores trasladado y apuntando a los modelos de la sub-app.
- **`tests.py`:** Suite de 5 pruebas unitarias (`PruebasGestionProveedores`) que verifican creación, unicidad insensible a mayúsculas, normalización de teléfono, soft-delete y registro en bitácora.

### Sub-app `apps.compras.compra_materia_prima` (CU07)
- **`apps.py`:** Configura `name = 'apps.compras.compra_materia_prima'` con label `compra_materia_prima`.
- **`models.py`:** Clases `Compra` y `DetalleCompra` preservando tablas físicas `db_table = 'compra'` y `db_table = 'detalle_compra'`. Llave foránea `Compra.id_proveedor` vinculada a `'proveedores.Proveedor'` y `DetalleCompra.id_materia_prima` a `'materia_prima.MateriaPrima'`.
- **`permissions.py`:** Clase `PuedeRegistrarCompras` exigiendo el permiso `registrar_compras`.
- **`services/registrar_compra.py`:** Lógica transaccional de alta de compra con `transaction.atomic()`, bloqueo de concurrencia `select_for_update()`, incremento en `stock_actual` de `InventarioMateriaPrima`, registro en `HistorialPrecioMateriaPrima`, movimientos `MovimientoMateriaPrima` (tipo `ENTRADA`) y traza en `Bitacora`.
- **`serializers.py`:** Serializadores de entrada (`CompraDetalleEntradaSerializer`, `CompraRegistroSerializer`) y salida (`CompraDetalleLecturaSerializer`, `CompraSerializer`, `CompraListSerializer`).
- **`views.py`:** Vistas controladoras `CompraListCreateView` (`GET`/`POST`) y `CompraDetailView` (`GET`).
- **`urls.py`:** Rutas `/` y `/<int:pk>/` dentro del namespace de la sub-app.
- **`admin.py`:** Registro en Django Admin con `CompraAdmin` y `DetalleCompraInline`.
- **`management/commands/seed_compras.py`:** Seeder de compras trasladado y apuntando a los modelos de la sub-app.
- **`tests.py`:** Suite de 6 pruebas unitarias (`PruebasRegistroCompra`, `PruebasAccesoCompra`, `PruebasDatosInvalidos`).

### Depuración y limpieza de la raíz `apps.compras`
- Se eliminaron todos los archivos sueltos y carpetas redundantes de la raíz de `compras`: `models.py`, `views.py`, `tests.py`, `admin.py`, `serializers.py`, `permissions.py`, `services/` y `management/`.
- `urls.py`: Actúa como router paraguas que incluye las rutas de `/api/proveedores/` y `/api/compras/` manteniendo intactos los contratos públicos de la API.
- `config/settings.py`: Registradas `'apps.compras.proveedores'` y `'apps.compras.compra_materia_prima'` en `INSTALLED_APPS`.

### Migraciones con preservación física (`SeparateDatabaseAndState`)
- `proveedores/migrations/0001_initial.py`: Registra `Proveedor` en el estado de Django con `SeparateDatabaseAndState`.
- `compra_materia_prima/migrations/0001_initial.py`: Registra `Compra` y `DetalleCompra` en el estado de Django con `SeparateDatabaseAndState`.
- `compra_materia_prima/migrations/0002_alter_compra_id_proveedor.py`: Actualiza la FK apuntando a `proveedores.proveedor`.
- `compras/migrations/0003_remove_detallecompra_id_compra_and_more.py`: Desvincula los modelos del estado de `compras` sin ejecutar `DROP TABLE`.
- `compras/migrations/0004_delete_proveedor.py`: Desvincula `Proveedor` del estado del paquete `compras` sin ejecutar `DROP TABLE`.

---

## 3. 🧠 Decisiones técnicas tomadas
- **Incolumidad de la Base de Datos:** Cero operaciones destructivas de DDL en PostgreSQL. Los datos existentes de proveedores y compras permanecen intactos.
- **Transparencia en el Frontend:** Las rutas `/api/proveedores/` y `/api/compras/` no cambiaron su estructura ni sus respuestas JSON.
- **Consistencia Modular:** El paquete `apps/compras/` queda simétrico y desacoplado, preparado para recibir `gastos` (CU20) en el Ciclo 4.

---

## 4. 🧪 Pruebas y verificación
```powershell
# 1. Django check
.\venv\Scripts\python.exe manage.py check
# Resultado: System check identified no issues (0 silenced).

# 2. Migraciones
.\venv\Scripts\python.exe manage.py migrate
# Resultado: Migraciones de proveedores y compra_materia_prima aplicadas con OK.

# 3. Suite completa de tests de compras (11 pruebas)
.\venv\Scripts\python.exe manage.py test apps.compras.proveedores.tests apps.compras.compra_materia_prima.tests
# Resultado: Ran 11 tests in 5.105s — OK (5 tests proveedores + 6 tests compras)

# 4. Seeders
.\venv\Scripts\python.exe manage.py seed_proveedores
.\venv\Scripts\python.exe manage.py seed_compras
# Resultado: Ejecutados con éxito sin duplicados.
```
