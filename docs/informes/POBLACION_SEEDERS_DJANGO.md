# Población de datos — Django (`manage.py seed_*`)

Panadería Santiago (SI-1) usa **dos referencias** de datos de ejemplo:

| Referencia | Alcance | Uso recomendado |
|---|---|---|
| [`Poblacion_4_Dias_Panaderia_Santiago.sql`](Poblacion_4_Dias_Panaderia_Santiago.sql) | **4 jornadas** (2026-09-06 … 09), 12 productos en el SQL, compras del 05-sep | Informe académico, prueba de escritorio, cargar con DDL+SQL en PostgreSQL puro |
| Comandos Django + **`seed_all`** | Catálogo **ampliado** (36 productos, 5 categorías, 9 proveedores, 20 materias primas, recetas BOM para las 36 variedades) + demos + **mes operativo octubre 2026** | Desarrollo local, Railway (`build.sh`), pruebas de reportes y demo integral |

## Comando maestro

```bash
# Docker
docker compose exec backend python manage.py seed_all

# Local (venv en backend/)
python manage.py seed_all
```

Railway/producción: `backend/build.sh` ejecuta migraciones y luego `seed_all` (ver `backend/config/urls.py` si aplica auto-seed en arranque).

## Orden de los 12 seeders (`seed_all.py`)

| Paso | Comando | Qué puebla | Rango de fechas (operación) |
|:---:|:---:|---|---|
| 1 | `seed_usuarios` | Roles, permisos, 6 usuarios demo | — |
| 2 | `seed_materias_primas` | 20 insumos + inventario inicial | Registro catálogo: 2026-08-01 |
| 3 | `seed_productos` | 5 categorías, 36 productos | 2026-08-01 |
| 4 | `seed_recetas` | BOM/MRP para las 36 variedades | — |
| 5 | `seed_proveedores` | 9 proveedores | 2026-07-15 |
| 6 | `seed_compras` | Compras iniciales (escenario 4 días) | 2026-09-05 |
| 7 | `seed_existencias` | Stock inicial de pan terminado | — |
| 8 | `seed_historial_demo` | 4 jornadas producción + mermas demo | **2026-09-06 … 09** |
| 9 | `seed_pedidos_demo` | Clientes y pedidos (escenario 4 días) | Sep 2026 (del SQL) |
| 10 | `seed_gastos_demo` | Gastos/inversiones (escenario 4 días) | 2026-09-06 … 08 |
| 11 | `seed_ventas_demo` | Tickets dispersos para CU21 | 2026-09-02 … 2026-11-18 |
| 12 | `seed_mes_operativo` | Mes completo: ventas, producción, compras, pedidos, gastos, mermas | **2026-10-01 … 2026-10-31** (lun–sáb) |

## Rangos útiles para reportes y pruebas

- **Escenario corto (informe):** `2026-09-06` → `2026-09-09`
- **Volumen alto (Raysa / `seed_mes_operativo`):** `2026-10-01` → `2026-10-31`
- **Mezcla si corriste `seed_all` completo:** datos desde fines de agosto (catálogo) hasta noviembre (`seed_ventas_demo`); el bloque principal operativo adicional está en **octubre 2026**.

## Idempotencia

- La mayoría de seeders de catálogo usan `get_or_create` / `update_or_create`.
- `seed_mes_operativo` se omite si ya existen ventas de octubre 2026 con prefijo `pi_mes_oct_`.
- Varios demos (historial, pedidos, ventas demo) omiten o abortan si ya hay registros.

## Trazabilidad

- Expansión catálogo + mes operativo: commits de Raysa Sofía Rodríguez (`RSofi12`, nov 2026), bitácora `docs/ai/sessions/2026-11-14-antigravity-poblacion-1-mes-operativo.md`.
- Adaptación seeders al SQL de 4 días: `docs/ai/sessions/2026-11-05-antigravity-seeder-maestro-poblacion-4-dias-2.md`.