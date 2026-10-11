import React from 'react';
import {
  Calendar,
  Layers,
  User,
  Wheat,
  X,
} from 'lucide-react';
import type { ProduccionRegistro } from '../../../../../types/produccion';
import { JORNADAS_LABELS } from '../../../../../types/produccion';

interface ModalDetalleProduccionProps {
  registro: ProduccionRegistro | null;
  onCerrar: () => void;
}

export const ModalDetalleProduccion: React.FC<ModalDetalleProduccionProps> = ({
  registro,
  onCerrar,
}) => {
  if (!registro) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-detalle-produccion"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs"
    >
      <div className="relative flex flex-col w-full max-w-2xl max-h-[90vh] bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        {/* Encabezado */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/80 px-6 py-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-600 text-white text-xs font-bold">
                #{registro.id_produccion}
              </span>
              <h2
                id="titulo-detalle-produccion"
                className="text-lg font-bold text-slate-900"
              >
                Jornada de Producción
              </h2>
              <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
                {JORNADAS_LABELS[registro.jornada] || registro.jornada}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-500 flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5 text-slate-400" />
                {registro.fecha}
              </span>
              <span className="flex items-center gap-1">
                <User className="h-3.5 w-3.5 text-slate-400" />
                {registro.usuario_nombre}
              </span>
            </p>
          </div>

          <button
            type="button"
            onClick={onCerrar}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-200/60 hover:text-slate-700 cursor-pointer transition-colors"
            aria-label="Cerrar modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Resumen numérico */}
        <div className="grid grid-cols-3 gap-3 p-6 bg-slate-50/50 border-b border-slate-100 text-center">
          <div className="rounded-xl bg-white border border-slate-200/70 p-3 shadow-2xs">
            <p className="text-[11px] font-medium text-slate-500">Unidades producidas</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">
              {registro.total_unidades.toLocaleString('es-BO')}
            </p>
          </div>
          <div className="rounded-xl bg-white border border-slate-200/70 p-3 shadow-2xs">
            <p className="text-[11px] font-medium text-slate-500">Variedades de pan</p>
            <p className="text-xl font-bold text-slate-900 mt-0.5">
              {registro.total_variedades}
            </p>
          </div>
          <div className="rounded-xl bg-amber-50/80 border border-amber-200/70 p-3 shadow-2xs">
            <p className="text-[11px] font-medium text-amber-800">Costo total lote</p>
            <p className="text-xl font-bold text-amber-950 mt-0.5">
              Bs {parseFloat(registro.costo_total).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Cuerpo con pestañas o secciones: Productos y Consumo de Insumos */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Sección 1: Productos horneados */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5 mb-2.5">
              <Layers className="h-4 w-4 text-amber-600" />
              Panes elaborados en la jornada
            </h3>
            <div className="rounded-xl border border-slate-200 overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-[11px] font-semibold text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Producto</th>
                    <th className="py-2.5 px-3 text-right">Cantidad</th>
                    <th className="py-2.5 px-3 text-right">Costo unit.</th>
                    <th className="py-2.5 px-3 text-right">Subtotal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {registro.detalles.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-slate-400">
                        Detalle histórico resumido.
                      </td>
                    </tr>
                  ) : (
                    registro.detalles.map((d) => (
                      <tr key={d.id_detalle_produccion} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-medium text-slate-900">
                          {d.nombre_producto}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-800">
                          {d.cantidad_producida} u.
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-500">
                          Bs {parseFloat(d.costo_unitario).toFixed(2)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-mono font-semibold text-slate-900">
                          Bs {parseFloat(d.subtotal_costo).toFixed(2)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sección 2: Descuento de materias primas */}
          {registro.consumos_materia_prima && registro.consumos_materia_prima.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5 mb-2.5">
                <Wheat className="h-4 w-4 text-amber-600" />
                Insumos descontados del almacén (Movimientos de salida)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {registro.consumos_materia_prima.map((c) => (
                  <div
                    key={c.id_materia_prima}
                    className="rounded-xl border border-slate-200 bg-slate-50/70 p-2.5 text-xs"
                  >
                    <p className="text-slate-500 text-[11px] font-medium">{c.nombre_insumo}</p>
                    <p className="text-sm font-bold text-slate-900 mt-0.5">
                      -{c.cantidad_descontada.toFixed(3)} {c.unidad_medida}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Pie de modal */}
        <div className="flex justify-end border-t border-slate-100 bg-slate-50 px-6 py-3.5">
          <button
            type="button"
            onClick={onCerrar}
            className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 cursor-pointer transition-colors"
          >
            Cerrar detalle
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalDetalleProduccion;
