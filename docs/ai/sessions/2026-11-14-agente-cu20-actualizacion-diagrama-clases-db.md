# Sesión: 2026-11-14 — Agente IA — Actualización Diagrama de Clases BD (CU20 Gastos e Inversiones)

## Objetivo
Actualizar el diagrama de clases PlantUML de la base de datos ([`docs/informes/database_panaderia_con_funciones.puml`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/database_panaderia_con_funciones.puml)) con los nuevos atributos y operaciones del modelo `MovimientoEconomico` (sub-app `backend/apps/compras/gastos/`, CU20) reflejados en [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql) y en el código del backend.

---

## Cambios Aplicados al Diagrama de Clases (`MovimientoEconomico`)

1. **Nuevos Atributos:**
   - `-categoria : String`: Clasificación del egreso operativo o inversión (`alquiler`, `servicios`, `mantenimiento`, `equipos`, `otros`). Necesario para la agregación en los reportes económicos (CU24 y CU25).
   - `-anulado : boolean`: Flag de anulación lógica (`default false`). Por trazabilidad y auditoría contable no se eliminan físicamente los registros (`DELETE`), sino que se marcan como anulados para excluirlos de los reportes financieros.

2. **Ajuste de Métodos / Operaciones:**
   - Se removió `+editar()`, ya que por regla de negocio contable los movimientos económicos no admiten modificación directa tras su registro.
   - Se incorporó `+consultar()`: Consulta de registros con filtros por tipo, categoría, rango de fechas y estado de anulación.
   - Se incorporó `+anular()`: Anulación lógica auditada con registro de acción `ANULACION_MOVIMIENTO_ECONOMICO` en `Bitacora`.

3. **Relaciones Mantenidas:**
   - `Usuario "1" -- "0..*" MovimientoEconomico : registra >` (Llave foránea `id_usuario` con `on_delete=PROTECT` hacia el modelo de usuarios).

---

## Archivos Afectados
- [`docs/informes/database_panaderia_con_funciones.puml`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/database_panaderia_con_funciones.puml)
- [`docs/informes/Database_Panaderia_Santiago.sql`](file:///c:/Users/PERSONAL/panaderia-SI1/docs/informes/Database_Panaderia_Santiago.sql)
