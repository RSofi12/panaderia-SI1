import React, { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Filter,
  Layers,
  Loader2,
  Search,
} from 'lucide-react';
import { Paginacion } from '../../components/Paginacion';
import { paginar, usePagina } from '../../components/paginar';
import {
  consultarReporteProduccion,
  descargarReporteProduccionCsv,
  descargarReporteProduccionPdf,
} from '../../../../services/reporteProduccionService';
import {
  fechaHoy,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
  semanaIsoDesdeFecha,
  type PeriodoReporte,
} from '../../../../services/reporteVentasService';
import type { LoteProduccion, ReporteProduccion } from '../../../../types/reporteProduccion';
import { inferirSelectoresPeriodo, type RangoConsultaReportes } from '../rangoConsulta';
import { EncabezadoCasoUso } from './EncabezadoCasoUso';
import { BotonesExportacionTabla } from './BotonesExportacionTabla';
import { TarjetaKpiReporte } from './TarjetaKpiReporte';

const MENSAJE_SIN_DATOS = 'No hay datos disponibles para el período solicitado.';

const PERIODOS: { id: PeriodoReporte; etiqueta: string }[] = [
  { id: 'dia', etiqueta: 'Día' },
  { id: 'semana', etiqueta: 'Semana' },
  { id: 'mes', etiqueta: 'Mes' },
];

interface ColumnaConfig {
  id: string;
  etiqueta: string;
}

const COLUMNAS_LOTES: ColumnaConfig[] = [
  { id: 'lote', etiqueta: 'Nº Lote' },
  { id: 'fecha', etiqueta: 'Fecha' },
  { id: 'jornada', etiqueta: 'Jornada' },
  { id: 'responsable', etiqueta: 'Responsable' },
  { id: 'unidades', etiqueta: 'Unidades' },
  { id: 'costo', etiqueta: 'Costo' },
];

type ColumnaOrden = 'fecha' | 'lote' | 'unidades' | 'responsable' | 'costo';

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

function etiquetaJornada(jornada: string): string {
  if (jornada === 'Mañana') return 'Mañana';
  if (jornada === 'Tarde') return 'Tarde';
  if (jornada === 'Noche') return 'Noche';
  if (jornada === 'unica') return 'Jornada única';
  return 'Todas las jornadas';
}

function etiquetaPeriodo(periodo: PeriodoReporte): string {
  return PERIODOS.find((item) => item.id === periodo)?.etiqueta ?? periodo;
}

function badgeJornada(jornada: string): string {
  if (jornada === 'Tarde') return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  if (jornada === 'Noche' || jornada === 'Jornada Única') return 'bg-slate-100 text-slate-700 border-slate-200';
  return 'bg-amber-50 text-amber-800 border-amber-200';
}

export interface ComandoProduccionPendiente {
  formato: string;
  accion: string;
  desde?: string;
  hasta?: string;
  jornada?: string;
}

interface ReporteProduccionViewProps {
  onAvisoSinDatos?: (mensaje: string) => void;
  comandoVozPendiente?: ComandoProduccionPendiente | null;
  onComandoVozEjecutado?: () => void;
  rangoCompartido?: RangoConsultaReportes;
}

