import React, { useEffect, useMemo, useState } from 'react';
import { isAxiosError } from 'axios';
import { AlertCircle, Filter, Loader2, Search } from 'lucide-react';
import { Paginacion } from '../../components/Paginacion';
import { paginar, usePagina } from '../../components/paginar';
import {
  consultarReporteExistencias,
  descargarReporteExistenciasCsv,
  descargarReporteExistenciasExcel,
  descargarReporteExistenciasPdf,
} from '../../../../services/reporteExistenciasService';
import type {
  EstadoExistencia,
  ReporteExistencias,
  ReporteExistenciasFiltros,
} from '../../../../types/reporteExistencias';
import { BotonesExportacionTabla } from './BotonesExportacionTabla';
import { EncabezadoCasoUso } from './EncabezadoCasoUso';
import { TarjetaKpiReporte } from './TarjetaKpiReporte';

const INITIAL_FILTERS: ReporteExistenciasFiltros = { tipo: 'todos', q: '', estado: 'todos' };
const STATUS_LABELS: Record<EstadoExistencia, string> = {
  normal: 'Disponible',
  bajo_stock: 'Stock bajo',
  sin_inventario: 'Sin registro',
};
const STATUS_CLASSES: Record<EstadoExistencia, string> = {
  normal: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  bajo_stock: 'border-amber-200 bg-amber-50 text-amber-900',
  sin_inventario: 'border-rose-200 bg-rose-50 text-rose-800',
};
const QUANTITY_FORMAT = new Intl.NumberFormat('es-BO', { maximumFractionDigits: 3 });

function formatQuantity(value: string): string {
  return QUANTITY_FORMAT.format(Number(value));
}

function errorMessage(error: unknown): string {
  if (isAxiosError<Record<string, unknown>>(error)) {
    if (error.response?.status === 403) {
      return 'No tienes el permiso necesario para consultar existencias.';
    }
  }
  return 'No se pudieron consultar las existencias.';
}


