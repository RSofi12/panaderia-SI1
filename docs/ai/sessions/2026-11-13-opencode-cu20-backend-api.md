# Sesión de Desarrollo: CU20 — API backend de Gastos e Inversiones

- **Fecha:** 2026-11-13
- **Autor / Integrante:** OpenCode (Agente IA)
- **Paquete / Módulo:** `apps.compras.gastos`
- **Casos de Uso abordados:** CU20 (Registrar gasto / inversión), CU26 (Bitácora)
- **Ciclo:** Ciclo 4

---

## 1. 🎯 Objetivo de la sesión

Implementar el **paso 1 y paso 2** del plan de implementación de CU20 (backend):
serializadores, servicio de negocio, consulta de filtros, permisos RBAC, vistas
y rutas; y aplicar el lote de mejoras aprobado (categoría, anulación lógica,
fecha editable, integridad en base de datos). La pantalla React queda para una
sesión posterior.

Rama de trabajo: `prueba` (rama actual del repositorio).

## 2. 🛠️ Cambios realizados

### 2.1 API inicial (pasos 1 y 2)

- **Backend (`apps.compras.gastos`):**
  - `permissions.py` (nuevo): `PuedeGestionarGastos`, valida el permiso
    `registrar_gastos` del rol autenticado.
  - `serializers.py` (nuevo):
    - `MovimientoEconomicoRegistroSerializer` — entrada del POST: `tipo`,
      `categoria` (opcional), `concepto`, `monto`, `descripcion` opcional,
      `fecha_hora` opcional. No acepta `id_usuario` desde el cliente.
    - `MovimientoEconomicoSerializer` — salida para listado y detalle, con
      `tipo_display`, `categoria_display` y `registrado_por`.
  - `services/registrar_movimiento.py` (nuevo): `registrar_movimiento()` y
    `anular_movimiento()`, ambos con `@transaction.atomic`; validan y registran
    `ALTA_MOVIMIENTO_ECONOMICO` / `ANULACION_MOVIMIENTO_ECONOMICO` en `bitacora`.
  - `consulta.py` (nuevo): `leer_filtros_gasto()` (tipo, categoría, rango de
    fechas, estado de anulación y búsqueda, con validación 400) y
    `gastos_filtrados()` (orden `-fecha_hora`, `-id_movimiento`).
  - `views.py` (nuevo): `GastoListCreateView` (GET listado filtrado / POST
    registro), `GastoDetailView` (GET detalle) y `GastoAnularView` (POST anular).
  - `urls.py` (modificado): `GET|POST /api/gastos/`,
    `GET /api/gastos/<id>/` y `POST /api/gastos/<id>/anular/`.
  - `tests.py` (nuevo): 32 pruebas del CU20.
  - `admin.py`: columnas y filtros de `categoria` y `anulado`.

### 2.2 Lote de mejoras aprobado (modelo y base de datos)

- `models.py`:
  - `CategoriaMovimientoEconomico` (`alquiler`, `servicios`, `mantenimiento`,
    `equipos`, `otros`) y campo `categoria` (por defecto `otros`).
  - Campo `anulado` (boolean, `false`): se anula, no se borra.
  - Se quitó `default=Decimal('0.00')` de `monto`; el monto siempre se exige.
  - `Meta.constraints`: `monto > 0`, `tipo IN ('gasto','inversion')` y
    `categoria IN (...)`. `Meta.indexes`: índice sobre `fecha_hora`.
  - Migración `gastos.0002_categoria_anulado_constraints.py`.
- `docs/informes/Database_Panaderia_Santiago.sql`: se actualizó la tabla
  `movimiento_economico` (columnas `categoria` y `anulado`, los tres `CHECK` y
  el índice `mov_economico_fecha_idx`).
