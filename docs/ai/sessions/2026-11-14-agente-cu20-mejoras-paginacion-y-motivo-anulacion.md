# Sesión: 2026-11-14 — Agente IA — Mejoras CU20 (Paginación Backend y Motivo de Anulación)

## Objetivo
Implementar las mejoras arquitectónicas y de auditoría identificadas en la auditoría técnica de CU20 (Registrar Gasto o Inversión):
1. **Paginación opcional en Backend (`PageNumberPagination` de DRF):** Soportar `?page=` y `?page_size=` en `GET /api/gastos/` manteniendo total compatibilidad retroactiva con clientes que esperan arreglos completos.
2. **Justificación / Motivo de Anulación en Frontend y Backend:** Permitir registrar un texto opcional de justificación al anular un gasto o inversión, el cual queda asentado en la descripción de la tabla `bitacora` (CU26).

---

## Cambios por Capa

### 1. Backend (`apps.compras.gastos`)
* **`services/registrar_movimiento.py`:**
  - `anular_movimiento(*, usuario, id_movimiento, motivo=None, agente_usuario=None)`: Acepta el parámetro `motivo`. Si se proporciona, se concatena a la descripción de la bitácora (`f'Anulación del movimiento #... — Motivo: {motivo}'`).
* **`views.py`:**
  - `GastoListCreateView.get()`: Detecta si en los query params viene `page` o `page_size`. De ser así, activa la paginación estándar de DRF (`count`, `next`, `previous`, `results`). Si no vienen parámetros de paginación, retorna el arreglo estándar como antes para evitar romper compatibilidad.
  - `GastoAnularView.post()`: Extrae `motivo = request.data.get('motivo')` y lo traslada a la llamada del servicio.
* **`tests.py`:**
  - Se agregaron pruebas para verificar que el motivo viaje a la bitácora y que el listado responda paginado al solicitar `?page=1&page_size=5`.

### 2. Frontend (`src/apps/dashboard/compras/`)
* **`services/gastosService.ts`:**
  - `anular(id: number, motivo?: string)`: Si se provee `motivo`, envía el payload JSON `{ motivo: motivo.trim() }`.
* **`components/AnularGastoModal.tsx`:**
  - Se incorporó un campo `<textarea>` para ingresar el motivo o justificación de anulación (ej. *"Factura duplicada, error en el monto"*).
  - Pasa el motivo al callback `onConfirmar(motivo)`.
* **`GastosPage.tsx`:**
  - `confirmarAnulacion(motivo?: string)`: Conecta el modal con `gastosService.anular(id, motivo)` y refresca el listado.
