import React from 'react';
import { Ban, Calendar, CheckCircle2, DollarSign, FileText, Receipt, Tag, User } from 'lucide-react';
import type { MovimientoEconomico } from '../../../../types/gasto';
import ModalLectura from '../../components/ModalLectura';
import { formatearBs } from '../../productos/precios';

interface DetalleGastoModalProps {
  movimiento: MovimientoEconomico;
  onClose: () => void;
}

const formatoFechaLargo = new Intl.DateTimeFormat('es-BO', {
  dateStyle: 'full',
  timeStyle: 'short',
});

/**
 * DetalleGastoModal
 * Diálogo de solo lectura para visualizar la ficha completa de un egreso (gasto operativo o inversión).
 * Utiliza la plantilla arquitectónica ModalLectura.
 */
export const DetalleGastoModal: React.FC<DetalleGastoModalProps> = ({ movimiento, onClose }) => {
  const esInversion = movimiento.tipo === 'inversion';
  const fechaFormateada = formatoFechaLargo.format(new Date(movimiento.fecha_hora));

  return (
    <ModalLectura
      titulo={esInversion ? 'Detalle de inversión' : 'Detalle de gasto operativo'}
      subtitulo={`Movimiento #${movimiento.id_movimiento} · CU20`}
      iconoCabecera={
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-xl shadow-xs ${
            movimiento.anulado
              ? 'bg-slate-100 text-slate-500'
              : esInversion
                ? 'bg-indigo-100 text-indigo-700'
                : 'bg-rose-100 text-rose-700'
          }`}
        >
          <Receipt className="h-5 w-5" />
        </div>
      }
      onCerrar={onClose}
      ancho="md"
      pie={
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 cursor-pointer"
          >
            Cerrar detalle
          </button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Cabecera de estado y monto */}
        <div
          className={`flex items-center justify-between rounded-2xl border p-4 ${
            movimiento.anulado
              ? 'border-slate-200 bg-slate-50/80 text-slate-500'
              : esInversion
                ? 'border-indigo-100 bg-indigo-50/50'
                : 'border-rose-100 bg-rose-50/50'
          }`}
        >
          <div>
            <div className="flex items-center gap-1.5 mb-1">
              {movimiento.anulado ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-200 px-2 py-0.5 text-xs font-semibold text-slate-700">
                  <Ban className="h-3 w-3" /> Anulado
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                  <CheckCircle2 className="h-3 w-3" /> Vigente
                </span>
              )}
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                  esInversion ? 'bg-indigo-100 text-indigo-800' : 'bg-rose-100 text-rose-800'
                }`}
              >
                {movimiento.tipo_display}
              </span>
            </div>
            <p className="text-xs text-slate-500">Monto total registrado</p>
          </div>

          <div className="text-right">
            <span
              className={`text-2xl font-black tabular-nums ${
                movimiento.anulado
                  ? 'text-slate-400 line-through'
                  : esInversion
                    ? 'text-indigo-900'
                    : 'text-rose-900'
              }`}
            >
              {formatearBs(movimiento.monto)}
            </span>
          </div>
        </div>

        {/* Ficha técnica del movimiento */}
        <div className="rounded-2xl border border-slate-100 bg-slate-50/40 divide-y divide-slate-100 text-sm">
          <div className="p-3.5 flex items-start gap-3">
            <Tag className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <span className="block text-xs font-semibold text-slate-500">Categoría</span>
              <span className="font-medium text-slate-800">{movimiento.categoria_display}</span>
            </div>
          </div>

          <div className="p-3.5 flex items-start gap-3">
            <DollarSign className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <span className="block text-xs font-semibold text-slate-500">Concepto principal</span>
              <p className="font-medium text-slate-900 whitespace-pre-wrap">{movimiento.concepto}</p>
            </div>
          </div>

          {movimiento.descripcion && (
            <div className="p-3.5 flex items-start gap-3">
              <FileText className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <span className="block text-xs font-semibold text-slate-500">Observaciones o detalle</span>
                <p className="text-slate-700 whitespace-pre-wrap text-xs mt-0.5 bg-white p-2.5 rounded-xl border border-slate-200">
                  {movimiento.descripcion}
                </p>
              </div>
            </div>
          )}

          <div className="p-3.5 flex items-start gap-3">
            <Calendar className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <span className="block text-xs font-semibold text-slate-500">Fecha y hora del pago</span>
              <span className="text-slate-800 text-xs font-medium">{fechaFormateada}</span>
            </div>
          </div>

          <div className="p-3.5 flex items-start gap-3">
            <User className="h-4 w-4 text-slate-400 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <span className="block text-xs font-semibold text-slate-500">Registrado por</span>
              <span className="text-slate-800 text-xs font-medium">{movimiento.registrado_por}</span>
            </div>
          </div>
        </div>
      </div>
    </ModalLectura>
  );
};

export default DetalleGastoModal;
