import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Download,
  Filter,
  Loader2,
  Save,
  ShieldCheck,
  Wallet,
} from 'lucide-react';
import api from '../../../services/api';
import {
  type CierreReporteCompras,
  type PeriodoReporte,
  type ReporteCompras,
  consultarReporteCompras,
  descargarCierreComprasPdf,
  descargarReporteComprasCsv,
  descargarReporteComprasPdf,
  fechaHoy,
  guardarCierreCompras,
  listarCierresCompras,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
} from '../../../services/reporteComprasService';
import { inferirSelectoresPeriodo, type RangoConsultaReportes } from './rangoConsulta';
import { EncabezadoCasoUso } from './components/EncabezadoCasoUso';
import { BotonesExportacionTabla } from './components/BotonesExportacionTabla';
import { TarjetaKpiReporte } from './components/TarjetaKpiReporte';

interface ProveedorItem {
  id_proveedor: number;
  nombre: string;
}

interface MateriaPrimaItem {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
}

const PERIODOS: { id: PeriodoReporte; etiqueta: string }[] = [
  { id: 'dia', etiqueta: 'Día' },
  { id: 'semana', etiqueta: 'Semana' },
  { id: 'mes', etiqueta: 'Mes' },
];

function bolivianos(valor: string | number): string {
  return `Bs ${Number(valor).toFixed(2)}`;
}

function cantidadFormateada(valor: string | number, unidad: string): string {
  return `${Number(valor).toFixed(3)} ${unidad}`;
}

function etiquetaPeriodo(periodo: PeriodoReporte): string {
  return PERIODOS.find((item) => item.id === periodo)?.etiqueta ?? periodo;
}

function fechaLegible(iso: string): string {
  return new Date(iso).toLocaleString('es-BO', { dateStyle: 'medium', timeStyle: 'short' });
}

interface ReporteComprasCu24Props {
  rangoCompartido?: RangoConsultaReportes;
}

