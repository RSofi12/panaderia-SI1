import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, Filter, Layers, Loader2, Search } from 'lucide-react';
import { Paginacion } from '../../components/Paginacion';
import { paginar, usePagina } from '../../components/paginar';
import {
  consultarReporteVentas,
  descargarReporteCsv,
  descargarReporteExcel,
  descargarReportePdf,
  fechaHoy,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
  type PeriodoReporte,
  type ReporteVentas,
} from '../../../../services/reporteVentasService';
import { inferirSelectoresPeriodo, type RangoConsultaReportes } from '../rangoConsulta';
import { BotonesExportacionTabla } from './BotonesExportacionTabla';
import { EncabezadoCasoUso } from './EncabezadoCasoUso';
import { TarjetaKpiReporte } from './TarjetaKpiReporte';

const PERIODOS: { id: PeriodoReporte; etiqueta: string }[] = [
  { id: 'dia', etiqueta: 'Día' },
  { id: 'semana', etiqueta: 'Semana' },
  { id: 'mes', etiqueta: 'Mes' },
];

const MENSAJE_SIN_DATOS = 'No hay datos disponibles para el período solicitado.';

const COLUMNAS_VENTAS = [
  { id: 'comprobante', etiqueta: 'Nº Comprobante' },
  { id: 'fecha', etiqueta: 'Fecha y Hora' },
  { id: 'metodo', etiqueta: 'Método de Pago' },
  { id: 'cajero', etiqueta: 'Cajero' },
  { id: 'total', etiqueta: 'Total' },
] as const;

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

function etiquetaMetodo(metodo: string | null | undefined): string {
  if (metodo === 'efectivo') return 'Efectivo';
  if (metodo === 'stripe') return 'Tarjeta';
  return 'Efectivo y tarjeta';
}

interface SeccionReporteVentasProps {
  rango: RangoConsultaReportes;
  metodoVoz?: string;
  onError: (mensaje: string) => void;
}

function etiquetaPeriodo(periodo: PeriodoReporte): string {
  return PERIODOS.find((item) => item.id === periodo)?.etiqueta ?? periodo;
}

