import React, { useCallback, useMemo, useState } from 'react';
import { AlertCircle, BarChart3, Filter, Loader2 } from 'lucide-react';
import {
  descargarAnalisisReporteCsv,
  descargarAnalisisReportePdf,
} from '../../../services/reporteVozService';
import {
  descargarReporteProduccionCsv,
  descargarReporteProduccionPdf,
} from '../../../services/reporteProduccionService';
import { descargarReporteCsv, descargarReportePdf, rangoDelPeriodo, mesActual } from '../../../services/reporteVentasService';
import type { AnalisisVozReporte, ContextoDescargaAsistente } from '../../../types/reporteVoz';
import AsistenteVozReporte from './components/AsistenteVozReporte';
import { ReporteProduccionView } from './components/ReporteProduccionView';
import { ResultadosEconomicosView } from './components/ResultadosEconomicosView';
import { SeccionReporteExistencias } from './components/SeccionReporteExistencias';
import { SeccionReporteVentas } from './components/SeccionReporteVentas';
import ReporteComprasCu24 from './ReporteComprasCu24';
import { ANCLAS_REPORTES, type RangoConsultaReportes } from './rangoConsulta';

function rangoInicial(): { desde: string; hasta: string } {
  return rangoDelPeriodo('mes', mesActual());
}

