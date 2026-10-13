import React from 'react';
import { Power } from 'lucide-react';
import type { MateriaPrimaStock } from '../../../../../types/inventario';

interface ConfirmarEstadoMateriaDialogProps {
  materia: MateriaPrimaStock;
  procesando: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

export const ConfirmarEstadoMateriaDialog: React.FC<ConfirmarEstadoMateriaDialogProps> = ({
  materia,
  procesando,
  onCancel,
  onConfirm,
}) => {
  const inactivar = materia.activo;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="titulo-estado-mp"
        className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl border border-slate-200"
      >
        <div
          className={`mb-4 flex w-11 h-11 items-center justify-center rounded-full ${
            inactivar ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'
          }`}
        >
          <Power className="w-5 h-5" />
        </div>
        <h2 id="titulo-estado-mp" className="text-base font-bold text-slate-900">
          {inactivar ? `¿Inactivar ${materia.nombre}?` : `¿Activar ${materia.nombre}?`}
        </h2>
        <p className="mt-1.5 text-sm text-slate-600">
          {inactivar
            ? 'Dejará de estar disponible para nuevas compras y recetas de producción. El registro de inventario y su historial de precios se conservan.'
            : 'Volverá a estar disponible para el registro de compras y el cálculo de insumos de producción.'}
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={procesando}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer disabled:opacity-50"
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

export default ConfirmarEstadoMateriaDialog;
