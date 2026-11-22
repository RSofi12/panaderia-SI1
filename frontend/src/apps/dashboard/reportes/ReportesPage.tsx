import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  PieChart,
  Wallet,
  FileSpreadsheet,
  Sparkles,
  AlertCircle,
  ShieldCheck,
  Download,
  Loader2,
  Save,
} from 'lucide-react';
import {
  consultarReporteVentas,
  descargarCierrePdf,
  descargarReporteCsv,
  fechaHoy,
  guardarCierreVentas,
  listarCierresVentas,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
  type CierreReporteVentas,
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

function bolivianos(valor: string): string {
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

function fechaLegible(iso: string): string {
  return new Date(iso).toLocaleString('es-BO', { dateStyle: 'medium', timeStyle: 'short' });
}

function CifrasReporte({ reporte }: { reporte: ReporteVentas }) {
  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500">
        Del {reporte.desde} al {reporte.hasta}
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <article className="rounded-2xl bg-amber-50 p-4">
          <p className="text-xs font-semibold uppercase text-amber-800">Total</p>
          <p className="mt-1 text-2xl font-black">{bolivianos(reporte.total)}</p>
          <p className="text-xs text-slate-500">{reporte.cantidad} ventas</p>
        </article>
        <article className="rounded-2xl bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Efectivo</p>
          <p className="mt-1 text-2xl font-black">{bolivianos(reporte.efectivo)}</p>
        </article>
        <article className="rounded-2xl bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase text-slate-500">Tarjeta</p>
          <p className="mt-1 text-2xl font-black">{bolivianos(reporte.tarjeta)}</p>
        </article>
      </div>
      {reporte.productos.length === 0 ? (
        <p className="text-sm text-slate-500">Ese periodo no tiene ventas.</p>
      ) : (
        <ul className="divide-y divide-slate-100 text-sm">
          {reporte.productos.map((producto) => (
            <li key={producto.nombre} className="flex items-center justify-between py-2">
              <span className="font-semibold text-slate-800">{producto.nombre}</span>
              <span className="text-slate-500">
                {producto.cantidad} u · {bolivianos(producto.subtotal)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ReporteVentasCu21() {
  const [modo, setModo] = useState<'dinamico' | 'estatico'>('dinamico');
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [dia, setDia] = useState(fechaHoy);
  const [semana, setSemana] = useState(semanaActual);
  const [mes, setMes] = useState(mesActual);
  const [metodo, setMetodo] = useState('');
  const [reporte, setReporte] = useState<ReporteVentas | null>(null);
  const [consulta, setConsulta] = useState<{
    desde: string;
    hasta: string;
    periodo: PeriodoReporte;
    metodo: string;
  } | null>(null);
  const [cierres, setCierres] = useState<CierreReporteVentas[]>([]);
  const [cierreAbierto, setCierreAbierto] = useState<CierreReporteVentas | null>(null);
  const [cargando, setCargando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [descargando, setDescargando] = useState<'csv' | 'pdf' | ''>('');
  const [error, setError] = useState('');

  const valorPeriodo = periodo === 'dia' ? dia : periodo === 'semana' ? semana : mes;

  useEffect(() => {
    if (modo !== 'estatico') return;
    let vigente = true;
    listarCierresVentas()
      .then((lista) => {
        if (vigente) setCierres(lista);
      })
      .catch(() => {
        if (vigente) setError('No se pudieron leer los cierres guardados.');
      });
    return () => {
      vigente = false;
    };
  }, [modo]);

  async function consultar() {
    setError('');
    setCargando(true);
    try {
      const rango = rangoDelPeriodo(periodo, valorPeriodo);
      setConsulta({ ...rango, periodo, metodo });
      setReporte(await consultarReporteVentas(rango.desde, rango.hasta, metodo));
    } catch {
      setReporte(null);
      setConsulta(null);
      setError('No se pudo armar el reporte de ese periodo.');
    } finally {
      setCargando(false);
    }
  }

  async function guardar() {
    setError('');
    setGuardando(true);
    try {
      if (!consulta) return;
      const cierre = await guardarCierreVentas({
        desde: consulta.desde,
        hasta: consulta.hasta,
        periodo: consulta.periodo,
        metodoPago: consulta.metodo,
      });
      setCierreAbierto(cierre);
      setCierres((lista) => [cierre, ...lista.filter((item) => item.id_cierre !== cierre.id_cierre)]);
      setModo('estatico');
    } catch {
      setError('No se pudo guardar el cierre.');
    } finally {
      setGuardando(false);
    }
  }

  async function descargarCsv() {
    if (!consulta) return;
    setError('');
    setDescargando('csv');
    try {
      await descargarReporteCsv(consulta.desde, consulta.hasta, consulta.metodo);
    } catch {
      setError('No se pudo descargar el CSV.');
    } finally {
      setDescargando('');
    }
  }

  async function descargarPdf(idCierre: number) {
    setError('');
    setDescargando('pdf');
    try {
      await descargarCierrePdf(idCierre);
    } catch {
      setError('No se pudo descargar el PDF.');
    } finally {
      setDescargando('');
    }
  }

  return (
    <section className="rounded-3xl border border-amber-200 bg-white p-6 shadow-sm">
      <span className="inline-flex rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-900">
        CU21
      </span>
      <h3 className="mt-3 text-lg font-bold text-slate-900">Reporte de ventas</h3>
      <p className="mt-1 max-w-2xl text-sm text-slate-600">
        El dinámico vuelve a sumar las ventas del periodo. El estático guarda esa suma y ya no cambia.
      </p>
      <div className="mt-4 inline-flex rounded-xl bg-slate-100 p-1" role="group" aria-label="Tipo de reporte">
        <button
          type="button"
          aria-pressed={modo === 'dinamico'}
          onClick={() => setModo('dinamico')}
          className={`rounded-lg px-4 py-2 text-sm font-bold ${modo === 'dinamico' ? 'bg-white text-amber-900 shadow-sm' : 'text-slate-600'}`}
        >
          Dinámico
        </button>
        <button
          type="button"
          aria-pressed={modo === 'estatico'}
          onClick={() => setModo('estatico')}
          className={`rounded-lg px-4 py-2 text-sm font-bold ${modo === 'estatico' ? 'bg-white text-amber-900 shadow-sm' : 'text-slate-600'}`}
        >
          Estático
        </button>
      </div>

      {modo === 'dinamico' ? (
        <form
          className="mt-4 space-y-4"
          onSubmit={(evento) => {
            evento.preventDefault();
            void consultar();
          }}
        >
          <div className="flex flex-wrap gap-2" role="group" aria-label="Periodo">
            {PERIODOS.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={periodo === item.id}
                onClick={() => {
                  setPeriodo(item.id);
                  setReporte(null);
                  setConsulta(null);
                }}
                className={`rounded-full px-3 py-1 text-xs font-bold ${periodo === item.id ? 'bg-amber-700 text-white' : 'bg-slate-100 text-slate-600'}`}
              >
                {item.etiqueta}
              </button>
            ))}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <label className="text-sm font-semibold text-slate-700">
              {etiquetaPeriodo(periodo)}
              {periodo === 'dia' ? (
                <input required type="date" value={dia} onChange={(evento) => { setDia(evento.target.value); setReporte(null); setConsulta(null); }} className="mt-1 block rounded-xl border border-slate-200 px-3 py-2" />
              ) : null}
              {periodo === 'semana' ? (
                <input required type="week" value={semana} onChange={(evento) => { setSemana(evento.target.value); setReporte(null); setConsulta(null); }} className="mt-1 block rounded-xl border border-slate-200 px-3 py-2" />
              ) : null}
              {periodo === 'mes' ? (
                <input required type="month" value={mes} onChange={(evento) => { setMes(evento.target.value); setReporte(null); setConsulta(null); }} className="mt-1 block rounded-xl border border-slate-200 px-3 py-2" />
              ) : null}
            </label>
            <label className="text-sm font-semibold text-slate-700">
              Método de pago
              <select value={metodo} onChange={(evento) => { setMetodo(evento.target.value); setReporte(null); setConsulta(null); }} className="mt-1 block rounded-xl border border-slate-200 px-3 py-2">
                <option value="">Todos</option>
                <option value="efectivo">Efectivo</option>
                <option value="stripe">Tarjeta</option>
              </select>
            </label>
            <button
              type="submit"
              disabled={cargando || !valorPeriodo}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-amber-700 px-4 text-sm font-bold text-white disabled:opacity-50"
            >
              {cargando ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
              Consultar
            </button>
          </div>
        </form>
      ) : null}

      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}

      {modo === 'dinamico' && reporte ? (
        <div className="mt-5 space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
            Dinámico · se vuelve a calcular · {etiquetaMetodo(metodo)}
          </p>
          <CifrasReporte reporte={reporte} />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={descargando === 'csv' || !consulta}
              onClick={() => void descargarCsv()}
              className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-slate-900 px-4 text-sm font-bold text-white disabled:opacity-50"
            >
              {descargando === 'csv' ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Download className="h-4 w-4" aria-hidden="true" />}
              Descargar CSV
            </button>
            <button
              type="button"
              disabled={guardando || !consulta}
              onClick={() => void guardar()}
              className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-amber-300 px-4 text-sm font-bold text-amber-900 disabled:opacity-50"
            >
              {guardando ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Save className="h-4 w-4" aria-hidden="true" />}
              Guardar cierre estático
            </button>
          </div>
          <p className="text-xs text-slate-500">El CSV se arma al descargarlo, con las ventas de ese momento.</p>
        </div>
      ) : null}

      {modo === 'estatico' ? (
        <div className="mt-5 space-y-4">
          {cierres.length === 0 ? (
            <p className="text-sm text-slate-500">Todavía no hay cierres. Consulta un periodo y guárdalo.</p>
          ) : (
            <ul className="space-y-2">
              {cierres.map((cierre) => (
                <li key={cierre.id_cierre}>
                  <button
                    type="button"
                    onClick={() => setCierreAbierto(cierre)}
                    className={`flex w-full items-center justify-between rounded-xl border px-4 py-3 text-left text-sm ${cierreAbierto?.id_cierre === cierre.id_cierre ? 'border-amber-400 bg-amber-50' : 'border-slate-200'}`}
                  >
                    <span className="font-semibold text-slate-800">
                      {etiquetaPeriodo(cierre.periodo)} · {cierre.desde} a {cierre.hasta}
                    </span>
                    <span className="text-slate-500">{bolivianos(cierre.total)}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {cierreAbierto ? (
            <div className="space-y-3 rounded-2xl border border-slate-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">
                Estático · congelado el {fechaLegible(cierreAbierto.fecha_generacion)} por {cierreAbierto.generado_por}
              </p>
              <p className="text-xs text-slate-500">{etiquetaMetodo(cierreAbierto.metodo_pago)}</p>
              <CifrasReporte reporte={cierreAbierto} />
              <button
                type="button"
                disabled={descargando === 'pdf'}
                onClick={() => void descargarPdf(cierreAbierto.id_cierre)}
                className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-slate-900 px-4 text-sm font-bold text-white disabled:opacity-50"
              >
                {descargando === 'pdf' ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Download className="h-4 w-4" aria-hidden="true" />}
                Descargar PDF
              </button>
              <p className="text-xs text-slate-500">El PDF usa la copia guardada. No vuelve a sumar las ventas.</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

export const ReportesPage: React.FC = () => {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Encabezado General */}
      <div className="mostrador-aparecer">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-700">
          Reportes y Estadísticas · Ciclo 4 (CU21–CU25)
        </p>
        <div className="mt-1 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-7 w-7 text-amber-700" />
              Reportes Gerenciales
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Métricas consolidadas del negocio, balance financiero y comparativas de rendimiento.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
            <Sparkles className="h-3.5 w-3.5 text-amber-600" />
            Módulo en Progreso · Ciclo 4
          </span>
        </div>
      </div>

      {/* Banner Informativo */}
      <section className="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50 via-orange-50/50 to-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-700 text-white shadow-md shadow-amber-700/20">
              <BarChart3 className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Módulo de Inteligencia de Negocio y Reportes
              </h3>
              <p className="mt-1 text-sm text-slate-600 leading-relaxed max-w-2xl">
                Diseñado exclusivamente para el <strong className="text-slate-800">Propietario</strong>,
                este módulo consolidará la información generada en Compras, Producción, Inventario y Ventas para
                ofrecer reportes dinámicos, exportación a PDF/Excel y análisis de rentabilidad.
              </p>
            </div>
          </div>
          <div className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-amber-300 bg-white px-4 py-2 text-xs font-semibold text-amber-900 shadow-sm">
            <ShieldCheck className="h-4 w-4 text-amber-700" />
            <span>Acceso: Propietario</span>
          </div>
        </div>
      </section>

      <ReporteVentasCu21 />

      {/* Casos de Uso Planificados */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Reportes Planificados (5 Casos de Uso)
          </h3>
          <span className="text-xs text-slate-500 font-medium">Ciclo 4 PUDS</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {REPORTES_CASOS.map((item) => {
            const Icono = item.icono;
            return (
              <div
                key={item.cu}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-md hover:border-amber-200"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-900">
                      {item.cu}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500">
                      <AlertCircle className="h-3 w-3 text-amber-600" />
                      {item.cu === 'CU21' ? 'Disponible' : 'Planificado'}
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
                    <span className="font-semibold text-slate-600">Actor:</span> Propietario
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
