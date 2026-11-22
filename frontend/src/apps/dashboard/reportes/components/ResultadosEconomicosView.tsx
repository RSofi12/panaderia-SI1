import React, { useEffect, useState } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import {
  consultarReporteResultadosEconomicos,
  descargarReporteResultadosCsv,
  descargarReporteResultadosPdf,
} from '../../../../services/reporteResultadosEconomicosService';
import {
  fechaHoy,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
  type PeriodoReporte,
} from '../../../../services/reporteVentasService';
import type { ReporteResultadosEconomicos } from '../../../../types/reporteResultadosEconomicos';
import { inferirSelectoresPeriodo, type RangoConsultaReportes } from '../rangoConsulta';
import { EncabezadoCasoUso } from './EncabezadoCasoUso';
import { BotonesExportacionTabla } from './BotonesExportacionTabla';
import { TarjetaKpiReporte } from './TarjetaKpiReporte';

function bolivianos(valor: string | number | undefined | null): string {
  if (valor === undefined || valor === null) return 'Bs 0.00';
  return `Bs ${Number(valor).toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

interface ResultadosEconomicosViewProps {
  onAvisoSinDatos?: (mensaje: string) => void;
  comandoVozPendiente?: {
    formato: string;
    accion: string;
    desde?: string;
    hasta?: string;
  } | null;
  onComandoVozEjecutado?: () => void;
  rangoCompartido?: RangoConsultaReportes;
}

export const ResultadosEconomicosView: React.FC<ResultadosEconomicosViewProps> = ({
  onAvisoSinDatos,
  comandoVozPendiente,
  onComandoVozEjecutado,
  rangoCompartido,
}) => {
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [fechaDia, setFechaDia] = useState<string>(fechaHoy());
  const [semanaIso, setSemanaIso] = useState<string>(semanaActual());
  const [mesAno, setMesAno] = useState<string>(mesActual());

  const [reporte, setReporte] = useState<ReporteResultadosEconomicos | null>(null);
  const [cargando, setCargando] = useState<boolean>(true);
  const [descargando, setDescargando] = useState<'csv' | 'excel' | 'pdf' | ''>('');
  const [error, setError] = useState<string | null>(null);

  const valorPeriodo = periodo === 'dia' ? fechaDia : periodo === 'semana' ? semanaIso : mesAno;
  const rango = rangoDelPeriodo(periodo, valorPeriodo);

  const cargarReporte = async (desde: string, hasta: string) => {
    setCargando(true);
    setError(null);
    try {
      const data = await consultarReporteResultadosEconomicos(desde, hasta);
      setReporte(data);
      if (!data.tiene_movimientos && onAvisoSinDatos) {
        onAvisoSinDatos('No hay movimientos económicos registrados para el período seleccionado.');
      }
    } catch (err: any) {
      const msj = err?.response?.data?.detail || 'No se pudo obtener el reporte de resultados económicos.';
      setError(msj);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    if (!rangoCompartido) return;
    const sel = inferirSelectoresPeriodo(rangoCompartido.desde, rangoCompartido.hasta);
    setPeriodo(sel.periodo);
    setFechaDia(sel.dia);
    setSemanaIso(sel.semana);
    setMesAno(sel.mes);
  }, [rangoCompartido?.desde, rangoCompartido?.hasta, rangoCompartido?.version]);

  useEffect(() => {
    void cargarReporte(rango.desde, rango.hasta);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rango.desde, rango.hasta]);

  // Manejar comandos automáticos del asistente de voz
  useEffect(() => {
    if (!comandoVozPendiente) return;
    const { formato, accion, desde, hasta } = comandoVozPendiente;

    const ejecutarAccionVoz = async () => {
      const fechaDesde = desde || rango.desde;
      const fechaHasta = hasta || rango.hasta;
      await cargarReporte(fechaDesde, fechaHasta);

      if (accion === 'descargar') {
        if (formato === 'pdf') {
          await handleDescargarPdf(fechaDesde, fechaHasta);
        } else if (formato === 'csv' || formato === 'excel') {
          await handleDescargarCsv(fechaDesde, fechaHasta, formato === 'excel' ? 'excel' : 'csv');
        }
      }
      if (onComandoVozEjecutado) onComandoVozEjecutado();
    };

    ejecutarAccionVoz();
  }, [comandoVozPendiente]);

  const handleDescargarPdf = async (desde = rango.desde, hasta = rango.hasta) => {
    if (!reporte?.tiene_movimientos) {
      if (onAvisoSinDatos) onAvisoSinDatos('No hay datos para exportar en este período.');
      return;
    }
    setDescargando('pdf');
    try {
      await descargarReporteResultadosPdf(desde, hasta);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Error al exportar en PDF.');
    } finally {
      setDescargando('');
    }
  };

  const handleDescargarCsv = async (
    desde = rango.desde,
    hasta = rango.hasta,
    tipo: 'csv' | 'excel' = 'csv',
  ) => {
    if (!reporte?.tiene_movimientos) {
      if (onAvisoSinDatos) onAvisoSinDatos('No hay datos para exportar en este período.');
      return;
    }
    setDescargando(tipo);
    try {
      await descargarReporteResultadosCsv(desde, hasta);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Error al exportar en CSV/Excel.');
    } finally {
      setDescargando('');
    }
  };

  const financiero = reporte?.resumen_financiero;

  return (
    <div id="resultados" className="scroll-mt-24 space-y-6">
      {/* 1. Barra de Controles y Filtros de Período */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs">
        <EncabezadoCasoUso
          cu="CU25"
          titulo="Generar reporte de resultados económicos"
          descripcion={`Período evaluado: del ${rango.desde} al ${rango.hasta}.`}
        />

        {/* Selector de Períodos original del CU25 */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200">
            {(['dia', 'semana', 'mes'] as PeriodoReporte[]).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPeriodo(p)}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                  periodo === p
                    ? 'bg-amber-800 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {p === 'dia' ? 'Día' : p === 'semana' ? 'Semana' : 'Mes'}
              </button>
            ))}
          </div>

          {/* Input reactivo según período */}
          {periodo === 'dia' && (
            <input
              type="date"
              value={fechaDia}
              onChange={(e) => setFechaDia(e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-800"
            />
          )}
          {periodo === 'semana' && (
            <input
              type="week"
              value={semanaIso}
              onChange={(e) => setSemanaIso(e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-800"
            />
          )}
          {periodo === 'mes' && (
            <input
              type="month"
              value={mesAno}
              onChange={(e) => setMesAno(e.target.value)}
              className="rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-800"
            />
          )}

          <div className="border-l border-slate-200 pl-3">
            <BotonesExportacionTabla
              onCsv={() => void handleDescargarCsv(rango.desde, rango.hasta, 'csv')}
              onExcel={() => void handleDescargarCsv(rango.desde, rango.hasta, 'excel')}
              onPdf={() => void handleDescargarPdf()}
              descargando={descargando}
              deshabilitado={cargando || !reporte?.tiene_movimientos}
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-800 text-xs font-medium">
          <AlertCircle className="h-5 w-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <TarjetaKpiReporte
          etiqueta="Ingresos por ventas"
          valor={bolivianos(reporte?.ingresos.total)}
          detalle={`Efectivo ${bolivianos(reporte?.ingresos.efectivo)} · Tarjeta ${bolivianos(reporte?.ingresos.tarjeta)}`}
        />
        <TarjetaKpiReporte
          etiqueta="Costos directos"
          valor={bolivianos(reporte?.costos.total_costos_directos)}
          detalle={`Insumos ${bolivianos(reporte?.costos.compras_materia_prima)} · Mermas ${bolivianos(reporte?.costos.mermas_perdidas)}`}
        />
        <TarjetaKpiReporte
          etiqueta="Gastos operativos"
          valor={bolivianos(reporte?.gastos_operativos.total)}
          detalle={`${reporte?.gastos_operativos.cantidad || 0} movimientos · Inversiones ${bolivianos(reporte?.inversiones.total)}`}
        />
        <TarjetaKpiReporte
          etiqueta="Resultado neto final"
          valor={bolivianos(financiero?.utilidad_neta)}
          detalle={`Margen neto ${financiero?.margen_neto_pct ?? 0}% · Operativo ${financiero?.margen_operativo_pct ?? 0}%`}
        />
      </div>

      {/* 3. Tabla Contable: Estado de Resultados del Período */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-2xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-slate-900">
              Estado de Resultados Oficial (Esquema Financiero)
            </h3>
          </div>
          <span className="text-xs text-slate-500">Valores en Bolivianos (Bs)</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-amber-200 bg-amber-50 text-[11px] font-bold uppercase tracking-wider text-amber-900">
                <th className="py-3 px-4">Concepto Contable / Rubro</th>
                <th className="py-3 px-4 text-center">Tipo de Movimiento</th>
                <th className="py-3 px-4 text-right">Monto (Bs)</th>
                <th className="py-3 px-4 text-right">% s/ Ingresos</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cargando ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-slate-400">
                    <Loader2 className="mx-auto h-6 w-6 animate-spin text-amber-800" />
                    <p className="mt-2 text-xs">Calculando resultados económicos...</p>
                  </td>
                </tr>
              ) : !reporte?.tiene_movimientos ? (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-slate-500 font-medium">
                    No se registran movimientos comerciales o financieros en este período.
                  </td>
                </tr>
              ) : (
                reporte.estado_resultados.map((fila, idx) => {
                  const esSubtotal = fila.tipo === 'subtotal';
                  const esTotalNeto = fila.tipo === 'total_neto';
                  const esIngreso = fila.tipo === 'ingreso';

                  return (
                    <tr
                      key={idx}
                      className={`transition-colors ${
                        esTotalNeto
                          ? 'bg-amber-700 text-white font-black'
                          : esSubtotal
                          ? 'bg-amber-50 font-bold text-slate-900'
                          : 'hover:bg-slate-50/60 text-slate-700'
                      }`}
                    >
                      <td className="py-3 px-4">{fila.concepto}</td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${
                            esIngreso
                              ? 'bg-emerald-100 text-emerald-800'
                              : fila.tipo === 'costo_directo'
                              ? 'bg-amber-100 text-amber-900'
                              : fila.tipo === 'gasto_operativo'
                              ? 'bg-orange-100 text-orange-900'
                              : fila.tipo === 'inversion'
                              ? 'bg-purple-100 text-purple-900'
                              : esTotalNeto
                              ? 'bg-white/20 text-white'
                              : 'bg-slate-200 text-slate-800'
                          }`}
                        >
                          {fila.tipo.replace('_', ' ')}
                        </span>
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-mono ${
                          esTotalNeto
                            ? 'text-sm font-black text-white'
                            : esSubtotal
                            ? 'font-bold text-slate-900'
                            : esIngreso
                            ? 'font-bold text-slate-900'
                            : 'text-slate-800'
                        }`}
                      >
                        {bolivianos(fila.monto)}
                      </td>
                      <td
                        className={`py-3 px-4 text-right font-mono ${
                            esTotalNeto ? 'text-amber-100 font-bold' : 'text-slate-500'
                        }`}
                      >
                        {fila.porcentaje_ingresos}%
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* 4. Desglose de Gastos e Inversiones por Categoría (CU20) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Desglose Gastos Operativos */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h4 className="text-sm font-bold text-slate-900">
              Gastos Operativos por Categoría
            </h4>
            <span className="text-xs font-semibold text-slate-500">
              Total: {bolivianos(reporte?.gastos_operativos.total)}
            </span>
          </div>
          <div className="space-y-2">
            {!reporte?.gastos_operativos.desglose.length ? (
              <p className="py-4 text-center text-xs text-slate-400">
                Sin gastos operativos en este período.
              </p>
            ) : (
              reporte.gastos_operativos.desglose.map((g) => (
                <div
                  key={g.categoria}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors text-xs"
                >
                  <span className="font-semibold capitalize text-slate-800">
                    {g.categoria}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-400">{g.cantidad} reg.</span>
                    <span className="font-bold text-slate-900 font-mono">
                      {bolivianos(g.total)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Desglose Inversiones */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h4 className="text-sm font-bold text-slate-900">
              Inversiones de Capital por Categoría
            </h4>
            <span className="text-xs font-semibold text-slate-500">
              Total: {bolivianos(reporte?.inversiones.total)}
            </span>
          </div>
          <div className="space-y-2">
            {!reporte?.inversiones.desglose.length ? (
              <p className="py-4 text-center text-xs text-slate-400">
                Sin inversiones de capital en este período.
              </p>
            ) : (
              reporte.inversiones.desglose.map((i) => (
                <div
                  key={i.categoria}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors text-xs"
                >
                  <span className="font-semibold capitalize text-slate-800">
                    {i.categoria}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-slate-400">{i.cantidad} reg.</span>
                    <span className="font-bold text-purple-900 font-mono">
                      {bolivianos(i.total)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
