import { useEffect, useState } from 'react';
import { isAxiosError } from 'axios';
import { Link } from 'react-router-dom';
import { AlertCircle, AlertTriangle, ArrowLeft, Filter, Loader2, Package, RefreshCw, Search } from 'lucide-react';
import { Paginacion } from '../components/Paginacion';
import { paginar, usePagina } from '../components/paginar';
import { consultarReporteExistencias } from '../../../services/reporteExistenciasService';
import type {
  EstadoExistencia,
  ReporteExistencias,
  ReporteExistenciasFiltros,
} from '../../../types/reporteExistencias';

const INITIAL_FILTERS: ReporteExistenciasFiltros = { tipo: 'todos', q: '', estado: 'todos' };
const FIELD_CLASS = 'min-h-11 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2';
const BUTTON_CLASS = 'inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60';
const STATUS_LABELS: Record<EstadoExistencia, string> = {
  normal: 'Normal',
  bajo_stock: 'Bajo stock',
  sin_inventario: 'Sin registro de inventario',
};
const STATUS_CLASSES: Record<EstadoExistencia, string> = {
  normal: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  bajo_stock: 'border-amber-200 bg-amber-50 text-amber-900',
  sin_inventario: 'border-slate-300 bg-slate-100 text-slate-800',
};
const QUANTITY_FORMAT = new Intl.NumberFormat('es-BO', { maximumFractionDigits: 3 });

function formatQuantity(value: string): string {
  // Solo presentación: las comparaciones y los decimales originales pertenecen a la API.
  return QUANTITY_FORMAT.format(Number(value));
}

interface QueryResult {
  key: string;
  data: ReporteExistencias | null;
  error: string | null;
}

function errorMessage(error: unknown): string {
  if (isAxiosError<Record<string, unknown>>(error)) {
    if (error.response?.status === 403) {
      return 'No tienes el permiso necesario para consultar el reporte de existencias.';
    }
    if (error.response?.status === 400) {
      const messages = Object.values(error.response.data).flatMap((value) =>
        typeof value === 'string' ? [value]
          : Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [],
      );
      if (messages.length > 0) return messages.join(' ');
    }
  }
  return 'No se pudieron consultar las existencias. Comprueba la conexión con el servidor y vuelve a intentar.';
}

