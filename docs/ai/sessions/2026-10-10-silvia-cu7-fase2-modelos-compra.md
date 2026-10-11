# Sesión 2026-10-10 — Silvia — CU7 Fase 2 modelos Compra

## Objetivo
Modelos ORM `Compra` y `DetalleCompra` en `apps/compras` alineados al DDL.

## Cambios
- **Backend:** `backend/apps/compras/models.py` — clases `Compra`, `DetalleCompra` (FK a `Proveedor`, usuario, `MateriaPrima`).

## Decisiones
- `DetalleCompra.id_compra` → `CASCADE` (líneas dependen de la cabecera; en producción no se borran compras).
- Materia prima referenciada con string `'productos_inventario.MateriaPrima'` para evitar imports circulares.

## Cómo probar
```powershell
docker compose exec backend python manage.py makemigrations compras
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py check
```

## Actualización — CU7 Fase 3 Lección 3
- **Backend:** `apps/compras/services/registrar_compra.py` — validaciones, `@transaction.atomic`, creación de `Compra`/`DetalleCompra` y cálculo de total (sin inventario/bitácora aún).
- **Limpieza:** stub retirado de `apps/compras/__init__.py`.

## Actualización — CU7 Fase 3 Lección 4
- **`registrar_compra`:** por cada línea — `select_for_update` en inventario, suma `stock_actual`, nuevo `HistorialPrecioMateriaPrima`, `MovimientoMateriaPrima` tipo `entrada` ligado a la compra; al cierre `Bitacora.registrar` con `ALTA_COMPRA`.

## Actualización — CU7 Fase 4
- **`compras/serializers.py`:** `CompraRegistroSerializer` (POST → `registrar_compra`), `CompraSerializer` / `CompraListSerializer` / `CompraDetalleLecturaSerializer` (lectura).

## Actualización — CU7 Fase 5 y 6
- Vistas `CompraListCreateView` / `CompraDetailView`, permiso `PuedeRegistrarCompras`, rutas `/api/compras/`.
- `apps/compras/tests.py`: 6 pruebas (alta con stock/bitácora, detalle, 401, 403, body vacío, proveedor inactivo). `manage.py test apps.compras.tests` en verde.

## Pendiente
- Fase 7: pantalla React de registrar compra en `/dashboard/compras`.
