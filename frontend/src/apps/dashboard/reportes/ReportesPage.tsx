import React, { useEffect, useMemo, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  PieChart,
  Wallet,
  FileSpreadsheet,
  AlertCircle,
  ShieldCheck,
  Loader2,
  Search,
  Filter,
  Layers,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Paginacion } from '../components/Paginacion';
import { paginar, usePagina } from '../components/paginar';
import {
  consultarReporteVentas,
  descargarReporteCsv,
  descargarReportePdf,
  fechaHoy,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
  type PeriodoReporte,
  type ReporteVentas,
} from '../../../services/reporteVentasService';

interface CasoUsoReporte {
  cu: string;
  titulo: string;
  descripcion: string;
  icono: React.ElementType;
}

const REPORTES_CASOS: CasoUsoReporte[] = [
  {
    cu: 'CU21',
    titulo: 'Generar reporte de ventas',
    descripcion:
      'Reporte de las ventas realizadas en un periodo (diario, semanal o mensual), detallado por producto o por método de pago.',
    icono: TrendingUp,
  },
  {
    cu: 'CU22',
    titulo: 'Generar reporte de producción',
    descripcion:
      'Reporte de las cantidades producidas en un periodo, permitiendo comparar producción física vs ventas registradas.',
    icono: BarChart3,
  },
  {
    cu: 'CU23',
    titulo: 'Generar reporte de existencias',
    descripcion:
      'Reporte del estado y valorización de existencias de materias primas y productos terminados en mostrador.',
    icono: PieChart,
  },
  {
    cu: 'CU24',
    titulo: 'Generar reporte de compras y gastos',
    descripcion:
      'Reporte de las compras a proveedores y de los gastos operativos e inversiones realizados en un periodo.',
    icono: Wallet,
  },
  {
    cu: 'CU25',
    titulo: 'Generar reporte de resultados económicos',
    descripcion:
      'Reporte analítico que relaciona ingresos por ventas con egresos (compras, mermas y gastos), mostrando el margen neto.',
    icono: FileSpreadsheet,
  },
];

const PERIODOS: { id: PeriodoReporte; etiqueta: string }[] = [
  { id: 'dia', etiqueta: 'Día' },
  { id: 'semana', etiqueta: 'Semana' },
  { id: 'mes', etiqueta: 'Mes' },
];

interface ColumnaConfig {
  id: string;
  etiqueta: string;
  defecto: boolean;
}

const COLUMNAS_VENTAS: ColumnaConfig[] = [
  { id: 'comprobante', etiqueta: 'Nº Comprobante', defecto: true },
  { id: 'fecha', etiqueta: 'Fecha y Hora', defecto: true },
  { id: 'metodo', etiqueta: 'Método de Pago', defecto: true },
  { id: 'cajero', etiqueta: 'Cajero', defecto: true },
  { id: 'total', etiqueta: 'Total', defecto: true },
];

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

function etiquetaMetodo(metodo: string | null | undefined): string {
  if (metodo === 'efectivo') return 'Efectivo';
  if (metodo === 'stripe') return 'Tarjeta';
  return 'Efectivo y tarjeta';
}

function etiquetaPeriodo(periodo: PeriodoReporte): string {
  return PERIODOS.find((item) => item.id === periodo)?.etiqueta ?? periodo;
}

