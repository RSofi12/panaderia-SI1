import React, { useEffect } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmarDescarteDialogProps {
  abierto: boolean;
  onContinuar: () => void;
  onDescartar: () => void;
  titulo?: string;
  mensaje?: string;
}

/**
 * Diálogo de confirmación para prevenir pérdida accidental de datos en formularios.
 * Se presenta sobre el modal activo con foco en "Continuar editando".
 */
export const ConfirmarDescarteDialog: React.FC<ConfirmarDescarteDialogProps> = ({
  abierto,
  onContinuar,
  onDescartar,
  titulo = '¿Descartar cambios sin guardar?',
  mensaje = 'Has ingresado información en este formulario. Si sales ahora, todos los cambios se perderán.',
}) => {
  useEffect(() => {
    if (!abierto) return;
    const manejarTeclado = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onContinuar();
      }
    };
    window.addEventListener('keydown', manejarTeclado, true);
    return () => window.removeEventListener('keydown', manejarTeclado, true);
  }, [abierto, onContinuar]);

  if (!abierto) return null;

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="titulo-descarte"
      className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs transition-opacity duration-200 animate-in fade-in"
      onClick={(e) => {
        // Clic fuera del diálogo de confirmación equivale a "Continuar editando"
        if (e.target === e.currentTarget) onContinuar();
      }}
    >
      <div className="w-full max-w-sm overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl transition-all duration-200 animate-in zoom-in-95">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600 ring-8 ring-amber-50/50">
          <AlertTriangle className="h-6 w-6 stroke-[2.2]" />
        </div>

        <h3 id="titulo-descarte" className="text-base font-bold text-slate-900">
          {titulo}
        </h3>

        <p className="mt-2 text-xs leading-relaxed text-slate-600">
          {mensaje}
        </p>

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onContinuar}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 transition-colors hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-amber-500/20 sm:w-auto cursor-pointer"
          >
            Continuar editando
          </button>
          <button
            type="button"
            onClick={onDescartar}
            className="w-full rounded-xl bg-rose-600 px-4 py-2.5 text-xs font-semibold text-white shadow-xs transition-colors hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-500/30 sm:w-auto cursor-pointer"
          >
            Descartar y salir
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmarDescarteDialog;