export const SeccionReporteVentas: React.FC<SeccionReporteVentasProps> = ({
  rango,
  metodoVoz = '',
  onError,
}) => {
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [dia, setDia] = useState(fechaHoy);
  const [semana, setSemana] = useState(semanaActual);
  const [mes, setMes] = useState(mesActual);
  const [metodo, setMetodo] = useState(metodoVoz);
  const [reporte, setReporte] = useState<ReporteVentas | null>(null);
  const [consulta, setConsulta] = useState<{ desde: string; hasta: string; metodo: string } | null>(null);
  const [cargando, setCargando] = useState(false);
  const [descargando, setDescargando] = useState<'csv' | 'excel' | 'pdf' | ''>('');
  const [error, setError] = useState('');
  const [vistaTabla, setVistaTabla] = useState<'ventas' | 'productos'>('ventas');
  const [busqueda, setBusqueda] = useState('');
  const [columnaOrden, setColumnaOrden] = useState<'fecha' | 'comprobante' | 'total' | 'cajero'>('fecha');
  const [direccionOrden, setDireccionOrden] = useState<'asc' | 'desc'>('desc');
  const [tamanoPagina, setTamanoPagina] = useState(10);
  const [mostrarColumnas, setMostrarColumnas] = useState(false);
  const [columnasVisibles, setColumnasVisibles] = useState<Record<string, boolean>>({
    comprobante: true,
    fecha: true,
    metodo: true,
    cajero: true,
    total: true,
  });

  const valorPeriodo = periodo === 'dia' ? dia : periodo === 'semana' ? semana : mes;

  async function cargar(desde: string, hasta: string, metodoPago: string) {
    setError('');
    setCargando(true);
    try {
      const datos = await consultarReporteVentas(desde, hasta, metodoPago);
      setConsulta({ desde, hasta, metodo: metodoPago });
      setReporte(datos);
    } catch {
      setReporte(null);
      setConsulta(null);
      const mensaje = 'No se pudo armar el reporte de ventas de ese período.';
      setError(mensaje);
      onError(mensaje);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    setMetodo(metodoVoz);
  }, [metodoVoz]);

  useEffect(() => {
    const sel = inferirSelectoresPeriodo(rango.desde, rango.hasta);
    setPeriodo(sel.periodo);
    setDia(sel.dia);
    setSemana(sel.semana);
    setMes(sel.mes);
    void cargar(rango.desde, rango.hasta, metodo);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rango.desde, rango.hasta, rango.version, metodoVoz]);

  const columnasSeleccionadas = useMemo(
    () => Object.entries(columnasVisibles).filter(([, visible]) => visible).map(([id]) => id),
    [columnasVisibles],
  );

  const ventasFiltradas = useMemo(() => {
    if (!reporte?.ventas) return [];
    let items = [...reporte.ventas];
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase().trim();
      items = items.filter(
        (v) =>
          v.numero_comprobante.toString().includes(q) ||
          v.fecha_hora.toLowerCase().includes(q) ||
          v.cajero.toLowerCase().includes(q) ||
          etiquetaMetodo(v.metodo_pago).toLowerCase().includes(q) ||
          v.total.toString().includes(q),
      );
    }
    items.sort((a, b) => {
      let valA: string | number = a.id_venta;
      let valB: string | number = b.id_venta;
      if (columnaOrden === 'fecha') {
        valA = a.fecha_hora;
        valB = b.fecha_hora;
      } else if (columnaOrden === 'comprobante') {
        valA = a.numero_comprobante;
        valB = b.numero_comprobante;
      } else if (columnaOrden === 'total') {
        valA = Number(a.total);
        valB = Number(b.total);
      } else {
        valA = a.cajero.toLowerCase();
        valB = b.cajero.toLowerCase();
      }
      if (valA < valB) return direccionOrden === 'asc' ? -1 : 1;
      if (valA > valB) return direccionOrden === 'asc' ? 1 : -1;
      return 0;
    });
    return items;
  }, [reporte?.ventas, busqueda, columnaOrden, direccionOrden]);

  const clavePaginacion = `${consulta?.desde}|${consulta?.hasta}|${busqueda}|${columnaOrden}|${direccionOrden}|${tamanoPagina}`;
  const [paginaVentas, setPaginaVentas] = usePagina(clavePaginacion);
  const listadoPaginado = useMemo(
    () => paginar(ventasFiltradas, paginaVentas, tamanoPagina),
    [ventasFiltradas, paginaVentas, tamanoPagina],
  );

  async function exportar(tipo: 'csv' | 'excel' | 'pdf') {
    if (!consulta) return;
    if (reporte && reporte.cantidad === 0) {
      setError(MENSAJE_SIN_DATOS);
      onError(MENSAJE_SIN_DATOS);
      return;
    }
    setError('');
    setDescargando(tipo);
    try {
      if (tipo === 'pdf') {
        await descargarReportePdf(consulta.desde, consulta.hasta, consulta.metodo, columnasSeleccionadas);
      } else if (tipo === 'excel') {
        await descargarReporteExcel(consulta.desde, consulta.hasta, consulta.metodo, columnasSeleccionadas);
      } else {
        await descargarReporteCsv(consulta.desde, consulta.hasta, consulta.metodo, columnasSeleccionadas);
      }
    } catch {
      setError(tipo === 'pdf' ? MENSAJE_SIN_DATOS : 'No se pudo descargar el archivo.');
    } finally {
      setDescargando('');
    }
  }

  const totalFilas = vistaTabla === 'ventas' ? ventasFiltradas.length : reporte?.productos.length || 0;

  return (
    <section id="ventas" className="scroll-mt-24 space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <EncabezadoCasoUso
          cu="CU21"
          titulo="Generar reporte de ventas"
          descripcion="Ventas del período, detalladas por comprobante o por producto."
        />
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const local = rangoDelPeriodo(periodo, valorPeriodo);
            void cargar(local.desde, local.hasta, metodo);
          }}
          className="mt-4 space-y-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex rounded-xl bg-slate-100 p-1" role="group" aria-label="Granularidad de período de ventas">
              {PERIODOS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={periodo === item.id}
                  onClick={() => setPeriodo(item.id)}
                  className={`min-h-11 cursor-pointer rounded-lg px-4 py-1.5 text-xs font-bold transition-all ${
                    periodo === item.id
                      ? 'bg-amber-700 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {item.etiqueta}
                </button>
              ))}
            </div>
            <p className="text-xs font-medium text-slate-500">
              Período evaluado: <strong className="text-slate-800">{etiquetaPeriodo(periodo)}</strong>
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="flex-1 text-xs font-semibold text-slate-700">
              Seleccionar {etiquetaPeriodo(periodo)}
              {periodo === 'dia' ? (
                <input
                  required
                  type="date"
                  value={dia}
                  onChange={(e) => setDia(e.target.value)}
                  className="mt-1 block min-h-11 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
                />
              ) : null}
              {periodo === 'semana' ? (
                <input
                  required
                  type="week"
                  value={semana}
                  onChange={(e) => setSemana(e.target.value)}
                  className="mt-1 block min-h-11 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
                />
              ) : null}
              {periodo === 'mes' ? (
                <input
                  required
                  type="month"
                  value={mes}
                  onChange={(e) => setMes(e.target.value)}
                  className="mt-1 block min-h-11 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
                />
              ) : null}
            </label>

            <label className="text-xs font-semibold text-slate-700 sm:w-48">
              Método de pago
              <select
                value={metodo}
                onChange={(e) => setMetodo(e.target.value)}
                className="mt-1 block min-h-11 w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
              >
                <option value="">Todos los métodos</option>
                <option value="efectivo">Solo efectivo</option>
                <option value="stripe">Solo tarjeta (Stripe)</option>
              </select>
            </label>

            <button
              type="submit"
              disabled={cargando || !valorPeriodo}
              className="inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-xl bg-amber-700 px-5 text-sm font-bold text-white transition-colors hover:bg-amber-800 disabled:opacity-50"
            >
              {cargando ? <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" /> : <Filter className="h-4 w-4" />}
              Actualizar reporte
            </button>
          </div>
        </form>
      </div>

      {reporte ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <TarjetaKpiReporte
            etiqueta="Total recaudado"
            valor={bolivianos(reporte.total)}
            detalle={`${reporte.cantidad} ventas`}
          />
          <TarjetaKpiReporte etiqueta="Efectivo" valor={bolivianos(reporte.efectivo)} />
          <TarjetaKpiReporte etiqueta="Tarjeta" valor={bolivianos(reporte.tarjeta)} />
          <TarjetaKpiReporte
            etiqueta="Ticket promedio"
            valor={reporte.cantidad > 0 ? bolivianos(Number(reporte.total) / reporte.cantidad) : 'Bs 0.00'}
          />
        </div>
      ) : null}

      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xl font-bold text-slate-900">
              {vistaTabla === 'ventas' ? 'Ventas por período' : 'Productos vendidos'}
            </h3>
            <p className="mt-0.5 text-sm font-medium text-slate-500">Total filas: {totalFilas}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <BotonesExportacionTabla
              onCsv={() => void exportar('csv')}
              onExcel={() => void exportar('excel')}
              onPdf={() => void exportar('pdf')}
              descargando={descargando}
              deshabilitado={!consulta}
            />
            <button
              type="button"
              onClick={() => setVistaTabla(vistaTabla === 'ventas' ? 'productos' : 'ventas')}
              className="inline-flex min-h-11 cursor-pointer items-center gap-1 rounded-lg border border-amber-200 bg-amber-50 px-2.5 text-xs font-bold text-amber-900 transition-colors hover:bg-amber-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
            >
              <Layers className="h-3.5 w-3.5" aria-hidden="true" />
              {vistaTabla === 'ventas' ? 'Ver productos' : 'Ver ventas'}
            </button>
          </div>
        </div>

        {vistaTabla === 'ventas' ? (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 md:grid-cols-4">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" aria-hidden="true" />
                <input
                  type="search"
                  placeholder="Buscar comprobante, cajero o total…"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="min-h-11 w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm placeholder:text-slate-400 focus:border-amber-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
                />
              </div>
              <select
                value={columnaOrden}
                onChange={(e) => setColumnaOrden(e.target.value as typeof columnaOrden)}
                className="min-h-11 w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-amber-600 focus:outline-none"
                aria-label="Ordenar por"
              >
                <option value="fecha">Fecha y hora</option>
                <option value="comprobante">Nº comprobante</option>
                <option value="total">Total</option>
                <option value="cajero">Cajero</option>
              </select>
              <select
                value={direccionOrden}
                onChange={(e) => setDireccionOrden(e.target.value as 'asc' | 'desc')}
                className="min-h-11 w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-amber-600 focus:outline-none"
                aria-label="Dirección"
              >
                <option value="desc">Descendente</option>
                <option value="asc">Ascendente</option>
              </select>
              <select
                value={tamanoPagina}
                onChange={(e) => setTamanoPagina(Number(e.target.value))}
                className="min-h-11 w-full cursor-pointer rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:border-amber-600 focus:outline-none"
                aria-label="Filas por página"
              >
                <option value={5}>5 por página</option>
                <option value={10}>10 por página</option>
                <option value={20}>20 por página</option>
                <option value={50}>50 por página</option>
              </select>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-3">
              <button
                type="button"
                onClick={() => setMostrarColumnas(!mostrarColumnas)}
                className="flex min-h-11 cursor-pointer items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900"
                aria-expanded={mostrarColumnas}
              >
                {mostrarColumnas ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                Columnas visibles (también se incluyen en el PDF)
              </button>
              {mostrarColumnas ? (
                <div className="mt-2.5 flex flex-wrap gap-4">
                  {COLUMNAS_VENTAS.map((col) => (
                    <label key={col.id} className="inline-flex cursor-pointer items-center gap-1.5 text-xs text-slate-700">
                      <input
                        type="checkbox"
                        checked={!!columnasVisibles[col.id]}
                        onChange={() =>
                          setColumnasVisibles((prev) => ({ ...prev, [col.id]: !prev[col.id] }))
                        }
                        className="rounded border-slate-300 text-amber-700 focus:ring-amber-600"
                      />
                      {col.etiqueta}
                    </label>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {error ? (
          <p role="alert" className="mt-3 flex items-center gap-2 text-sm text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
            {error}
          </p>
        ) : null}

        <div className="mt-4 overflow-x-auto">
          {vistaTabla === 'ventas' ? (
            <table className="w-full min-w-[40rem] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-indigo-900">
                  {columnasVisibles.comprobante ? <th className="px-3 py-3">Comprobante</th> : null}
                  {columnasVisibles.fecha ? <th className="px-3 py-3">Fecha y hora</th> : null}
                  {columnasVisibles.metodo ? <th className="px-3 py-3">Método</th> : null}
                  {columnasVisibles.cajero ? <th className="px-3 py-3">Cajero</th> : null}
                  {columnasVisibles.total ? <th className="px-3 py-3 text-right">Total</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cargando ? (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-slate-500">
                      <Loader2 className="mx-auto h-6 w-6 animate-spin text-amber-700 motion-reduce:animate-none" />
                      <p className="mt-2 text-xs">Consultando ventas…</p>
                    </td>
                  </tr>
                ) : listadoPaginado.items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-sm font-medium text-slate-500">
                      No se encontraron ventas para este período o criterio de búsqueda.
                    </td>
                  </tr>
                ) : (
                  listadoPaginado.items.map((venta) => (
                    <tr key={venta.id_venta} className="transition-colors hover:bg-slate-50/80">
                      {columnasVisibles.comprobante ? (
                        <td className="px-3 py-3 font-bold text-slate-900">#{venta.numero_comprobante}</td>
                      ) : null}
                      {columnasVisibles.fecha ? (
                        <td className="px-3 py-3 text-slate-600">{venta.fecha_hora}</td>
                      ) : null}
                      {columnasVisibles.metodo ? (
                        <td className="px-3 py-3">
                          <span
                            className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${
                              venta.metodo_pago === 'stripe'
                                ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
                                : 'border-emerald-200 bg-emerald-50 text-emerald-700'
                            }`}
                          >
                            {etiquetaMetodo(venta.metodo_pago)}
                          </span>
                        </td>
                      ) : null}
                      {columnasVisibles.cajero ? (
                        <td className="px-3 py-3 font-medium text-slate-600">{venta.cajero}</td>
                      ) : null}
                      {columnasVisibles.total ? (
                        <td className="px-3 py-3 text-right font-black tabular-nums text-slate-900">
                          {bolivianos(venta.total)}
                        </td>
                      ) : null}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full min-w-[28rem] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-amber-900">
                  <th className="px-3 py-3">Producto</th>
                  <th className="px-3 py-3 text-center">Unidades</th>
                  <th className="px-3 py-3 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {!reporte?.productos || reporte.productos.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="py-10 text-center text-sm font-medium text-slate-500">
                      No hay productos vendidos en este período.
                    </td>
                  </tr>
                ) : (
                  reporte.productos.map((prod) => (
                    <tr key={prod.nombre} className="hover:bg-slate-50/80">
                      <td className="px-3 py-3 font-bold text-slate-900">{prod.nombre}</td>
                      <td className="px-3 py-3 text-center font-medium text-slate-600">{prod.cantidad} u.</td>
                      <td className="px-3 py-3 text-right font-bold tabular-nums text-slate-900">
                        {bolivianos(prod.subtotal)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        {vistaTabla === 'ventas' ? (
          <div className="mt-2 flex justify-end border-t border-slate-100 pt-2">
            <Paginacion
              pagina={listadoPaginado.pagina}
              totalPaginas={listadoPaginado.totalPaginas}
              onCambiar={setPaginaVentas}
              deshabilitado={cargando}
              etiqueta="Paginación de ventas"
            />
          </div>
        ) : null}
      </div>
    </section>
  );
};