export const ReportesPage: React.FC = () => {
  // Filtros de período
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [dia, setDia] = useState(fechaHoy);
  const [semana, setSemana] = useState(semanaActual);
  const [mes, setMes] = useState(mesActual);
  const [metodo, setMetodo] = useState('');

  // Datos
  const [reporte, setReporte] = useState<ReporteVentas | null>(null);
  const [consulta, setConsulta] = useState<{
    desde: string;
    hasta: string;
    periodo: PeriodoReporte;
    metodo: string;
  } | null>(null);

  // Estados de carga y descarga
  const [cargando, setCargando] = useState(false);
  const [descargando, setDescargando] = useState<'csv' | 'excel' | 'pdf' | ''>('');
  const [error, setError] = useState('');

  // Pestaña activa dentro del reporte: Ventas individuales o Desglose por producto
  const [vistaTabla, setVistaTabla] = useState<'ventas' | 'productos'>('ventas');

  // Controles de tabla (como en las imágenes de referencia)
  const [busqueda, setBusqueda] = useState('');
  const [columnaOrden, setColumnaOrden] = useState<'fecha' | 'comprobante' | 'total' | 'cajero'>('fecha');
  const [direccionOrden, setDireccionOrden] = useState<'asc' | 'desc'>('desc');
  const [tamanoPagina, setTamanoPagina] = useState<number>(10);
  const [mostrarColumnas, setMostrarColumnas] = useState<boolean>(true);
  const [columnasVisibles, setColumnasVisibles] = useState<Record<string, boolean>>({
    comprobante: true,
    fecha: true,
    metodo: true,
    cajero: true,
    total: true,
  });

  const valorPeriodo = periodo === 'dia' ? dia : periodo === 'semana' ? semana : mes;

  // Carga inicial automática del mes actual
  useEffect(() => {
    void consultar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function consultar() {
    setError('');
    setCargando(true);
    try {
      const rango = rangoDelPeriodo(periodo, valorPeriodo);
      setConsulta({ ...rango, periodo, metodo });
      const datos = await consultarReporteVentas(rango.desde, rango.hasta, metodo);
      setReporte(datos);
    } catch {
      setReporte(null);
      setConsulta(null);
      setError('No se pudo armar el reporte de ese período.');
    } finally {
      setCargando(false);
    }
  }

  // Columnas activas para exportación (PDF / CSV / Excel)
  const columnasSeleccionadas = useMemo(() => {
    return Object.entries(columnasVisibles)
      .filter(([, visible]) => visible)
      .map(([id]) => id);
  }, [columnasVisibles]);

  function toggleColumna(id: string) {
    setColumnasVisibles((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  }

  // Filtrado y ordenamiento en cliente de las transacciones de ventas
  const ventasFiltradas = useMemo(() => {
    if (!reporte?.ventas) return [];
    let items = [...reporte.ventas];

    // Búsqueda
    if (busqueda.trim()) {
      const q = busqueda.toLowerCase().trim();
      items = items.filter(
        (v) =>
          v.numero_comprobante.toString().includes(q) ||
          v.fecha_hora.toLowerCase().includes(q) ||
          v.cajero.toLowerCase().includes(q) ||
          etiquetaMetodo(v.metodo_pago).toLowerCase().includes(q) ||
          v.total.toString().includes(q)
      );
    }

    // Ordenamiento
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
      } else if (columnaOrden === 'cajero') {
        valA = a.cajero.toLowerCase();
        valB = b.cajero.toLowerCase();
      }

      if (valA < valB) return direccionOrden === 'asc' ? -1 : 1;
      if (valA > valB) return direccionOrden === 'asc' ? 1 : -1;
      return 0;
    });

    return items;
  }, [reporte?.ventas, busqueda, columnaOrden, direccionOrden]);

  // Paginación reactiva de la tabla de ventas
  const clavePaginacion = `${consulta?.desde}|${consulta?.hasta}|${busqueda}|${columnaOrden}|${direccionOrden}|${tamanoPagina}`;
  const [paginaVentas, setPaginaVentas] = usePagina(clavePaginacion);
  const listadoPaginado = useMemo(() => {
    return paginar(ventasFiltradas, paginaVentas, tamanoPagina);
  }, [ventasFiltradas, paginaVentas, tamanoPagina]);

  // Manejadores de exportación
  async function handleDescargarCsv() {
    if (!consulta) return;
    setError('');
    setDescargando('csv');
    try {
      await descargarReporteCsv(consulta.desde, consulta.hasta, consulta.metodo, columnasSeleccionadas);
    } catch {
      setError('No se pudo descargar el archivo CSV.');
    } finally {
      setDescargando('');
    }
  }

  async function handleDescargarExcel() {
    if (!consulta) return;
    setError('');
    setDescargando('excel');
    try {
      // Exportación CSV delimitada por punto y coma con BOM para apertura nativa de Excel
      await descargarReporteCsv(consulta.desde, consulta.hasta, consulta.metodo, columnasSeleccionadas);
    } catch {
      setError('No se pudo exportar a Excel.');
    } finally {
      setDescargando('');
    }
  }

  async function handleDescargarPdf() {
    if (!consulta) return;
    setError('');
    setDescargando('pdf');
    try {
      await descargarReportePdf(consulta.desde, consulta.hasta, consulta.metodo, columnasSeleccionadas);
    } catch {
      setError('No se pudo generar el documento PDF.');
    } finally {
      setDescargando('');
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* 1. Encabezado General */}
      <div className="mostrador-aparecer">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
          Inteligencia de Negocio · Panadería Santiago
        </p>
        <div className="mt-1 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-7 w-7 text-amber-700" />
              Reportes Gerenciales y Ventas
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Consulta dinámica de ventas en tiempo real, KPIs consolidados y exportación personalizada.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
            <ShieldCheck className="h-4 w-4 text-amber-700" />
            Acceso: Propietario
          </span>
        </div>
      </div>

      {/* 2. Barra de Selección de Período y Filtros */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void consultar();
          }}
          className="space-y-4"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Botones de selección de granularidad (Día / Semana / Mes) */}
            <div className="inline-flex rounded-xl bg-slate-100 p-1" role="group" aria-label="Granularidad de Período">
              {PERIODOS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={periodo === item.id}
                  onClick={() => {
                    setPeriodo(item.id);
                  }}
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
              Método de Pago
              <select
                value={metodo}
                onChange={(e) => setMetodo(e.target.value)}
                className="mt-1 block w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:border-amber-600 focus:outline-none"
              >
                <option value="">Todos los métodos</option>
                <option value="efectivo">Solo Efectivo</option>
                <option value="stripe">Solo Tarjeta (Stripe)</option>
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

      {/* 3. Tarjetas KPIs de Resumen Financiero */}
      {reporte ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <article className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-4 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-amber-800">Total Recaudado</p>
            <p className="mt-1.5 text-2xl font-black text-slate-900">{bolivianos(reporte.total)}</p>
            <p className="mt-1 text-xs text-slate-500 font-medium">{reporte.cantidad} ventas concretadas</p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-700">En Efectivo</p>
            <p className="mt-1.5 text-2xl font-black text-slate-900">{bolivianos(reporte.efectivo)}</p>
            <p className="mt-1 text-xs text-slate-400">Ingresos directos en caja</p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-indigo-700">En Tarjeta (Stripe)</p>
            <p className="mt-1.5 text-2xl font-black text-slate-900">{bolivianos(reporte.tarjeta)}</p>
            <p className="mt-1 text-xs text-slate-400">Pagos con tarjeta confirmados</p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-600">Ticket Promedio</p>
            <p className="mt-1.5 text-2xl font-black text-slate-900">
              {reporte.cantidad > 0 ? bolivianos(Number(reporte.total) / reporte.cantidad) : 'Bs 0.00'}
            </p>
            <p className="mt-1 text-xs text-slate-400">Promedio por comprobante</p>
          </article>
        </div>
      ) : null}

      {/* 4. Tarjeta Principal de Tabla (Siguiendo la maqueta solicitada) */}
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        {/* Cabecera superior: Título y Botones CSV / Excel / PDF */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xl font-bold text-slate-900">
              {vistaTabla === 'ventas' ? 'Ventas por período' : 'Productos vendidos por período'}
            </h3>
            <p className="mt-0.5 text-sm font-medium text-slate-500">
              Total filas: {vistaTabla === 'ventas' ? ventasFiltradas.length : reporte?.productos.length || 0}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={descargando === 'csv' || !consulta}
              onClick={() => void handleDescargarCsv()}
              className="inline-flex min-h-9 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 disabled:opacity-50"
              title="Descargar en formato CSV estándar"
            >
              {descargando === 'csv' ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              CSV
            </button>

            <button
              type="button"
              disabled={descargando === 'excel' || !consulta}
              onClick={() => void handleDescargarExcel()}
              className="inline-flex min-h-9 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 disabled:opacity-50"
              title="Descargar para abrir directamente en Microsoft Excel"
            >
              {descargando === 'excel' ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              Excel
            </button>

            <button
              type="button"
              disabled={descargando === 'pdf' || !consulta}
              onClick={() => void handleDescargarPdf()}
              className="inline-flex min-h-9 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 disabled:opacity-50"
              title="Generar y descargar documento PDF formal con las columnas seleccionadas"
            >
              {descargando === 'pdf' ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              PDF
            </button>

            {/* Alternador de vista entre Detalle de Ventas y Resumen de Productos */}
            <div className="ml-2 border-l border-slate-200 pl-2">
              <button
                type="button"
                onClick={() => setVistaTabla(vistaTabla === 'ventas' ? 'productos' : 'ventas')}
                className="inline-flex items-center gap-1 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs font-bold text-amber-900 transition-colors hover:bg-amber-100"
                title="Cambiar vista entre transacciones individuales y desglose de panes"
              >
                <Layers className="h-3.5 w-3.5" />
                <span>{vistaTabla === 'ventas' ? 'Ver Productos' : 'Ver Ventas'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Fila de controles: Barra de búsqueda, Ordenar por, Dirección, y Filas por página */}
        {vistaTabla === 'ventas' ? (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 md:grid-cols-4">
              {/* Buscador */}
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar fecha, estado o total..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-9 pr-3 text-xs placeholder:text-slate-400 focus:border-amber-600 focus:outline-none"
                />
              </div>

              {/* Ordenar por columna */}
              <div>
                <select
                  value={columnaOrden}
                  onChange={(e) => setColumnaOrden(e.target.value as any)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-amber-600 focus:outline-none"
                >
                  <option value="fecha">Fecha y Hora</option>
                  <option value="comprobante">Nº Comprobante</option>
                  <option value="total">Total Recaudado</option>
                  <option value="cajero">Cajero / Usuario</option>
                </select>
              </div>

              {/* Dirección */}
              <div>
                <select
                  value={direccionOrden}
                  onChange={(e) => setDireccionOrden(e.target.value as any)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700 focus:border-amber-600 focus:outline-none"
                >
                  <option value="desc">Descendente</option>
                  <option value="asc">Ascendente</option>
                </select>
              </div>

              {/* Cantidad por página */}
              <div>
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
            </div>

            {/* Selector de Columnas Visibles (Colapsable) */}
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
                  {COLUMNAS_VENTAS.map((col) => (
                    <label key={col.id} className="inline-flex items-center gap-1.5 text-xs text-slate-700 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={!!columnasVisibles[col.id]}
                        onChange={() => toggleColumna(col.id)}
                        className="rounded border-slate-300 text-amber-700 focus:ring-amber-600"
                      />
                      <span className="font-medium">{col.id}</span>
                    </label>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {/* 5. Tabla de Datos */}
        <div className="mt-4 overflow-x-auto">
          {vistaTabla === 'ventas' ? (
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-indigo-900">
                  {columnasVisibles.comprobante ? <th className="py-3 px-3">Comprobante</th> : null}
                  {columnasVisibles.fecha ? <th className="py-3 px-3">Fecha y Hora</th> : null}
                  {columnasVisibles.metodo ? <th className="py-3 px-3">Método</th> : null}
                  {columnasVisibles.cajero ? <th className="py-3 px-3">Cajero</th> : null}
                  {columnasVisibles.total ? <th className="py-3 px-3 text-right">Total</th> : null}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cargando ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-400">
                      <Loader2 className="mx-auto h-6 w-6 animate-spin text-amber-700" />
                      <p className="mt-2 text-xs">Consultando ventas del período...</p>
                    </td>
                  </tr>
                ) : listadoPaginado.items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-500 font-medium">
                      No se encontraron ventas para este período o criterio de búsqueda.
                    </td>
                  </tr>
                ) : (
                  listadoPaginado.items.map((venta) => (
                    <tr key={venta.id_venta} className="hover:bg-slate-50/80 transition-colors">
                      {columnasVisibles.comprobante ? (
                        <td className="py-3 px-3 font-bold text-slate-900">
                          #{venta.numero_comprobante}
                        </td>
                      ) : null}

                      {columnasVisibles.fecha ? (
                        <td className="py-3 px-3 text-slate-600">
                          {venta.fecha_hora}
                        </td>
                      ) : null}

                      {columnasVisibles.metodo ? (
                        <td className="py-3 px-3">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                              venta.metodo_pago === 'stripe'
                                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            }`}
                          >
                            {etiquetaMetodo(venta.metodo_pago)}
                          </span>
                        </td>
                      ) : null}

                      {columnasVisibles.cajero ? (
                        <td className="py-3 px-3 text-slate-600 font-medium">
                          {venta.cajero}
                        </td>
                      ) : null}

                      {columnasVisibles.total ? (
                        <td className="py-3 px-3 text-right font-black text-slate-900">
                          {bolivianos(venta.total)}
                        </td>
                      ) : null}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          ) : (
            /* Vista alternativa de Productos Vendidos */
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold uppercase tracking-wider text-amber-900">
                  <th className="py-3 px-3">Producto</th>
                  <th className="py-3 px-3 text-center">Unidades Vendidas</th>
                  <th className="py-3 px-3 text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {!reporte?.productos || reporte.productos.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="py-8 text-center text-slate-500 font-medium">
                      No hay productos vendidos en este período.
                    </td>
                  </tr>
                ) : (
                  reporte.productos.map((prod) => (
                    <tr key={prod.nombre} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-3 font-bold text-slate-900">{prod.nombre}</td>
                      <td className="py-3 px-3 text-center text-slate-600 font-medium">{prod.cantidad} u.</td>
                      <td className="py-3 px-3 text-right font-bold text-slate-900">{bolivianos(prod.subtotal)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* 6. Barra de Paginación Inferior (Como en las imágenes) */}
        {vistaTabla === 'ventas' && ventasFiltradas.length > 0 ? (
          <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end border-t border-slate-100 pt-3">
            <Paginacion
              pagina={listadoPaginado.pagina}
              totalPaginas={listadoPaginado.totalPaginas}
              onCambiar={setPaginaVentas}
              deshabilitado={cargando}
              etiqueta="Paginación de ventas del reporte"
            />
          </div>
        ) : null}
      </section>

      {/* 5. Catálogo de Casos de Uso Planificados de Reportes (Ciclo 4) */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Reportes del Sistema (5 Casos de Uso)
          </h3>
          <span className="text-xs text-slate-500 font-medium">Ciclo 4 PUDS</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {REPORTES_CASOS.map((item) => {
            const Icono = item.icono;
            return (
              <div
                key={item.cu}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs transition-shadow hover:shadow-md hover:border-amber-200"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-900">
                      {item.cu}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500">
                      <AlertCircle className="h-3 w-3 text-amber-600" />
                      {item.cu === 'CU21' ? 'Activo y Funcional' : 'Planificado'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-800">
                      <Icono className="h-4 w-4" />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900">{item.titulo}</h4>
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed mb-4">{item.descripcion}</p>
                </div>

                <div className="border-t border-slate-100 pt-3">
                  <p className="text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-600">Actor autorizado:</span> Propietario
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default ReportesPage;
