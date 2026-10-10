import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  Eye,
  Filter,
  Layers,
  Loader2,
  Plus,
  RefreshCw,
  Wheat,
} from 'lucide-react';
import { useAuth } from '../../../../contexts/AuthContext';
import produccionService from '../../../../services/produccionService';
import type {
  JornadaProduccion,
  ProduccionFiltros,
  ProduccionRegistro,
} from '../../../../types/produccion';
import { JORNADAS_LABELS } from '../../../../types/produccion';
import RegistrarProduccionModal from './RegistrarProduccionModal';
import ModalDetalleProduccion from './components/ModalDetalleProduccion';

export const ProduccionTab: React.FC = () => {
  const { hasPermission } = useAuth();
  const puedeRegistrar = hasPermission('registrar_produccion');

  const [historial, setHistorial] = useState<ProduccionRegistro[]>([]);
  const [cargando, setCargando] = useState(true);
  const [modalRegistroAbierto, setModalRegistroAbierto] = useState(false);
  const [registroDetalleSeleccionado, setRegistroDetalleSeleccionado] =
    useState<ProduccionRegistro | null>(null);

  // Filtros
  const [filtroJornada, setFiltroJornada] = useState<JornadaProduccion | ''>('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  const [aviso, setAviso] = useState<string | null>(null);

  const cargarHistorial = async () => {
    setCargando(true);
    try {
      const filtros: ProduccionFiltros = {};
      if (filtroJornada) filtros.jornada = filtroJornada;
      if (fechaDesde) filtros.fecha_desde = fechaDesde;
      if (fechaHasta) filtros.fecha_hasta = fechaHasta;

      const data = await produccionService.listarHistorial(filtros);
      setHistorial(data);
    } catch {
      // Manejo de error al listar
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarHistorial();
  }, [filtroJornada, fechaDesde, fechaHasta]);

  const handleGuardadoExitoso = (nuevoRegistro: ProduccionRegistro) => {
    setAviso(
      `¡Producción #${nuevoRegistro.id_produccion} registrada con éxito! Se descontaron las materias primas y se actualizaron las existencias de producto terminado.`
    );
    cargarHistorial();
    setTimeout(() => setAviso(null), 6000);
  };

  // Cálculos para KPI cards
  const totalUnidadesHistorial = historial.reduce(
    (acc, h) => acc + (h.total_unidades || 0),
    0
  );
  const totalCostoHistorial = historial.reduce(
    (acc, h) => acc + parseFloat(h.costo_total || '0'),
    0
  );

  return (
    <div className="space-y-6">
      {/* Barra de título y acción principal */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-xl font-bold tracking-tight text-slate-900">
            Jornadas de Producción Diaria
          </h3>
          <p className="mt-1 text-xs text-slate-500">
            Registro del horneado de panes, explosión de recetas y descarga automática de materia prima (CU10 & CU11).
          </p>
        </div>

        {puedeRegistrar && (
          <button
            type="button"
            onClick={() => setModalRegistroAbierto(true)}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-amber-600/20 hover:from-amber-700 hover:to-amber-800 cursor-pointer transition-all"
          >
            <Plus className="h-4 w-4" />
            Registrar Producción del Día
          </button>
        )}
      </div>

      {/* Banner de éxito */}
      {aviso && (
        <div className="flex items-center gap-2.5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-900 animate-in fade-in duration-300">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{aviso}</span>
        </div>
      )}

      {/* Tarjetas KPI de resumen */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm flex items-center gap-3.5">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
            <Wheat className="h-6 w-6" />
          </span>
          <div>
            <p className="text-[11px] font-medium text-slate-500">Total unidades elaboradas</p>
            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
              {totalUnidadesHistorial.toLocaleString('es-BO')} <span className="text-xs font-normal text-slate-500">panes</span>
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm flex items-center gap-3.5">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-800">
            <Layers className="h-6 w-6" />
          </span>
          <div>
            <p className="text-[11px] font-medium text-slate-500">Jornadas registradas</p>
            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
              {historial.length} <span className="text-xs font-normal text-slate-500">lotes</span>
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm flex items-center gap-3.5">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800">
            <span className="text-base font-bold">Bs</span>
          </span>
          <div>
            <p className="text-[11px] font-medium text-slate-500">Costo acumulado de insumos</p>
            <p className="text-xl font-extrabold text-slate-900 mt-0.5">
              Bs {totalCostoHistorial.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Filtros de historial */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="font-semibold text-slate-700 flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            Filtros:
          </span>

          {/* Selector de jornada */}
          <select
            value={filtroJornada}
            onChange={(e) => setFiltroJornada(e.target.value as JornadaProduccion | '')}
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-amber-600"
          >
            <option value="">Todas las jornadas</option>
            <option value="manana">Mañana</option>
            <option value="tarde">Tarde</option>
            <option value="noche">Noche</option>
            <option value="unica">Jornada Única</option>
          </select>

          {/* Rango de fechas */}
          <div className="flex items-center gap-1.5">
            <input
              type="date"
              value={fechaDesde}
              onChange={(e) => setFechaDesde(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none"
              title="Fecha desde"
            />
            <span className="text-slate-400">a</span>
            <input
              type="date"
              value={fechaHasta}
              onChange={(e) => setFechaHasta(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-700 focus:outline-none"
              title="Fecha hasta"
            />
          </div>

          {(filtroJornada || fechaDesde || fechaHasta) && (
            <button
              type="button"
              onClick={() => {
                setFiltroJornada('');
                setFechaDesde('');
                setFechaHasta('');
              }}
              className="text-amber-800 hover:underline font-semibold cursor-pointer"
            >
              Restablecer
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={cargarHistorial}
          className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${cargando ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Tabla de Historial (CU11) */}
      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Lote #</th>
                <th className="py-3 px-4">Fecha</th>
                <th className="py-3 px-4">Jornada</th>
                <th className="py-3 px-4">Responsable</th>
                <th className="py-3 px-4 text-right">Panes producidos</th>
                <th className="py-3 px-4 text-right">Variedades</th>
                <th className="py-3 px-4 text-right">Costo Total</th>
                <th className="py-3 px-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cargando ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto text-amber-600 mb-2" />
                    Cargando historial de producciones...
                  </td>
                </tr>
              ) : historial.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <Wheat className="h-8 w-8 mx-auto text-slate-300 mb-2 stroke-[1.5]" />
                    <p className="font-medium text-slate-600">No hay producciones registradas</p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Usa el botón "Registrar Producción del Día" para ingresar el primer lote.
                    </p>
                  </td>
                </tr>
              ) : (
                historial.map((reg) => (
                  <tr key={reg.id_produccion} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">
                      #{reg.id_produccion}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      {reg.fecha}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block rounded-full bg-amber-100/80 px-2.5 py-0.5 text-[11px] font-semibold text-amber-900">
                        {JORNADAS_LABELS[reg.jornada] || reg.jornada}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {reg.usuario_nombre}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900">
                      {reg.total_unidades.toLocaleString('es-BO')} u.
                    </td>
                    <td className="py-3 px-4 text-right text-slate-600">
                      {reg.total_variedades}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-slate-900">
                      Bs {parseFloat(reg.costo_total).toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        type="button"
                        onClick={() => setRegistroDetalleSeleccionado(reg)}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100 cursor-pointer shadow-2xs"
                      >
                        <Eye className="h-3.5 w-3.5 text-slate-500" />
                        Ver detalle
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modales */}
      <RegistrarProduccionModal
        abierto={modalRegistroAbierto}
        onCerrar={() => setModalRegistroAbierto(false)}
        onGuardado={handleGuardadoExitoso}
      />

      <ModalDetalleProduccion
        registro={registroDetalleSeleccionado}
        onCerrar={() => setRegistroDetalleSeleccionado(null)}
      />
    </div>
  );
};

export default ProduccionTab;
