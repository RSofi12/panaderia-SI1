# Sesión 2026-11-13 — CU20 Frontend

**Autor:** opencode
**Alcance:** frontend de CU20 (gastos e inversiones)
**Estado:** completo y verificado con `tsc`, build y lint. Sin commit (lo hace el usuario).

## Objetivo

Construir la pestaña "Gastos e inversiones" del módulo Compras y Proveedores,
consumiendo la API de CU20 ya implementada y verificada en el backend, sin salir
del lenguaje visual existente del dashboard.

## Cambios por capa

### Frontend

| Archivo | Cambio |
|---|---|
| `frontend/src/types/gasto.ts` | creado: `MovimientoEconomico`, `MovimientoEconomicoInput`, `GastoFiltros` y catálogos `TIPOS_MOVIMIENTO` / `CATEGORIAS_MOVIMIENTO` |
| `frontend/src/services/gastosService.ts` | creado: `listar`, `obtener`, `registrar`, `anular`; descarta filtros vacíos |
| `frontend/src/apps/dashboard/compras/GastosPage.tsx` | creado: resumen, filtros, tabla, paginación, alta y anulación |
| `frontend/src/apps/dashboard/compras/components/RegistrarGastoModal.tsx` | creado: formulario accesible (`role="dialog"`), validación local + errores de DRF por campo |
| `frontend/src/apps/dashboard/compras/components/AnularGastoModal.tsx` | creado: confirmación `role="alertdialog"`, foco inicial en "Cancelar" |
| `frontend/src/apps/dashboard/compras/ComprasModuloPage.tsx` | pestaña `?tab=gastos` visible con `registrar_gastos` |
| `frontend/src/apps/dashboard/navigation.ts` | `registrar_gastos` agregado a los permisos del módulo Compras |
| `frontend/src/routes/AppRoutes.tsx` | comentario de la ruta actualizado (CU7 + CU20 + CU6) |

### Backend

Sin cambios en esta sesión; se reutiliza la API de CU20 ya implementada
(`/api/gastos/`, `/api/gastos/<id>/`, `/api/gastos/<id>/anular/`).

## Decisiones

- **Un solo momento visual fuerte:** la "cinta de caja" con el total de egresos del
  período y una barra proporcional gasto/inversión. El resto sigue el patrón del
  dashboard (tarjetas `rounded-2xl border-slate-200 shadow-xs`, tipografía y
  botones ámbar con gradiente, filtros `bg-slate-50` + `rounded-xl`).
- Totales calculados sobre movimientos **vigentes**; si se incluyen anulados, la
  cinta lo aclara y no los suma. La autoridad del dinero sigue siendo el backend.
- Todos los montos viajan como string (DRF); nunca se convierten para persistir.
- Anulación lógica, con modal de confirmación y aviso de que queda en la bitácora.
- Accesibilidad: `aria-modal`, Escape, bloqueo de scroll, foco inicial en el primer
  campo (alta) y en "Cancelar" (anulación), errores con `role="alert"`.
- Se respeta `prefers-reduced-motion`: solo se usa la animación existente
  `mostrador-aparecer` y transiciones de color/ancho.

## Verificación

- `npx tsc -b` → sin errores.
- `npm run build` → correcto (`✓ built`). Persiste el aviso previo de chunks > 500 kB.
- `npm run lint` → sin hallazgos en los archivos nuevos; los 20 errores existentes
  están en `usuarios/roles/RolesTab.tsx` y `services/produccionService.ts`, ajenos a CU20.
- Contrato verificado contra `backend/apps/compras/gastos/serializers.py` y
  `consulta.py`: nombres de campo, `registrado_por` y `?anulado=todos` coinciden.

## Pendientes

- Recorrido visual con sesión real (Administrador o Propietario): registrar, filtrar,
  anular e incluir anulados.
- Commit manual por parte del usuario.

## Cómo probar

1. Backend: `python manage.py runserver`.
2. Frontend: `npm run dev`, entrar con un rol con `registrar_gastos` y abrir
   Compras y Proveedores → "Gastos e inversiones".
3. Registrar un gasto, filtrar por tipo/categoría/fechas, anularlo e incluir anulados.
