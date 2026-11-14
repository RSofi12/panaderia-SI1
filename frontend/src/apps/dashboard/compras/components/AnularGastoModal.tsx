import React, { useEffect, useRef, useState } from 'react';
import { Ban, Loader2 } from 'lucide-react';
import { formatearBs } from '../../productos/precios';
import type { MovimientoEconomico } from '../../../../types/gasto';

interface Props {
  movimiento: MovimientoEconomico;
  ocupado: boolean;
  onCancelar: () => void;
  onConfirmar: (motivo?: string) => void;
}

/**
 * Confirmación de anulación. Es un `alertdialog`: la acción es reversible solo
 * por decisión humana (el registro queda en el historial), así que el foco
 * inicial va en "Cancelar" y no en el botón destructivo.
 */
export const AnularGastoModal: React.FC<Props> = ({ movimiento, ocupado, onCancelar, onConfirmar }) => {
  const [motivo, setMotivo] = useState('');
  const cancelarRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelarRef.current?.focus();
  }, []);

  useEffect(() => {
    function alPresionar(evento: KeyboardEvent) {
      if (evento.key === 'Escape' && !ocupado) onCancelar();
    }
    document.addEventListener('keydown', alPresionar);
    const overflowPrevio = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', alPresionar);
      document.body.style.overflow = overflowPrevio;
    };
  }, [ocupado, onCancelar]);

  const manejarConfirmacion = () => {
    onConfirmar(motivo.trim() || undefined);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget && !ocupado) onCancelar();
      }}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="titulo-anular-gasto"
        aria-describedby="detalle-anular-gasto"
        className="mostrador-aparecer w-full max-w-md overflow-hidden rounded-2xl border border-amber-100 bg-white shadow-xl"
      >
        <div className="flex items-start gap-4 px-5 py-5">
          <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600">
            <Ban className="h-5 w-5" />
          </span>
          <div className="flex-1">
            <h2 id="titulo-anular-gasto" className="text-base font-bold text-slate-900">
              ¿Anular este movimiento?
            </h2>
            <p id="detalle-anular-gasto" className="mt-1 text-sm text-slate-600">
              <span className="font-semibold text-slate-800">{movimiento.concepto}</span> por{' '}
              <span className="font-semibold tabular-nums text-slate-800">{formatearBs(movimiento.monto)}</span>.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Dejará de contar en los reportes, pero seguirá visible en el historial y en la bitácora.
              No se puede revertir desde la aplicación.
            </p>

            <div className="mt-4">
              <label htmlFor="motivo-anulacion" className="block text-xs font-semibold text-slate-700 mb-1">
                Motivo o justificación (opcional)
              </label>
              <textarea
                id="motivo-anulacion"
                rows={2}
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                disabled={ocupado}
                placeholder="Ej: Factura duplicada, error en el monto..."
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
              />
            </div>
          </div>
        </div>
        <footer className="flex flex-col-reverse gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3 sm:flex-row sm:justify-end">
          <button
            ref={cancelarRef}
            type="button"
            onClick={onCancelar}
            disabled={ocupado}
            className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={manejarConfirmacion}
            disabled={ocupado}
            aria-busy={ocupado}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {ocupado && <Loader2 className="h-4 w-4 animate-spin" />}
            {ocupado ? 'Anulando…' : 'Anular movimiento'}
          </button>
        </footer>
      </div>
    </div>
  );
};

export default AnularGastoModal;