export default function ReporteExistenciasPage() {
  const [filters, setFilters] = useState<ReporteExistenciasFiltros>(INITIAL_FILTERS);
  const [query, setQuery] = useState({ ...INITIAL_FILTERS, version: 0 });
  const [result, setResult] = useState<QueryResult | null>(null);
  const { tipo, q, estado, version } = query;
  const queryKey = JSON.stringify([tipo, q, estado, version]);

  useEffect(() => {
    const controller = new AbortController();
    consultarReporteExistencias({ tipo, q, estado }, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setResult({ key: queryKey, data, error: null });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setResult({ key: queryKey, data: null, error: errorMessage(error) });
        }
      });
    return () => controller.abort();
  }, [tipo, q, estado, queryKey]);

  // Una respuesta anterior nunca representa los filtros que se están consultando.
  const current = result?.key === queryKey ? result : null;
  const loading = current === null;
  const report = current?.data ?? null;
  const error = current?.error ?? null;
  const pendingFilters = filters.tipo !== tipo || filters.q.trim() !== q || filters.estado !== estado;
  const hasFilters = tipo !== 'todos' || q !== '' || estado !== 'todos';
  const [page, setPage] = usePagina(queryKey);
  const visible = paginar(report?.resultados ?? [], page);

  function submitFilters() {
    setQuery((previous) => ({ ...filters, q: filters.q.trim(), version: previous.version + 1 }));
  }

  function retry() {
    setQuery((previous) => ({ ...previous, version: previous.version + 1 }));
  }

  function clearFilters() {
    setFilters(INITIAL_FILTERS);
    setQuery((previous) => ({ ...INITIAL_FILTERS, version: previous.version + 1 }));
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <Link to="/dashboard/reportes" className="inline-flex min-h-11 items-center gap-2 rounded-lg text-sm font-semibold text-amber-800 underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2">
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />Volver a Reportes
      </Link>

      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">CU23 · Panadería Santiago</p>
          <h1 className="mt-1 flex items-center gap-2 text-2xl font-bold tracking-tight text-slate-900">
            <Package aria-hidden="true" className="h-7 w-7 shrink-0 text-amber-700" />Reporte de existencias
          </h1>
          <p className="mt-2 text-sm text-slate-600">Consulta el stock actual de materias primas y productos terminados, activos e inactivos.</p>
        </div>
        <button type="button" disabled={loading} onClick={retry} className={`${BUTTON_CLASS} shrink-0 border border-slate-300 bg-white text-slate-800 hover:bg-slate-50`}>
          <RefreshCw aria-hidden="true" className="h-4 w-4" />Actualizar consulta
        </button>
      </header>

      <aside aria-labelledby="minimum-notice" className="flex gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-950">
        <AlertTriangle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-amber-800" />
        <div className="space-y-1 text-sm">
          <h2 id="minimum-notice" className="font-semibold">Mínimo referencial de productos terminados: provisional</h2>
          <p>Se utiliza un umbral referencial global de {formatQuantity(report?.umbral_productos_terminados ?? '20.000')} unidades para todos los productos terminados. No es una configuración guardada de cada producto. Este criterio es provisional y está pendiente de validación con el equipo. Las materias primas utilizan su mínimo guardado en catálogo.</p>
          <p>El servidor marca bajo stock cuando la existencia es estrictamente menor al mínimo; un valor igual al mínimo es normal. «Sin registro de inventario» indica la ausencia del registro y no equivale a stock cero.</p>
        </div>
      </aside>

      <section aria-labelledby="filters-heading" className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs sm:p-5">
        <h2 id="filters-heading" className="text-base font-bold text-slate-900">Filtros de consulta</h2>
        <form onSubmit={(event) => { event.preventDefault(); submitFilters(); }} className="mt-4 space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <label className="block text-sm font-semibold text-slate-700">
              Tipo de existencia
              <select value={filters.tipo} onChange={(event) => setFilters((previous) => ({ ...previous, tipo: event.target.value as ReporteExistenciasFiltros['tipo'] }))} className={`${FIELD_CLASS} mt-2`}>
                <option value="todos">Todos los tipos</option>
                <option value="materia_prima">Materias primas</option>
                <option value="producto_terminado">Productos terminados</option>
              </select>
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Buscar por nombre
              <span className="relative mt-2 block">
                <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-500" />
                <input type="search" maxLength={100} value={filters.q} onChange={(event) => setFilters((previous) => ({ ...previous, q: event.target.value }))} placeholder="Nombre del insumo o producto" className={`${FIELD_CLASS} pl-10`} />
              </span>
            </label>
            <label className="block text-sm font-semibold text-slate-700">
              Estado de existencias
              <select value={filters.estado} onChange={(event) => setFilters((previous) => ({ ...previous, estado: event.target.value as ReporteExistenciasFiltros['estado'] }))} className={`${FIELD_CLASS} mt-2`}>
                <option value="todos">Todos los estados</option>
                <option value="normal">Normal</option>
                <option value="bajo_stock">Bajo stock</option>
                <option value="sin_inventario">Sin registro de inventario</option>
              </select>
            </label>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" disabled={loading && !pendingFilters} className={`${BUTTON_CLASS} bg-amber-700 text-white hover:bg-amber-800`}>
              {loading ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin motion-reduce:animate-none" /> : <Filter aria-hidden="true" className="h-4 w-4" />}
              Consultar existencias
            </button>
            <button type="button" onClick={clearFilters} disabled={loading && !pendingFilters && !hasFilters} className={`${BUTTON_CLASS} text-amber-800 underline underline-offset-4 hover:bg-amber-50`}>Limpiar filtros</button>
            <p className="text-sm text-slate-600">Los filtros se aplican al consultar.</p>
          </div>
          {pendingFilters ? <p role="status" className="text-sm font-medium text-amber-900">Hay cambios sin aplicar. La consulta conserva los últimos filtros enviados.</p> : null}
        </form>
      </section>

      <section aria-labelledby="summary-heading">
        <h2 id="summary-heading" className="mb-3 text-sm font-bold text-slate-700">Resumen de los resultados filtrados</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
          {[
            { label: 'Total de registros', value: report?.resumen.total },
            { label: 'Materias primas', value: report?.resumen.materias_primas },
            { label: 'Productos terminados', value: report?.resumen.productos_terminados },
            { label: 'Bajo stock', value: report?.resumen.bajo_stock },
            { label: 'Sin registro de inventario', value: report?.resumen.sin_inventario },
          ].map((item) => (
            <article key={item.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
              <h3 className="text-sm font-semibold text-slate-600">{item.label}</h3>
              <p className="mt-2 text-3xl font-bold tabular-nums text-slate-900">{item.value ?? '—'}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="results-heading" aria-busy={loading} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
        <div className="border-b border-slate-100 p-4 sm:p-5">
          <h2 id="results-heading" className="text-lg font-bold text-slate-900">Detalle de existencias</h2>
          <p className="mt-1 text-sm text-slate-600">Los estados y mínimos utilizados provienen del servidor. Se incluyen registros activos e inactivos.</p>
        </div>
        {loading ? (
          <p role="status" className="flex min-h-40 items-center justify-center gap-2 p-6 text-sm text-slate-700">
            <Loader2 aria-hidden="true" className="h-5 w-5 animate-spin motion-reduce:animate-none" />Consultando existencias…
          </p>
        ) : error ? (
          <div className="space-y-3 p-6">
            <p role="alert" className="flex items-start gap-2 text-sm text-rose-800"><AlertCircle aria-hidden="true" className="h-5 w-5 shrink-0" />{error}</p>
            <button type="button" onClick={retry} className={`${BUTTON_CLASS} border border-slate-300 text-slate-800 hover:bg-slate-50`}>Reintentar consulta</button>
          </div>
        ) : report && report.resultados.length === 0 ? (
          <div className="space-y-3 p-6">
            <p role="status" className="text-sm text-slate-700">{hasFilters ? 'No hay existencias que coincidan con los filtros enviados.' : 'No hay materias primas ni productos terminados registrados.'}</p>
            {hasFilters ? <button type="button" onClick={clearFilters} className={`${BUTTON_CLASS} text-amber-800 underline underline-offset-4 hover:bg-amber-50`}>Ver todos los registros</button> : null}
          </div>
        ) : report ? (
          <>
            <p role="status" className="px-4 py-3 text-sm font-medium text-slate-700 sm:px-5">Mostrando {visible.inicio + 1}–{visible.fin} de {visible.total} registros de la consulta.</p>
            <div tabIndex={0} role="region" aria-label="Tabla de existencias; desplázate horizontalmente para ver todas las columnas" className="overflow-x-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-amber-600">
              <table className="w-full min-w-[53rem] text-left text-sm">
                <caption className="sr-only">Existencias por nombre, tipo, condición del catálogo, stock, unidad, mínimo utilizado y estado.</caption>
                <thead className="border-y border-slate-200 bg-slate-50 text-slate-700">
                  <tr>{['Nombre', 'Tipo', 'Condición', 'Stock actual', 'Unidad', 'Mínimo utilizado', 'Estado'].map((label) => <th key={label} scope="col" className="px-4 py-3 font-semibold">{label}</th>)}</tr>
                </thead>
                <tbody>
                  {visible.items.map((item) => (
                    <tr key={`${item.tipo}:${item.id}`} className="border-b border-slate-100 last:border-b-0">
                      <th scope="row" className="max-w-64 break-words px-4 py-4 font-semibold text-slate-900">{item.nombre}</th>
                      <td className="px-4 py-4 text-slate-700">{item.tipo === 'materia_prima' ? 'Materia prima' : 'Producto terminado'}</td>
                      <td className="px-4 py-4 text-slate-700">{item.activo ? 'Activo' : 'Inactivo'}</td>
                      <td className="px-4 py-4 font-medium tabular-nums text-slate-900">{item.stock_actual === null ? <span aria-label="Sin registro de inventario">—</span> : formatQuantity(item.stock_actual)}</td>
                      <td className="px-4 py-4 text-slate-700">{item.unidad_medida}</td>
                      <td className="px-4 py-4 text-slate-900">
                        <p className="font-medium tabular-nums">{formatQuantity(item.stock_minimo)} {item.unidad_medida}</p>
                        <p className="mt-1 text-xs text-slate-600">{item.origen_minimo === 'catalogo' ? 'Guardado en catálogo' : 'Referencial global · provisional'}</p>
                      </td>
                      <td className="px-4 py-4"><span className={`inline-flex whitespace-nowrap rounded-full border px-2.5 py-1 text-xs font-semibold ${STATUS_CLASSES[item.estado]}`}>{STATUS_LABELS[item.estado]}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Paginacion pagina={visible.pagina} totalPaginas={visible.totalPaginas} onCambiar={setPage} etiqueta="Paginación del reporte de existencias" />
          </>
        ) : null}
      </section>
    </div>
  );
}
