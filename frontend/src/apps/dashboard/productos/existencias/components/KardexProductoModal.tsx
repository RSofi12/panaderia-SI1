import React, { useEffect, useRef, useId } from 'react';
import {
  ArrowDownLeft,
  ArrowUpRight,
  Clock,
  History,
  Package,
  X,
} from 'lucide-react';
import type { DetalleKardexProducto } from '../../../../../types/existencias';

interface Props {
  kardex: DetalleKardexProducto | null;
  cargando: boolean;
  onClose: () => void;
}

export const KardexProductoModal: React.FC<Props> = ({ kardex, cargando, onClose }) => {
  const dialogId = useId();
  const modalRef = useRef<HTMLDivElement>(null);

  // Cierre accesible con tecla Escape y foco
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!kardex && !cargando) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={`${dialogId}-title`}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div
        ref={modalRef}
        className="w-full max-w-2xl overflow-hidden bg-white border border-slate-200 shadow-2xl rounded-2xl"
      >
        {/* Cabecera del Modal */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-500/10 text-amber-700">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 id={`${dialogId}-title`} className="text-lg font-bold text-slate-900">
                Kardex de existencias: {kardex?.producto_nombre ?? 'Cargando...'}
              </h3>
              <p className="text-xs text-slate-500">
                Auditoría cronológica de ingresos por horneado y salidas por despacho
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
            aria-label="Cerrar modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Resumen del Stock Actual */}
        {kardex && (
          <div className="px-6 py-3 border-b border-slate-100 bg-amber-50/40 flex items-center justify-between text-xs sm:text-sm">
            <div className="flex items-center gap-2 text-slate-600">
              <Package className="w-4 h-4 text-amber-600" />
              <span>Stock actual disponible en mostrador:</span>
            </div>
            <div className="font-bold text-amber-900 bg-amber-100/80 px-2.5 py-1 rounded-full text-xs">
              {kardex.stock_actual} unidades
            </div>
          </div>
        )}

        {/* Cuerpo / Tabla de Movimientos */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {cargando ? (
            <div className="py-12 text-center text-slate-400 space-y-3">
              <div className="w-8 h-8 mx-auto border-3 border-amber-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm">Cargando movimientos de inventario...</p>
            </div>
          ) : !kardex?.movimientos || kardex.movimientos.length === 0 ? (
            <div className="py-12 text-center text-slate-400 space-y-2">
              <Clock className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-sm font-medium text-slate-600">Sin movimientos registrados</p>
              <p className="text-xs text-slate-400">
                Este pan aún no presenta entradas de horneado ni salidas registradas en el sistema.
              </p>
            </div>
          ) : (
            <div className="overflow-hidden border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs sm:text-sm border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Fecha y hora</th>
                    <th className="py-2.5 px-3">Tipo</th>
                    <th className="py-2.5 px-3 text-right">Cantidad</th>
                    <th className="py-2.5 px-3">Detalle / Origen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {kardex.movimientos.map((mov) => {
                    const esEntrada = mov.tipo === 'entrada';
                    const fecha = new Date(mov.fecha_hora).toLocaleString('es-BO', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    });

                    return (
                      <tr key={mov.id_movimiento} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 text-slate-500 whitespace-nowrap">{fecha}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                              esEntrada
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-rose-50 text-rose-700 border border-rose-200'
                            }`}
                          >
                            {esEntrada ? (
                              <ArrowDownLeft className="w-3 h-3" />
                            ) : (
                              <ArrowUpRight className="w-3 h-3" />
                            )}
                            {esEntrada ? 'Entrada (+)' : 'Salida (-)'}
                          </span>
                        </td>
                        <td
                          className={`py-2.5 px-3 text-right font-bold tabular-nums ${
                            esEntrada ? 'text-emerald-700' : 'text-rose-700'
                          }`}
                        >
                          {esEntrada ? `+${mov.cantidad}` : `-${mov.cantidad}`} un.
                        </td>
                        <td className="py-2.5 px-3 text-slate-600">{mov.origen_detalle}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pie del Modal */}
        <div className="flex justify-end px-6 py-3 border-t border-slate-100 bg-slate-50/50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs sm:text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-100 transition-colors cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default KardexProductoModal;
