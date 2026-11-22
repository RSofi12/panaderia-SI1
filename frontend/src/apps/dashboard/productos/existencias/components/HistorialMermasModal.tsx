import React, { useState, useEffect, useMemo } from 'react';
import { X, Search, RefreshCw, AlertOctagon, TrendingDown, PackageMinus, Layers } from 'lucide-react';
import type { NotaPerdida } from '../../../../../types/existencias';
import { existenciasService } from '../../../../../services/existenciasService';

interface HistorialMermasModalProps {
  onClose: () => void;
  idProducto?: number;
}

export const HistorialMermasModal: React.FC<HistorialMermasModalProps> = ({
  onClose,
  idProducto,
}) => {
  const [mermas, setMermas] = useState<NotaPerdida[]>([]);
  const [cargando, setCargando] = useState<boolean>(true);
  const [busqueda, setBusqueda] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let activo = true;
    existenciasService
      .listarMermas(idProducto ? { id_producto: idProducto } : undefined)
      .then((data) => {
        if (activo) {
          setMermas(data);
          setCargando(false);
        }
      })
      .catch(() => {
        if (activo) {
          setError('No se pudo cargar el historial de mermas.');
          setCargando(false);
        }
      });

    return () => {
      activo = false;
    };
  }, [idProducto]);

  const handleRecargar = async () => {
    setCargando(true);
    setError(null);
    try {
      const data = await existenciasService.listarMermas(
        idProducto ? { id_producto: idProducto } : undefined
      );
      setMermas(data);
    } catch {
      setError('No se pudo cargar el historial de mermas.');
    } finally {
      setCargando(false);
    }
  };

  const mermasFiltradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return mermas;
    return mermas.filter(
      (m) =>
        m.producto_nombre?.toLowerCase().includes(q) ||
        m.categoria_nombre?.toLowerCase().includes(q) ||
        m.registrado_por?.toLowerCase().includes(q)
    );
  }, [mermas, busqueda]);

  const metricas = useMemo(() => {
    const totalNotas = mermas.length;
    const unidadesTotales = mermas.reduce((acc, m) => acc + (m.cantidad || 0), 0);
    const totalPerdida = mermas.reduce((acc, m) => acc + (Number(m.costo_total) || 0), 0);
    return {
      totalNotas,
      unidadesTotales,
      totalPerdida: totalPerdida.toFixed(2),
    };
  }, [mermas]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-mermas-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div
        className="bg-white w-full max-w-4xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-linear-to-r from-rose-50/70 to-amber-50/50">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-100 text-rose-700 shadow-2xs">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h2 id="modal-mermas-title" className="text-base font-bold text-slate-900">
                Historial de Bajas y Mermas (CU18)
              </h2>
              <p className="text-xs text-slate-500">
                Registro de notas de pérdida, descartes y salida de vitrina
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar modal"
            className="text-slate-400 hover:text-slate-700 hover:bg-slate-100 p-1.5 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 grid grid-cols-3 gap-3 border-b border-slate-100 bg-slate-50/50">
          <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-2xs flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-rose-50 text-rose-600">
              <PackageMinus className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Unidades Dadas de Baja
              </span>
              <span className="text-base font-bold text-rose-700">
                {metricas.unidadesTotales} un.
              </span>
            </div>
          </div>

          <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-2xs flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
              <TrendingDown className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Pérdida Económica
              </span>
              <span className="text-base font-bold text-slate-900">
                Bs. {metricas.totalPerdida}
              </span>
            </div>
          </div>

          <div className="p-3 bg-white rounded-xl border border-slate-200/80 shadow-2xs flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-slate-100 text-slate-600">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Notas Registradas
              </span>
              <span className="text-base font-bold text-slate-700">
                {metricas.totalNotas} registros
              </span>
            </div>
          </div>
        </div>

        <div className="px-6 py-3 border-b border-slate-100 flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por pan, categoría o responsable..."
              className="w-full pl-9 pr-3.5 py-1.5 text-xs rounded-xl border border-slate-200 bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
            />
          </div>

          <button
            type="button"
            onClick={handleRecargar}
            disabled={cargando}
            title="Refrescar datos"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${cargando ? 'animate-spin text-rose-600' : ''}`} />
            <span>Actualizar</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {cargando ? (
            <div className="py-16 text-center text-slate-400">
              <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin text-rose-500" />
              <p className="text-xs">Cargando notas de merma...</p>
            </div>
          ) : error ? (
            <div className="py-12 text-center text-rose-600 text-xs">{error}</div>
          ) : mermasFiltradas.length === 0 ? (
            <div className="py-16 text-center text-slate-400">
              <AlertOctagon className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p className="text-xs font-semibold">No se encontraron notas de baja o merma registradas.</p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-bold sticky top-0 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">ID Nota</th>
                  <th className="py-3 px-4">Fecha y Hora</th>
                  <th className="py-3 px-4">Producto</th>
                  <th className="py-3 px-4 text-center">Cant. Baja</th>
                  <th className="py-3 px-4 text-right">Costo Unit.</th>
                  <th className="py-3 px-4 text-right">Pérdida Total</th>
                  <th className="py-3 px-4">Responsable</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {mermasFiltradas.map((m) => {
                  const fechaObj = new Date(m.fecha_salida);
                  const fechaFormateada = isNaN(fechaObj.getTime())
                    ? m.fecha_salida
                    : fechaObj.toLocaleString('es-BO', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      });

                  return (
                    <tr key={m.id_nota_perdida} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-500">
                        #{m.id_nota_perdida}
                      </td>
                      <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                        {fechaFormateada}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        {m.producto_nombre}
                        <span className="block text-[10px] text-slate-400 font-normal">
                          {m.categoria_nombre}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full font-bold text-rose-700 bg-rose-50 border border-rose-200/60">
                          -{m.cantidad} un.
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-600 tabular-nums">
                        Bs. {Number(m.costo_unitario).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-rose-800 tabular-nums">
                        Bs. {Number(m.costo_total).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        <span className="font-medium text-slate-800">{m.registrado_por}</span>
                        {m.produccion_id && (
                          <span className="block text-[10px] text-slate-400 font-mono">
                            Prod #{m.produccion_id}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>Mostrando {mermasFiltradas.length} notas de merma</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};