export const ReportesPage: React.FC = () => {
  const inicial = useMemo(() => rangoInicial(), []);
  const [desde, setDesde] = useState(inicial.desde);
  const [hasta, setHasta] = useState(inicial.hasta);
  const [rango, setRango] = useState<RangoConsultaReportes>({
    ...inicial,
    version: 1,
  });
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState('');
  const [metodoVoz, setMetodoVoz] = useState('');
  const [descargandoAsistente, setDescargandoAsistente] = useState('');
  const [comandoEconomicoPendiente, setComandoEconomicoPendiente] = useState<{
    formato: string;
    accion: string;
    desde?: string;
    hasta?: string;
  } | null>(null);
  const [comandoProduccionPendiente, setComandoProduccionPendiente] = useState<{
    formato: string;
    accion: string;
    desde?: string;
    hasta?: string;
    jornada?: string;
  } | null>(null);

  const registrarError = useCallback((mensaje: string) => {
    setError(mensaje);
  }, []);

  function aplicarRango(nuevoDesde: string, nuevoHasta: string) {
    setDesde(nuevoDesde);
    setHasta(nuevoHasta);
    setRango((prev) => ({
      desde: nuevoDesde,
      hasta: nuevoHasta,
      version: prev.version + 1,
    }));
  }

  function generar(event?: React.FormEvent) {
    event?.preventDefault();
    if (!desde || !hasta) {
      setError('Indicá una fecha de inicio y una fecha de fin.');
      return;
    }
    if (desde > hasta) {
      setError('La fecha DESDE no puede ser posterior a HASTA.');
      return;
    }
    setError('');
    setGenerando(true);
    aplicarRango(desde, hasta);
    window.setTimeout(() => setGenerando(false), 400);
  }

  function irASeccion(id: string) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function handleAnalisisVoz(resultado: AnalisisVozReporte): Promise<void> {
    const desdeVoz = resultado.comando.filtros.desde ?? resultado.desde;
    const hastaVoz = resultado.comando.filtros.hasta ?? resultado.hasta;
    if (desdeVoz && hastaVoz) {
      aplicarRango(desdeVoz, hastaVoz);
    }

    if (resultado.comando.caso_uso === 'CU25' || resultado.caso_uso === 'CU25') {
      setComandoEconomicoPendiente({
        formato: resultado.comando.formato,
        accion: resultado.comando.accion,
        desde: desdeVoz,
        hasta: hastaVoz,
      });
      irASeccion('resultados');
      return;
    }

    if (
      resultado.comando.caso_uso === 'CU22' ||
      resultado.caso_uso === 'CU22' ||
      resultado.tema === 'produccion'
    ) {
      setComandoProduccionPendiente({
        formato: resultado.comando.formato,
        accion: resultado.comando.accion,
        desde: desdeVoz,
        hasta: hastaVoz,
        jornada: resultado.comando.filtros.jornada || undefined,
      });
      irASeccion('produccion');
      return;
    }

    if (resultado.comando.caso_uso === 'CU24' || resultado.caso_uso === 'CU24') {
      irASeccion('compras');
      return;
    }

    if (resultado.comando.caso_uso === 'CU23' || resultado.caso_uso === 'CU23') {
      irASeccion('existencias');
      return;
    }

    setMetodoVoz(resultado.comando.filtros.metodo_pago ?? '');
    irASeccion('ventas');
  }

  async function handleDescargaAsistente(
    formato: 'pdf' | 'csv' | 'excel',
    ctx: ContextoDescargaAsistente,
  ): Promise<void> {
    setError('');
    setDescargandoAsistente(formato);
    try {
      if (ctx.exportarVentas) {
        if (formato === 'pdf') {
          await descargarReportePdf(ctx.desde, ctx.hasta, ctx.metodo, ctx.columnas);
        } else {
          await descargarReporteCsv(ctx.desde, ctx.hasta, ctx.metodo, ctx.columnas);
        }
        return;
      }
      if (ctx.exportarProduccion) {
        if (formato === 'pdf') {
          await descargarReporteProduccionPdf(ctx.desde, ctx.hasta, ctx.jornada, ctx.columnas);
        } else {
          await descargarReporteProduccionCsv(ctx.desde, ctx.hasta, ctx.jornada, ctx.columnas);
        }
        return;
      }
      const payload = {
        consulta: ctx.consulta,
        tema: ctx.tema,
        desde: ctx.desde,
        hasta: ctx.hasta,
        analisis: ctx.analisis,
      };
      if (formato === 'pdf') {
        await descargarAnalisisReportePdf(payload);
      } else {
        await descargarAnalisisReporteCsv(payload);
      }
    } catch {
      setError('No se pudo generar el archivo.');
    } finally {
      setDescargandoAsistente('');
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="mostrador-aparecer">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Reportes</h1>
        <p className="mt-1 text-sm text-slate-500">
          Ventas, producción, existencias, compras y resultados, en el orden de los casos de uso.
        </p>
      </header>

      <form
        onSubmit={generar}
        className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs sm:flex-row sm:items-end sm:gap-4"
      >
        <label className="flex-1 text-xs font-bold uppercase tracking-wider text-slate-500">
          Desde
          <input
            type="date"
            value={desde}
            onChange={(e) => setDesde(e.target.value)}
            required
            className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-medium text-slate-900 focus:border-amber-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
          />
        </label>
        <label className="flex-1 text-xs font-bold uppercase tracking-wider text-slate-500">
          Hasta
          <input
            type="date"
            value={hasta}
            min={desde}
            onChange={(e) => setHasta(e.target.value)}
            required
            className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-medium text-slate-900 focus:border-amber-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
          />
        </label>
        <button
          type="submit"
          disabled={generando}
          className="inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-xl bg-amber-700 px-5 text-sm font-bold text-white transition-colors hover:bg-amber-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:opacity-60"
        >
          {generando ? (
            <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
          ) : (
            <Filter className="h-4 w-4" aria-hidden="true" />
          )}
          Generar reportes
        </button>
      </form>

      <AsistenteVozReporte
        onAnalisis={handleAnalisisVoz}
        onDescargar={handleDescargaAsistente}
        descargando={descargandoAsistente}
      />

      {error ? (
        <p role="alert" className="flex items-center gap-2 rounded-xl bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {error}
        </p>
      ) : null}

      <nav
        aria-label="Ir a un reporte"
        className="sticky top-2 z-10 flex gap-1 overflow-x-auto rounded-2xl border border-slate-200 bg-white/95 p-1 shadow-xs backdrop-blur"
      >
        {ANCLAS_REPORTES.map((ancla) => (
          <button
            key={ancla.id}
            type="button"
            onClick={() => irASeccion(ancla.id)}
            className="inline-flex min-h-11 shrink-0 cursor-pointer items-center gap-1.5 rounded-xl px-3 text-xs font-bold text-slate-600 transition-colors hover:bg-amber-50 hover:text-amber-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600"
          >
            <BarChart3 className="h-3.5 w-3.5 text-amber-700" aria-hidden="true" />
            {ancla.etiqueta}
          </button>
        ))}
      </nav>

      <SeccionReporteVentas rango={rango} metodoVoz={metodoVoz} onError={registrarError} />

      <ReporteProduccionView
        rangoCompartido={rango}
        onAvisoSinDatos={registrarError}
        comandoVozPendiente={comandoProduccionPendiente}
        onComandoVozEjecutado={() => setComandoProduccionPendiente(null)}
      />

      <SeccionReporteExistencias />

      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <ReporteComprasCu24 rangoCompartido={rango} />
      </div>

      <ResultadosEconomicosView
        rangoCompartido={rango}
        onAvisoSinDatos={registrarError}
        comandoVozPendiente={comandoEconomicoPendiente}
        onComandoVozEjecutado={() => setComandoEconomicoPendiente(null)}
      />
    </div>
  );
};

export default ReportesPage;