- **Backend (`apps.usuarios_seguridad.bitacora`):**
  - `models.py`: acciones `ALTA_MOVIMIENTO_ECONOMICO` y
    `ANULACION_MOVIMIENTO_ECONOMICO`.
  - Migración `0016_acciones_cu20_gastos.py`. Además de las acciones de CU20,
    **restaura** `EMISION_COMPROBANTE` y `REGISTRO_BAJA_PRODUCTO`, que la
    migración `0015` había eliminado por desincronización.
- **Seeder:** `seed_usuarios.py` usaba `gestionar_gastos` para el permiso 9;
  se alineó a `registrar_gastos`, el nombre documentado en 8 fuentes del repo.

## 3. 🧠 Decisiones técnicas tomadas

- **El responsable no viene del payload:** `id_usuario` se toma de
  `request.user`; así un cliente no puede atribuir un egreso a otro usuario.
  Hay una prueba explícita de que un `id_usuario` enviado se ignora.
- **`fecha_hora` editable pero nunca futura:** se acepta opcional y se valida
  en serializer y servicio. Sirve para registrar hoy un pago hecho ayer; una
  fecha futura se rechaza con 400.
- **Anulación lógica en lugar de borrado:** un egreso real no se elimina. Se
  marca `anulado` con `select_for_update`, para que dos anulaciones simultáneas
  no dupliquen la bitácora. Doble anulación → 400. El listado excluye los
  anulados por defecto; `?anulado=todos` los incluye.
- **Monto mínimo `0.01`:** se valida en el serializer y otra vez en el
  servicio (defensa en profundidad). Se descarta `monto = 0`; el `CHECK` de la
  base es la última barrera.
- **Una sola transacción:** si falla el registro de bitácora, el movimiento no
  queda guardado (probado con un mock que hace fallar `Bitacora.registrar`).
- **Integridad en base de datos:** los `CHECK` y el índice existen en el modelo
  y en el DDL, no solo en la capa de validación.
- **Nombres de archivo según el código real:** se siguió el patrón de
  `compra_materia_prima` (`services/<accion>.py` + `consulta.py`, `APIView`,
  listados como arreglo plano), no el `services.py`/`selectors.py`/ViewSet
  genérico de la plantilla de arquitectura.

## 4. ⚠️ Pendientes o siguientes pasos

1. **Frontend:** tipos, servicio API, pestaña Gastos en `ComprasModuloPage`,
   modal de registro/anulación y permiso en `navigation.ts`. Verificar con
   `npx tsc -b`, `npm run build` y `npm run lint`.
2. **Resumen para reportes (`/api/gastos/resumen/`):** no implementado;
   corresponde a CU24/CU25, no a este CU.
3. **Bitácora de los tests:** los 28 tests de `gastos` cubren el contrato; la
   suite completa de `apps.compras` queda en 49 pruebas.

## 5. 🧪 Cómo probar lo implementado

```powershell
cd backend
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py test apps.compras
```

Resultado observado en esta sesión:

- `System check identified no issues (0 silenced).`
- `No changes detected`
- `migrate`: `bitacora.0016_acciones_cu20_gastos` y
  `gastos.0002_categoria_anulado_constraints` aplicadas.
- `Ran 49 tests in 9.103s — OK` (32 de ellos de `apps.compras.gastos`).

Para probar el endpoint completo hace falta un usuario con rol **Propietario**
o **Administrador** (permiso `registrar_gastos`) y su token JWT:

```http
POST /api/gastos/
Authorization: Bearer <token>
Content-Type: application/json

{
  "tipo": "gasto",
  "categoria": "servicios",
  "concepto": "Energía eléctrica",
  "monto": "320.00",
  "descripcion": "Factura de octubre"
}
```

```http
POST /api/gastos/1/anular/
Authorization: Bearer <token>
```

```http
GET /api/gastos/?tipo=gasto&categoria=servicios&fecha_desde=2026-11-01&anulado=todos
Authorization: Bearer <token>
```

> Nota: las migraciones `gastos.0002` y `bitacora.0016` no se aplican solas.
> Cada entorno debe ejecutar `manage.py migrate` antes de usar el endpoint.