export const SeccionReporteExistencias: React.FC = () => {
  const [filters, setFilters] = useState<ReporteExistenciasFiltros>(INITIAL_FILTERS);
  const [query, setQuery] = useState({ ...INITIAL_FILTERS, version: 0 });
  const [reporte, setReporte] = useState<ReporteExistencias | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [descargando, setDescargando] = useState<'csv' | 'excel' | 'pdf' | ''>('');

  const queryKey = JSON.stringify(query);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    consultarReporteExistencias(
      { tipo: query.tipo, q: query.q, estado: query.estado },
      controller.signal,
    )
      .then((data) => {
        if (!controller.signal.aborted) setReporte(data);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setReporte(null);
          setError(errorMessage(err));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [query.tipo, query.q, query.estado, query.version]);

  const unidades = useMemo(() => {
    if (!reporte) return 0;
    return reporte.resultados.reduce((acc, item) => acc + Number(item.stock_actual ?? 0), 0);
  }, [reporte]);

  const [page, setPage] = usePagina(queryKey);
  const visible = paginar(reporte?.resultados ?? [], page, 10);

  function aplicarFiltros(event: React.FormEvent) {
    event.preventDefault();
    setQuery((prev) => ({ ...filters, q: filters.q.trim(), version: prev.version + 1 }));
  }

  function limpiar() {
    setFilters(INITIAL_FILTERS);
    setQuery((prev) => ({ ...INITIAL_FILTERS, version: prev.version + 1 }));
  }

  async function exportar(tipo: 'csv' | 'excel' | 'pdf') {
    if (!reporte || reporte.resultados.length === 0) return;
    setError(null);
    setDescargando(tipo);
    const filtros = { tipo: query.tipo, q: query.q, estado: query.estado };
    try {
      if (tipo === 'pdf') {
        await descargarReporteExistenciasPdf(filtros);
      } else if (tipo === 'excel') {
        await descargarReporteExistenciasExcel(filtros);
      } else {
        await descargarReporteExistenciasCsv(filtros);
      }
    } catch {
      setError('No se pudo descargar el archivo.');
    } finally {
      setDescargando('');
    }
  }

  return (
    <section id="existencias" className="scroll-mt-24 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <EncabezadoCasoUso
          cu="CU23"
          titulo="Generar reporte de existencias"
          descripcion="Stock actual de materias primas y productos terminados. No depende del rango de fechas."
        />
        <BotonesExportacionTabla
          onCsv={() => void exportar('csv')}
          onExcel={() => void exportar('excel')}
          onPdf={() => void exportar('pdf')}
          descargando={descargando}
          deshabilitado={!reporte || reporte.resultados.length === 0}
        />
      </div>

      <form onSubmit={aplicarFiltros} className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
        <label className="text-xs font-semibold text-slate-700">
          Buscar
          <span className="relative mt-1 block">
            <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" aria-hidden="true" />
            <input
              type="search"
              value={filters.q}
              onChange={(e) => setFilters((prev) => ({ ...prev, q: e.target.value }))}
              placeholder="Nombre del insumo o producto"
              className="min-h-11 w-full rounded-xl border border-slate-200 py-2 pl-9 pr-3 text-sm focus:border-amber-600 focus:outline-none"
            />
          </span>
        </label>
        <label className="text-xs font-semibold text-slate-700">
          Tipo
          <select
            value={filters.tipo}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, tipo: e.target.value as ReporteExistenciasFiltros['tipo'] }))
            }
            className="mt-1 min-h-11 w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 text-sm focus:border-amber-600 focus:outline-none"
          >
            <option value="todos">Todos</option>
            <option value="materia_prima">Materias primas</option>
            <option value="producto_terminado">Productos terminados</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-slate-700">
          Estado
          <select
            value={filters.estado}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                estado: e.target.value as ReporteExistenciasFiltros['estado'],
              }))
            }
            className="mt-1 min-h-11 w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 text-sm focus:border-amber-600 focus:outline-none"
          >
            <option value="todos">Todos</option>
            <option value="normal">Disponible</option>
            <option value="bajo_stock">Stock bajo</option>
            <option value="sin_inventario">Sin registro</option>
          </select>
        </label>
        <div className="flex items-end gap-2">
          <button
            type="submit"
            className="inline-flex min-h-11 flex-1 cursor-pointer items-center justify-center gap-2 rounded-xl bg-amber-700 px-4 text-sm font-bold text-white hover:bg-amber-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
          >
            <Filter className="h-4 w-4" aria-hidden="true" />
            Aplicar filtros
          </button>
          <button
            type="button"
            onClick={limpiar}
            className="inline-flex min-h-11 cursor-pointer items-center rounded-xl px-3 text-sm font-semibold text-amber-800 underline underline-offset-4 hover:bg-amber-50"
          >
            Limpiar
          </button>
        </div>
      </form>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <TarjetaKpiReporte etiqueta="Productos" valor={reporte?.resumen.total ?? '—'} />
        <TarjetaKpiReporte
          etiqueta="Unidades"
          valor={reporte ? formatQuantity(String(unidades)) : '—'}
        />
        <TarjetaKpiReporte etiqueta="Stock bajo" valor={reporte?.resumen.bajo_stock ?? '—'} />
        <TarjetaKpiReporte etiqueta="Sin registro" valor={reporte?.resumen.sin_inventario ?? '—'} />
        <TarjetaKpiReporte
          etiqueta="Terminados"
          valor={reporte?.resumen.productos_terminados ?? '—'}
        />
      </div>

      <div className="mt-5 overflow-x-auto">
        {loading ? (
          <p role="status" className="flex min-h-40 items-center justify-center gap-2 text-sm text-slate-600">
            <Loader2 className="h-5 w-5 animate-spin text-amber-700 motion-reduce:animate-none" aria-hidden="true" />
            Consultando existencias…
          </p>
        ) : error ? (
          <p role="alert" className="flex items-start gap-2 p-4 text-sm text-rose-800">
            <AlertCircle className="h-5 w-5 shrink-0" aria-hidden="true" />
            {error}
          </p>
        ) : !reporte || reporte.resultados.length === 0 ? (
          <p role="status" className="p-6 text-center text-sm text-slate-500">
            No hay existencias que coincidan con los filtros.
          </p>
        ) : (
          <table className="w-full min-w-[52rem] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-indigo-900">
                <th className="px-3 py-3">Producto</th>
                <th className="px-3 py-3">Tipo</th>
                <th className="px-3 py-3">Stock</th>
                <th className="px-3 py-3">Nivel</th>
                <th className="px-3 py-3">Unidad</th>
                <th className="px-3 py-3">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {visible.items.map((item) => (
                <tr key={`${item.tipo}:${item.id}`} className="hover:bg-slate-50/80">
                  <th scope="row" className="max-w-64 px-3 py-4 font-semibold text-slate-900">
                    {item.nombre}
                  </th>
                  <td className="px-3 py-4 text-slate-700">
                    {item.tipo === 'materia_prima' ? 'Materia prima' : 'Producto terminado'}
                  </td>
                  <td className="px-3 py-4 font-medium tabular-nums text-slate-900">
                    {item.stock_actual === null ? '—' : formatQuantity(item.stock_actual)}
                    {item.stock_actual !== null ? (
                      <span className="block text-xs font-normal text-slate-500">
                        Mínimo: {formatQuantity(item.stock_minimo)}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-3 py-4">
                    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${STATUS_CLASSES[item.estado]}`}>
                      {STATUS_LABELS[item.estado]}
                    </span>
                  </td>
                  <td className="px-3 py-4 text-slate-700">{item.unidad_medida}</td>
                  <td className="px-3 py-4 text-slate-700">{item.activo ? 'Activo' : 'Inactivo'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {reporte && reporte.resultados.length > 0 ? (
        <div className="mt-2 flex justify-end border-t border-slate-100 pt-2">
          <Paginacion
            pagina={visible.pagina}
            totalPaginas={visible.totalPaginas}
            onCambiar={setPage}
            deshabilitado={loading}
            etiqueta="Paginación de existencias"
          />
        </div>
      ) : null}
    </section>
  );
};