export const ReporteComprasCu24: React.FC<ReporteComprasCu24Props> = ({ rangoCompartido }) => {
  const [modo, setModo] = useState<'dinamico' | 'estatico'>('dinamico');
  const [periodo, setPeriodo] = useState<PeriodoReporte>('mes');
  const [dia, setDia] = useState(fechaHoy);
  const [semana, setSemana] = useState(semanaActual);
  const [mes, setMes] = useState(mesActual);
  const [idProveedor, setIdProveedor] = useState<number | ''>('');
  const [idMateriaPrima, setIdMateriaPrima] = useState<number | ''>('');

  const [proveedores, setProveedores] = useState<ProveedorItem[]>([]);
  const [materiasPrimas, setMateriasPrimas] = useState<MateriaPrimaItem[]>([]);

  const [reporte, setReporte] = useState<ReporteCompras | null>(null);
  const [consulta, setConsulta] = useState<{
    desde: string;
    hasta: string;
    periodo: PeriodoReporte;
  } | null>(null);

  const [cierres, setCierres] = useState<CierreReporteCompras[]>([]);
  const [cierreAbierto, setCierreAbierto] = useState<CierreReporteCompras | null>(null);

  const [cargando, setCargando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [descargando, setDescargando] = useState<'csv' | 'excel' | 'pdf' | ''>('');
  const [error, setError] = useState('');
  const [mensajeExito, setMensajeExito] = useState('');
  const [tabDetalle, setTabDetalle] = useState<'insumos' | 'proveedores'>('insumos');

  const valorPeriodo = periodo === 'dia' ? dia : periodo === 'semana' ? semana : mes;

  // Cargar catálogo de proveedores y materias primas para los selectores
  useEffect(() => {
    api
      .get<ProveedorItem[]>('/proveedores/')
      .then((res) => setProveedores(res.data))
      .catch(() => {});

    api
      .get<MateriaPrimaItem[]>('/materias-primas/')
      .then((res) => setMateriasPrimas(res.data))
      .catch(() => {});
  }, []);

  // Cargar lista de cierres al cambiar a modo estático
  useEffect(() => {
    if (modo !== 'estatico') return;
    let vigente = true;
    listarCierresCompras()
      .then((lista) => {
        if (vigente) setCierres(lista);
      })
      .catch(() => {
        if (vigente) setError('No se pudieron leer los cierres de compras guardados.');
      });
    return () => {
      vigente = false;
    };
  }, [modo]);

  async function consultar(desdeOverride?: string, hastaOverride?: string) {
    setError('');
    setMensajeExito('');
    setCargando(true);
    try {
      const rango = rangoDelPeriodo(periodo, valorPeriodo);
      const desde = desdeOverride ?? rango.desde;
      const hasta = hastaOverride ?? rango.hasta;
      const resultado = await consultarReporteCompras(
        desde,
        hasta,
        idProveedor,
        idMateriaPrima,
      );
      setReporte(resultado);
      setConsulta({ desde, hasta, periodo });
    } catch {
      setError('No se pudo calcular el reporte de compras.');
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    if (!rangoCompartido) return;
    const sel = inferirSelectoresPeriodo(rangoCompartido.desde, rangoCompartido.hasta);
    setPeriodo(sel.periodo);
    setDia(sel.dia);
    setSemana(sel.semana);
    setMes(sel.mes);
    void consultar(rangoCompartido.desde, rangoCompartido.hasta);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rangoCompartido?.desde, rangoCompartido?.hasta, rangoCompartido?.version]);

  async function guardar() {
    if (!consulta) return;
    setError('');
    setMensajeExito('');
    setGuardando(true);
    try {
      const guardado = await guardarCierreCompras({
        desde: consulta.desde,
        hasta: consulta.hasta,
        periodo: consulta.periodo,
        id_proveedor: idProveedor,
      });
      setCierres((prev) => [guardado, ...prev]);
      setCierreAbierto(guardado);
      setModo('estatico');
      setMensajeExito('¡Cierre estático de compras congelado y auditado con éxito!');
    } catch {
      setError('No se pudo guardar el cierre de compras.');
    } finally {
      setGuardando(false);
    }
  }

  async function exportar(tipo: 'csv' | 'excel' | 'pdf') {
    if (!consulta) return;
    setError('');
    setDescargando(tipo);
    try {
      if (tipo === 'pdf') {
        await descargarReporteComprasPdf(
          consulta.desde,
          consulta.hasta,
          idProveedor,
          idMateriaPrima,
        );
      } else {
        await descargarReporteComprasCsv(
          consulta.desde,
          consulta.hasta,
          idProveedor,
          idMateriaPrima,
        );
      }
    } catch {
      setError(tipo === 'pdf' ? 'No se pudo descargar el PDF.' : 'No se pudo descargar el archivo.');
    } finally {
      setDescargando('');
    }
  }

  async function exportarPdf(idCierre: number) {
    setError('');
    setDescargando('pdf');
    try {
      await descargarCierreComprasPdf(idCierre);
    } catch {
      setError('No se pudo descargar el PDF del cierre.');
    } finally {
      setDescargando('');
    }
  }

  return (
    <div id="compras" className="scroll-mt-24 space-y-6">
      {/* Selector de Modo: Dinámico vs Estático */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4">
        <EncabezadoCasoUso
          cu="CU24"
          titulo="Generar reporte de compras y gastos"
          descripcion="Compras a proveedores, insumos adquiridos y cierres estáticos del período."
        />

        <div className="flex rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => setModo('dinamico')}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
              modo === 'dinamico'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Reporte en Vivo (Dinámico)
          </button>
          <button
            type="button"
            onClick={() => setModo('estatico')}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
              modo === 'estatico'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Cierres Congelados (Historial)
          </button>
        </div>
      </div>

      {/* Alertas */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl bg-rose-50 p-4 text-xs font-semibold text-rose-800 border border-rose-200">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}
      {mensajeExito && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 border border-emerald-200">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>{mensajeExito}</span>
        </div>
      )}

      {/* MODO DINÁMICO */}
      {modo === 'dinamico' && (
        <div className="space-y-6">
          {/* Panel de Filtros */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
              <Filter className="h-4 w-4 text-amber-600" />
              <span>Criterios de Consulta y Filtros</span>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* Periodicidad */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Periodicidad</label>
                <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1">
                  {PERIODOS.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setPeriodo(item.id)}
                      className={`rounded-lg py-1.5 text-xs font-bold transition-all ${
                        periodo === item.id
                          ? 'bg-amber-600 text-white shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      {item.etiqueta}
                    </button>
                  ))}
                </div>
              </div>

              {/* Selector de Fecha */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  {periodo === 'dia' ? 'Fecha específica' : periodo === 'semana' ? 'Semana del año' : 'Mes contable'}
                </label>
                {periodo === 'dia' && (
                  <input
                    type="date"
                    value={dia}
                    onChange={(e) => setDia(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs focus:border-amber-600 focus:outline-hidden"
                  />
                )}
                {periodo === 'semana' && (
                  <input
                    type="week"
                    value={semana}
                    onChange={(e) => setSemana(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs focus:border-amber-600 focus:outline-hidden"
                  />
                )}
                {periodo === 'mes' && (
                  <input
                    type="month"
                    value={mes}
                    onChange={(e) => setMes(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs focus:border-amber-600 focus:outline-hidden"
                  />
                )}
              </div>

              {/* Filtro por Proveedor */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Proveedor (Opcional)</label>
                <select
                  value={idProveedor}
                  onChange={(e) => setIdProveedor(e.target.value ? Number(e.target.value) : '')}
                  className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs focus:border-amber-600 focus:outline-hidden"
                >
                  <option value="">Todos los proveedores</option>
                  {proveedores.map((p) => (
                    <option key={p.id_proveedor} value={p.id_proveedor}>
                      {p.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* Filtro por Materia Prima */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Materia Prima (Opcional)</label>
                <select
                  value={idMateriaPrima}
                  onChange={(e) => setIdMateriaPrima(e.target.value ? Number(e.target.value) : '')}
                  className="w-full rounded-xl border border-slate-200 px-3 py-1.5 text-xs focus:border-amber-600 focus:outline-hidden"
                >
                  <option value="">Todas las materias primas</option>
                  {materiasPrimas.map((m) => (
                    <option key={m.id_materia_prima} value={m.id_materia_prima}>
                      {m.nombre} ({m.unidad_medida})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => void consultar()}
                disabled={cargando}
                className="inline-flex items-center gap-2 rounded-xl bg-amber-700 px-5 py-2 text-xs font-bold text-white shadow-xs transition hover:bg-amber-800 disabled:opacity-50"
              >
                {cargando ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wallet className="h-4 w-4" />}
                Consultar Compras
              </button>
            </div>
          </div>

          {/* Resultados Dinámicos */}
          {reporte && (
            <div className="space-y-6">
              {/* Tarjetas KPI */}
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <TarjetaKpiReporte
                  etiqueta="Total invertido"
                  valor={bolivianos(reporte.total)}
                  detalle={`Del ${reporte.desde} al ${reporte.hasta}`}
                />
                <TarjetaKpiReporte
                  etiqueta="Órdenes de compra"
                  valor={reporte.cantidad}
                  detalle="Transacciones efectuadas"
                />
                <TarjetaKpiReporte
                  etiqueta="Proveedores activos"
                  valor={reporte.proveedores.length}
                  detalle="Con compras en el periodo"
                />
                <TarjetaKpiReporte
                  etiqueta="Variedad de insumos"
                  valor={reporte.insumos.length}
                  detalle="Materias primas adquiridas"
                />
              </div>

              {/* Botones de Acción */}
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-slate-50 p-4 border border-slate-200">
                <span className="text-xs font-semibold text-slate-600">
                  Acciones para el periodo ({etiquetaPeriodo(consulta?.periodo || 'mes')}):
                </span>

                <div className="flex flex-wrap items-center gap-2">
                  <BotonesExportacionTabla
                    onCsv={() => void exportar('csv')}
                    onExcel={() => void exportar('excel')}
                    onPdf={() => void exportar('pdf')}
                    descargando={descargando}
                    deshabilitado={reporte.cantidad === 0}
                  />

                  <button
                    type="button"
                    onClick={guardar}
                    disabled={guardando || reporte.cantidad === 0}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-amber-700 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-amber-800 disabled:opacity-50"
                  >
                    {guardando ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Save className="h-3.5 w-3.5" />
                    )}
                    Congelar Cierre Estático
                  </button>
                </div>
              </div>

              {/* Tablas de Desglose: Insumos y Proveedores */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setTabDetalle('insumos')}
                      className={`text-xs font-bold uppercase tracking-wider pb-1 transition-all ${
                        tabDetalle === 'insumos'
                          ? 'border-b-2 border-amber-600 text-amber-900'
                          : 'text-slate-400 hover:text-slate-600'
                      }`}
                    >
                      Detalle por Materia Prima ({reporte.insumos.length})
                    </button>
                    <span className="text-slate-300">|</span>
                    <button
                      type="button"
                      onClick={() => setTabDetalle('proveedores')}
                      className={`text-xs font-bold uppercase tracking-wider pb-1 transition-all ${
                        tabDetalle === 'proveedores'
                          ? 'border-b-2 border-amber-600 text-amber-900'
                          : 'text-slate-400 hover:text-slate-600'
                      }`}
                    >
                      Desglose por Proveedor ({reporte.proveedores.length})
                    </button>
                  </div>
                </div>

                {tabDetalle === 'insumos' && (
                  <div className="overflow-x-auto">
                    {reporte.insumos.length === 0 ? (
                      <p className="text-center py-6 text-xs text-slate-500">
                        No se registraron compras de materias primas en este periodo.
                      </p>
                    ) : (
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase">
                            <th className="py-2.5">Materia Prima</th>
                            <th className="py-2.5 text-right">Cantidad Adquirida</th>
                            <th className="py-2.5 text-right">Subtotal Invertido</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {reporte.insumos.map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/70">
                              <td className="py-2.5 font-bold text-slate-800">{item.nombre}</td>
                              <td className="py-2.5 text-right font-medium text-slate-600">
                                {cantidadFormateada(item.cantidad, item.unidad_medida)}
                              </td>
                              <td className="py-2.5 text-right font-bold text-slate-900">
                                {bolivianos(item.subtotal)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}

                {tabDetalle === 'proveedores' && (
                  <div className="overflow-x-auto">
                    {reporte.proveedores.length === 0 ? (
                      <p className="text-center py-6 text-xs text-slate-500">
                        No se registraron compras a proveedores en este periodo.
                      </p>
                    ) : (
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase">
                            <th className="py-2.5">Proveedor</th>
                            <th className="py-2.5 text-center">Compras Registradas</th>
                            <th className="py-2.5 text-right">Total Facturado</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {reporte.proveedores.map((prov, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/70">
                              <td className="py-2.5 font-bold text-slate-800">{prov.nombre}</td>
                              <td className="py-2.5 text-center font-medium text-slate-600">
                                {prov.cantidad_compras} compras
                              </td>
                              <td className="py-2.5 text-right font-bold text-slate-900">
                                {bolivianos(prov.total)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* MODO ESTÁTICO (HISTORIAL DE CIERRES) */}
      {modo === 'estatico' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Cierres de Compras Congelados en Base de Datos
            </h3>
            <span className="text-[11px] text-slate-400">Total guardados: {cierres.length}</span>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Lista lateral de cierres */}
            <div className="space-y-2 lg:col-span-1">
              {cierres.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 p-8 text-center text-xs text-slate-500">
                  Aún no se ha guardado ningún cierre estático de compras.
                </div>
              ) : (
                cierres.map((c) => (
                  <button
                    key={c.id_cierre}
                    type="button"
                    onClick={() => setCierreAbierto(c)}
                    className={`w-full text-left rounded-2xl border p-4 transition-all shadow-xs ${
                      cierreAbierto?.id_cierre === c.id_cierre
                        ? 'border-amber-600 bg-amber-50/60 ring-2 ring-amber-600/10'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[11px] font-bold text-amber-900 mb-1">
                      <span className="uppercase">Cierre {c.periodo} #{c.id_cierre}</span>
                      <span>{bolivianos(c.total)}</span>
                    </div>
                    <p className="text-xs font-semibold text-slate-800">
                      Del {c.desde} al {c.hasta}
                    </p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      {c.cantidad} compras · {c.proveedor || 'Todos los proveedores'}
                    </p>
                  </button>
                ))
              )}
            </div>

            {/* Detalle del cierre abierto */}
            <div className="lg:col-span-2">
              {cierreAbierto ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
                    <div>
                      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-200">
                        <ShieldCheck className="h-3 w-3" /> Cierre Congelado #{cierreAbierto.id_cierre}
                      </span>
                      <h4 className="text-sm font-bold text-slate-900 mt-1">
                        Periodo {cierreAbierto.periodo.toUpperCase()}: {cierreAbierto.desde} al {cierreAbierto.hasta}
                      </h4>
                      <p className="text-[11px] text-slate-400">
                        Guardado el {fechaLegible(cierreAbierto.fecha_generacion)} por {cierreAbierto.generado_por}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => exportarPdf(cierreAbierto.id_cierre)}
                      disabled={descargando === 'pdf'}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-amber-700 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-amber-800 disabled:opacity-50"
                    >
                      {descargando === 'pdf' ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Download className="h-3.5 w-3.5" />
                      )}
                      Descargar PDF
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Total Gastado</p>
                      <p className="text-lg font-black text-slate-900 mt-0.5">{bolivianos(cierreAbierto.total)}</p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Compras</p>
                      <p className="text-lg font-black text-slate-900 mt-0.5">{cierreAbierto.cantidad}</p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3 col-span-2 sm:col-span-1">
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Proveedor</p>
                      <p className="text-xs font-bold text-slate-900 mt-1 truncate">
                        {cierreAbierto.proveedor || 'Todos'}
                      </p>
                    </div>
                  </div>

                  {/* Tabla de líneas inmutables */}
                  <div>
                    <h5 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                      Insumos Congelados ({cierreAbierto.insumos.length})
                    </h5>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-100 text-slate-400 font-bold uppercase">
                            <th className="py-2">Materia Prima</th>
                            <th className="py-2 text-right">Cantidad</th>
                            <th className="py-2 text-right">Subtotal</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {cierreAbierto.insumos.map((linea, idx) => (
                            <tr key={idx}>
                              <td className="py-2 font-medium text-slate-800">{linea.nombre}</td>
                              <td className="py-2 text-right text-slate-600">
                                {cantidadFormateada(linea.cantidad, linea.unidad_medida)}
                              </td>
                              <td className="py-2 text-right font-bold text-slate-900">
                                {bolivianos(linea.subtotal)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 italic text-center pt-2">
                    * Estos valores representan un estado contable histórico que no se recalcula si se modifican compras futuras.
                  </p>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-300 p-12 text-center text-xs text-slate-500">
                  Selecciona un cierre de la lista izquierda para consultar su detalle y descargar el reporte formal en PDF.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReporteComprasCu24;