export const ReporteProduccionView: React.FC<ReporteProduccionViewProps> = ({
  onAvisoSinDatos,
  comandoVozPendiente,
  onComandoVozEjecutado,
  rangoCompartido,
}) => {
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [dia, setDia] = useState(fechaHoy);
  const [semana, setSemana] = useState(semanaActual);
  const [mes, setMes] = useState(mesActual);
  const [jornada, setJornada] = useState('');

  const [reporte, setReporte] = useState<ReporteProduccion | null>(null);
  const [consulta, setConsulta] = useState<{
    desde: string;
    hasta: string;
    periodo: PeriodoReporte;
    jornada: string;
  } | null>(null);

  const [cargando, setCargando] = useState(false);
  const [descargando, setDescargando] = useState<'csv' | 'excel' | 'pdf' | ''>('');
  const [error, setError] = useState('');
  const [vistaTabla, setVistaTabla] = useState<'lotes' | 'productos'>('lotes');
  const [busqueda, setBusqueda] = useState('');
  const [columnaOrden, setColumnaOrden] = useState<ColumnaOrden>('fecha');
  const [direccionOrden, setDireccionOrden] = useState<'asc' | 'desc'>('desc');
  const [tamanoPagina, setTamanoPagina] = useState(10);
  const [mostrarColumnas, setMostrarColumnas] = useState(true);
  const [columnasVisibles, setColumnasVisibles] = useState<Record<string, boolean>>({
    lote: true,
    fecha: true,
    jornada: true,
    responsable: true,
    unidades: true,
    costo: true,
  });

  const valorPeriodo = periodo === 'dia' ? dia : periodo === 'semana' ? semana : mes;

  const columnasSeleccionadas = useMemo(
    () =>
      Object.entries(columnasVisibles)
        .filter(([, visible]) => visible)
        .map(([id]) => id),
    [columnasVisibles],
  );

  async function cargar(desde: string, hasta: string, jornadaFiltro: string) {
    setError('');
    setCargando(true);
    try {
      setConsulta({ desde, hasta, periodo, jornada: jornadaFiltro });
      const datos = await consultarReporteProduccion(desde, hasta, jornadaFiltro);
      setReporte(datos);
      if (datos.cantidad === 0 && datos.productos.length === 0) {
        const mensaje = MENSAJE_SIN_DATOS;
        setError(mensaje);
        onAvisoSinDatos?.(mensaje);
      }
      return datos;
    } catch {
      setReporte(null);
      setConsulta(null);
      setError('No se pudo armar el reporte de ese período.');
      return null;
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    if (rangoCompartido) {
      const sel = inferirSelectoresPeriodo(rangoCompartido.desde, rangoCompartido.hasta);
      setPeriodo(sel.periodo);
      setDia(sel.dia);
      setSemana(sel.semana);
      setMes(sel.mes);
      const timer = window.setTimeout(() => {
        void cargar(rangoCompartido.desde, rangoCompartido.hasta, jornada);
      }, 0);
      return () => window.clearTimeout(timer);
    }
    const rango = rangoDelPeriodo(periodo, valorPeriodo);
    const timer = window.setTimeout(() => {
      void cargar(rango.desde, rango.hasta, jornada);
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rangoCompartido?.desde, rangoCompartido?.hasta, rangoCompartido?.version]);

  useEffect(() => {
    if (!comandoVozPendiente) return;
    const { formato, accion, desde, hasta, jornada: jornadaVoz } = comandoVozPendiente;

    const ejecutar = async () => {
      let fechaDesde = desde;
      let fechaHasta = hasta;
      if (!fechaDesde || !fechaHasta) {
        const rango = rangoDelPeriodo(periodo, valorPeriodo);
        fechaDesde = rango.desde;
        fechaHasta = rango.hasta;
      }
      if (desde && hasta) {
        if (desde === hasta) {
          setPeriodo('dia');
          setDia(desde);
        } else if (desde.endsWith('-01') && hasta.slice(0, 7) === desde.slice(0, 7)) {
          setPeriodo('mes');
          setMes(desde.slice(0, 7));
        } else {
          setPeriodo('semana');
          setSemana(semanaIsoDesdeFecha(desde));
        }
      }
      const jornadaFiltro = jornadaVoz ?? jornada;
      setJornada(jornadaFiltro);
      const datos = await cargar(fechaDesde, fechaHasta, jornadaFiltro);
      if (accion === 'descargar' && datos && datos.cantidad > 0) {
        if (formato === 'pdf') {
          await descargarReporteProduccionPdf(fechaDesde, fechaHasta, jornadaFiltro, columnasSeleccionadas);
        } else if (formato === 'csv' || formato === 'excel') {
          await descargarReporteProduccionCsv(fechaDesde, fechaHasta, jornadaFiltro, columnasSeleccionadas);
        }
      }
      onComandoVozEjecutado?.();
    };

    const timer = window.setTimeout(() => {
      void ejecutar();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comandoVozPendiente]);

  const lotesFiltrados = useMemo(() => {
    if (!reporte?.lotes) return [];
    let items: LoteProduccion[] = [...reporte.lotes];
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase().trim();
      items = items.filter(
        (lote) =>
          String(lote.id_produccion).includes(q) ||
          lote.fecha.toLowerCase().includes(q) ||
          lote.jornada.toLowerCase().includes(q) ||
          lote.responsable.toLowerCase().includes(q) ||
          String(lote.unidades).includes(q),
      );
    }
    items.sort((a, b) => {
      let valA: string | number = a.id_produccion;
      let valB: string | number = b.id_produccion;
      if (columnaOrden === 'fecha') {
        valA = a.fecha;
        valB = b.fecha;
      } else if (columnaOrden === 'lote') {
        valA = a.id_produccion;
        valB = b.id_produccion;
      } else if (columnaOrden === 'unidades') {
        valA = a.unidades;
        valB = b.unidades;
      } else if (columnaOrden === 'responsable') {
        valA = a.responsable.toLowerCase();
        valB = b.responsable.toLowerCase();
      } else if (columnaOrden === 'costo') {
        valA = Number(a.costo);
        valB = Number(b.costo);
      }
      if (valA < valB) return direccionOrden === 'asc' ? -1 : 1;
      if (valA > valB) return direccionOrden === 'asc' ? 1 : -1;
      return 0;
    });
    return items;
  }, [reporte, busqueda, columnaOrden, direccionOrden]);

  const clavePaginacion = `${consulta?.desde}|${consulta?.hasta}|${busqueda}|${columnaOrden}|${direccionOrden}|${tamanoPagina}`;
  const [paginaLotes, setPaginaLotes] = usePagina(clavePaginacion);
  const listadoPaginado = useMemo(
    () => paginar(lotesFiltrados, paginaLotes, tamanoPagina),
    [lotesFiltrados, paginaLotes, tamanoPagina],
  );

  async function handleDescargar(tipo: 'csv' | 'excel' | 'pdf') {
    if (!consulta) return;
    if (reporte && reporte.cantidad === 0 && reporte.productos.length === 0) {
      setError(MENSAJE_SIN_DATOS);
      onAvisoSinDatos?.(MENSAJE_SIN_DATOS);
      return;
    }
    setError('');
    setDescargando(tipo);
    try {
      if (tipo === 'pdf') {
        await descargarReporteProduccionPdf(
          consulta.desde,
          consulta.hasta,
          consulta.jornada,
          columnasSeleccionadas,
        );
      } else {
        await descargarReporteProduccionCsv(
          consulta.desde,
          consulta.hasta,
          consulta.jornada,
          columnasSeleccionadas,
        );
      }
    } catch {
      setError(tipo === 'pdf' ? MENSAJE_SIN_DATOS : 'No se pudo descargar el archivo.');
    } finally {
      setDescargando('');
    }
  }

  return (
    <div id="produccion" className="scroll-mt-24 space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <EncabezadoCasoUso
          cu="CU22"
          titulo="Generar reporte de producción"
          descripcion="Cantidades horneadas en el período, comparadas con las ventas registradas."
        />
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const rango = rangoDelPeriodo(periodo, valorPeriodo);
            void cargar(rango.desde, rango.hasta, jornada);
          }}
          className="mt-4 space-y-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex rounded-xl bg-slate-100 p-1" role="group" aria-label="Granularidad de Período">
              {PERIODOS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={periodo === item.id}
                  onClick={() => setPeriodo(item.id)}
                  className={`rounded-lg px-4 py-1.5 text-xs font-bold transition-all ${
                    periodo === item.id
                      ? 'bg-amber-700 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {item.etiqueta}
                </button>
              ))}
            </div>
            <div className="text-xs font-medium text-slate-500">
              Período evaluado: <strong className="text-slate-800">{etiquetaPeriodo(periodo)}</strong>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="text-xs font-semibold text-slate-700 flex-1">
              Seleccionar {etiquetaPeriodo(periodo)}
              {periodo === 'dia' ? (
                <input
                  required
                  type="date"
                  value={dia}
                  onChange={(e) => setDia(e.target.value)}
                  className="mt-1 block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
                />
              ) : null}
              {periodo === 'semana' ? (
                <input
                  required
                  type="week"
                  value={semana}
                  onChange={(e) => setSemana(e.target.value)}
                  className="mt-1 block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
                />
              ) : null}
              {periodo === 'mes' ? (
                <input
                  required
                  type="month"
                  value={mes}
                  onChange={(e) => setMes(e.target.value)}
                  className="mt-1 block w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
                />
              ) : null}
            </label>

            <label className="text-xs font-semibold text-slate-700 sm:w-48">
              Jornada
              <select
                value={jornada}
                onChange={(e) => setJornada(e.target.value)}
                className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
              >
                <option value="">Todas las jornadas</option>
                <option value="Mañana">Solo mañana</option>
                <option value="Tarde">Solo tarde</option>
                <option value="Noche">Solo noche</option>
                <option value="unica">Jornada única</option>
              </select>
            </label>

            <button
              type="submit"
              disabled={cargando || !valorPeriodo}
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl bg-amber-700 px-5 text-sm font-bold text-white transition-colors hover:bg-amber-800 disabled:opacity-50"
            >
              {cargando ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Filter className="h-4 w-4" />}
              Actualizar Reporte
            </button>
          </div>
        </form>

        {error ? (
          <div className="mt-3 flex items-center gap-2 rounded-xl bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}
      </section>

      {reporte ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <TarjetaKpiReporte
            etiqueta="Unidades producidas"
            valor={reporte.unidades}
            detalle={`${reporte.cantidad} jornada${reporte.cantidad === 1 ? '' : 's'} · ${etiquetaJornada(consulta?.jornada ?? '')}`}
          />
          <TarjetaKpiReporte
            etiqueta="Unidades vendidas"
            valor={reporte.unidades_vendidas}
            detalle="Mismo rango de fechas"
          />
          <TarjetaKpiReporte
            etiqueta="Mermas (CU18)"
            valor={`${reporte.unidades_mermadas ?? 0} u.`}
            detalle={`Costo: ${bolivianos(reporte.costo_mermas ?? 0)}`}
          />
          <TarjetaKpiReporte
            etiqueta="Diferencia"
            valor={reporte.diferencia}
            detalle="Producido − vendido − merma"
          />
          <TarjetaKpiReporte
            etiqueta="Costo de insumos"
            valor={bolivianos(reporte.costo)}
            detalle="Costo unitario × unidades"
          />
        </div>
      ) : null}

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xl font-bold text-slate-900">
              {vistaTabla === 'lotes' ? 'Jornadas por período' : 'Producción vs ventas por producto'}
            </h3>
            <p className="mt-0.5 text-sm font-medium text-slate-500">
              Total filas: {vistaTabla === 'lotes' ? lotesFiltrados.length : reporte?.productos.length || 0}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <BotonesExportacionTabla
              onCsv={() => void handleDescargar('csv')}
              onExcel={() => void handleDescargar('excel')}
              onPdf={() => void handleDescargar('pdf')}
              descargando={descargando}
              deshabilitado={!consulta}
            />
            <div className="ml-2 border-l border-slate-200 pl-2">
              <button
                type="button"
                onClick={() => setVistaTabla(vistaTabla === 'lotes' ? 'productos' : 'lotes')}
                className="inline-flex items-center gap-1 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs font-bold text-amber-900 transition-colors hover:bg-amber-100"
              >
                <Layers className="h-3.5 w-3.5" />
                <span>{vistaTabla === 'lotes' ? 'Ver productos' : 'Ver jornadas'}</span>
              </button>
            </div>
          </div>
        </div>

        {vistaTabla === 'lotes' ? (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 md:grid-cols-4">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar lote, jornada o responsable..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-xs placeholder:text-slate-400 focus:border-amber-600 focus:outline-none"
                />
              </div>
              <select
                value={columnaOrden}
                onChange={(e) => setColumnaOrden(e.target.value as ColumnaOrden)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-amber-600 focus:outline-none"
              >
                <option value="fecha">Fecha</option>
                <option value="lote">Nº Lote</option>
                <option value="unidades">Unidades</option>
                <option value="responsable">Responsable</option>
                <option value="costo">Costo</option>
              </select>
              <select
                value={direccionOrden}
                onChange={(e) => setDireccionOrden(e.target.value === 'asc' ? 'asc' : 'desc')}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-amber-600 focus:outline-none"
              >
                <option value="desc">Descendente</option>
                <option value="asc">Ascendente</option>
              </select>
              <select
                value={tamanoPagina}
                onChange={(e) => setTamanoPagina(Number(e.target.value))}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-amber-600 focus:outline-none"
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
                className="flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900"
              >
                {mostrarColumnas ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                <span>Columnas visibles (también seleccionan qué incluir en el PDF)</span>
              </button>
              {mostrarColumnas ? (
                <div className="mt-2.5 flex flex-wrap gap-4">
                  {COLUMNAS_LOTES.map((col) => (
                    <label key={col.id} className="inline-flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={!!columnasVisibles[col.id]}
                        onChange={() =>
                          setColumnasVisibles((prev) => ({ ...prev, [col.id]: !prev[col.id] }))
                        }
                        className="rounded border-slate-300 text-amber-700 focus:ring-amber-600"
                      />
                      <span className="font-medium">{col.etiqueta}</span>
                    </label>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        <div className="mt-4 overflow-x-auto">
          {vistaTabla === 'lotes' ? (
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-indigo-900">
                  {columnasVisibles.lote ? <th className="py-3 px-3">Lote</th> : null}
                  {columnasVisibles.fecha ? <th className="py-3 px-3">Fecha</th> : null}
                  {columnasVisibles.jornada ? <th className="py-3 px-3">Jornada</th> : null}
                  {columnasVisibles.responsable ? <th className="py-3 px-3">Responsable</th> : null}
                  {columnasVisibles.unidades ? <th className="py-3 px-3 text-right">Unidades</th> : null}
                  {columnasVisibles.costo ? <th className="py-3 px-3 text-right">Costo</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cargando ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      <Loader2 className="mx-auto h-6 w-6 animate-spin text-amber-700" />
                      <p className="mt-2 text-xs">Consultando producción del período...</p>
                    </td>
                  </tr>
                ) : listadoPaginado.items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 font-medium">
                      No se encontraron jornadas para este período o criterio de búsqueda.
                    </td>
                  </tr>
                ) : (
                  listadoPaginado.items.map((lote) => (
                    <tr key={lote.id_produccion} className="hover:bg-slate-50/80 transition-colors">
                      {columnasVisibles.lote ? (
                        <td className="py-3 px-3 font-bold text-slate-900">#{lote.id_produccion}</td>
                      ) : null}
                      {columnasVisibles.fecha ? (
                        <td className="py-3 px-3 text-slate-600">{lote.fecha}</td>
                      ) : null}
                      {columnasVisibles.jornada ? (
                        <td className="py-3 px-3">
                          <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${badgeJornada(lote.jornada)}`}>
                            {lote.jornada}
                          </span>
                        </td>
                      ) : null}
                      {columnasVisibles.responsable ? (
                        <td className="py-3 px-3 text-slate-600 font-medium">{lote.responsable}</td>
                      ) : null}
                      {columnasVisibles.unidades ? (
                        <td className="py-3 px-3 text-right font-bold text-slate-900">{lote.unidades}</td>
                      ) : null}
                      {columnasVisibles.costo ? (
                        <td className="py-3 px-3 text-right font-black text-slate-900">{bolivianos(lote.costo)}</td>
                      ) : null}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          ) : (
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-amber-900">
                  <th className="py-3 px-3">Producto</th>
                  <th className="py-3 px-3 text-center">Producidas</th>
                  <th className="py-3 px-3 text-center">Vendidas</th>
                  <th className="py-3 px-3 text-center text-rose-700">Mermas</th>
                  <th className="py-3 px-3 text-center">Diferencia</th>
                  <th className="py-3 px-3 text-right">Costo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {!reporte?.productos || reporte.productos.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 font-medium">
                      No hay productos producidos ni vendidos en este período.
                    </td>
                  </tr>
                ) : (
                  reporte.productos.map((prod) => (
                    <tr key={prod.nombre} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-3 font-bold text-slate-900">{prod.nombre}</td>
                      <td className="py-3 px-3 text-center text-slate-600 font-medium">{prod.cantidad} u.</td>
                      <td className="py-3 px-3 text-center text-slate-600 font-medium">{prod.vendidas} u.</td>
                      <td className="py-3 px-3 text-center font-bold text-rose-700">{prod.mermadas ?? 0} u.</td>
                      <td className={`py-3 px-3 text-center font-bold ${prod.diferencia < 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
                        {prod.diferencia}
                      </td>
                      <td className="py-3 px-3 text-right font-bold text-slate-900">{bolivianos(prod.costo)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        {vistaTabla === 'lotes' && lotesFiltrados.length > 0 ? (
          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end border-t border-slate-100 pt-3">
            <Paginacion
              pagina={listadoPaginado.pagina}
              totalPaginas={listadoPaginado.totalPaginas}
              onCambiar={setPaginaLotes}
              deshabilitado={cargando}
              etiqueta="Paginación de jornadas del reporte"
            />
          </div>
        ) : null}
      </section>
    </div>
  );
};
