import React from 'react';
import { Power } from 'lucide-react';
import type { Proveedor } from '../../../../types/proveedor';

interface ConfirmarEstadoProveedorDialogProps {
  proveedor: Proveedor;
  procesando: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export const ConfirmarEstadoProveedorDialog: React.FC<ConfirmarEstadoProveedorDialogProps> = ({
  proveedor,
  procesando,
  onCancel,
  onConfirm,
}) => {
  const inactivar = proveedor.activo;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="titulo-estado-proveedor"
        className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl border border-slate-200"
      >
        <div
          className={`mb-4 flex w-11 h-11 items-center justify-center rounded-full ${
            inactivar ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'
          }`}
        >
          <Power className="w-5 h-5" />
        </div>
        <h2 id="titulo-estado-proveedor" className="text-base font-bold text-slate-900">
          {inactivar ? `¿Inactivar ${proveedor.nombre}?` : `¿Activar ${proveedor.nombre}?`}
        </h2>
        <p className="mt-1.5 text-sm text-slate-600">
          {inactivar
            ? 'No aparecerá al registrar nuevas compras. Sus datos y las compras anteriores se conservan.'
            : 'Volverá a estar disponible para registrar compras.'}
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={procesando}
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-70 cursor-pointer ${
              inactivar ? 'bg-red-600 hover:bg-red-700' : 'bg-emerald-600 hover:bg-emerald-700'
            }`}
          >
            {procesando ? 'Procesando...' : inactivar ? 'Inactivar' : 'Activar'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmarEstadoProveedorDialog;
