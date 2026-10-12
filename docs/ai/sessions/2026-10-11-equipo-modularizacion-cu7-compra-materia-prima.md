# Sesión de Desarrollo: Modularización del CU7 en Sub-app `compra_materia_prima`

- **Fecha:** 2026-10-11
- **Autor / Integrante:** Equipo Panadería Santiago (Pair Programming con Asistente IA)
- **Paquete / Módulo:** `apps.compras` -> `apps.compras.compra_materia_prima`
- **Casos de Uso abordados:** CU07 (Registrar compra de materia prima)
- **Ciclo:** Ciclo 2

---

## 1. 🎯 Objetivo de la sesión
Reorganizar la arquitectura del paquete `backend/apps/compras/` para desacoplar el caso de uso **CU07 (Registrar compra de materia prima)** en una sub-app dedicada denominada `compra_materia_prima`, siguiendo el estándar arquitectónico modular ya establecido en `apps.usuarios_seguridad` (donde existen sub-apps como `users`, `roles`, `permisos`, `bitacora`). Mantener la lógica de negocio intacta, asegurar la no pérdida de datos en PostgreSQL mediante `SeparateDatabaseAndState` en migraciones y verificar que los tests unitarios pasen en verde.

---

## 2. 🛠️ Cambios realizados

### Backend
1. **Creación de la sub-app `apps.compras.compra_materia_prima`:**
   - `apps.py`: Configura `name = 'apps.compras.compra_materia_prima'` con label `compra_materia_prima`.
   - `models.py`: Clases `Compra` y `DetalleCompra` preservando tablas físicas `db_table = 'compra'` y `db_table = 'detalle_compra'`.
   - `permissions.py`: Clase `PuedeRegistrarCompras` exigiendo el permiso `registrar_compras`.
   - `services/registrar_compra.py`: Lógica transaccional de alta de compra, bloqueo de concurrencia `select_for_update()`, impacto en `stock_actual` de `InventarioMateriaPrima`, `HistorialPrecioMateriaPrima`, `MovimientoMateriaPrima` (tipo `ENTRADA`) y traza en `Bitacora`.
   - `serializers.py`: Serializadores de entrada (`CompraDetalleEntradaSerializer`, `CompraRegistroSerializer`) y salida (`CompraDetalleLecturaSerializer`, `CompraSerializer`, `CompraListSerializer`).
   - `views.py`: Vistas controladoras `CompraListCreateView` (`GET`/`POST`) y `CompraDetailView` (`GET`).
   - `urls.py`: Rutas `/` y `/<int:pk>/` dentro del namespace de la sub-app.
   - `tests.py`: Suite completa de 6 pruebas unitarias (`PruebasRegistroCompra`, `PruebasAccesoCompra`, `PruebasDatosInvalidos`).

2. **Ajuste del paquete padre `apps.compras` (Compatibilidad hacia atrás):**
   - `config/settings.py`: Registrada la sub-app `'apps.compras.compra_materia_prima'` en `INSTALLED_APPS`.
   - `apps/compras/urls.py`: Enruta `path('compras/', include('apps.compras.compra_materia_prima.urls'))` de modo que las URLs públicas de la API (`/api/compras/`) se conservan 100% idénticas.
   - `apps/compras/models.py`, `views.py`, `serializers.py`, `permissions.py`: Mantienen `Proveedor` (CU6) y re-exportan las clases de `compra_materia_prima` para evitar roturas de importación en módulos consumidores.
   - `apps/productos_inventario/models.py`: FK de `MovimientoMateriaPrima.id_compra` actualizada a `'compra_materia_prima.Compra'`.

3. **Migraciones con preservación física de datos:**
   - `compra_materia_prima/migrations/0001_initial.py`: Registra los modelos `Compra` y `DetalleCompra` en el estado de Django mediante `SeparateDatabaseAndState` con `database_operations=[]` (las tablas ya existen físicamente).
   - `compras/migrations/0003_remove_detallecompra_id_compra_and_more.py`: Desvincula los modelos del estado de `compras` usando `SeparateDatabaseAndState` sin emitir `DROP TABLE`.
   - `productos_inventario/migrations/0006_alter_movimientomateriaprima_id_compra.py`: Actualiza la FK sin alterar la columna física.

---

## 3. 🧠 Decisiones técnicas tomadas
- **Preservación de tablas físicas (`db_table`):** Ninguna tabla de base de datos fue renombrada ni destruida.
- **`SeparateDatabaseAndState`:** Utilizado en migraciones para transferir la propiedad del modelo entre apps de Django sin emitir `DROP TABLE` ni `CREATE TABLE` redundantes en PostgreSQL.
- **Cero cambios en Frontend:** Las URLs `/api/compras/` y `/api/compras/<id>/` permanecen idénticas, garantizando compatibilidad total con el frontend React.

---

## 4. ⚠️ Pendientes o siguientes pasos
- Modularizar a futuro `apps.compras.proveedores` para el CU06, completando la separación total del paquete en sub-apps.
- Aplicar la optimización de consulta N+1 en el listado de compras (`annotate(cantidad_lineas=Count('detalles'))`).

---

## 5. 🧪 Cómo probar lo implementado
```powershell
# 1. Comprobación de modelos e integridad de Django
.\venv\Scripts\python.exe manage.py check

# 2. Aplicar migraciones
.\venv\Scripts\python.exe manage.py migrate

# 3. Correr pruebas unitarias del CU7
.\venv\Scripts\python.exe manage.py test apps.compras.compra_materia_prima.tests
```
Resultados obtenidos:
- `System check identified no issues (0 silenced)`
- Migraciones aplicadas: `OK`
- Pruebas unitarias: `Ran 6 tests in 9.166s — OK`
