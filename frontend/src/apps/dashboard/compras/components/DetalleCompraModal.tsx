import React, { useEffect, useState } from 'react';
import { AlertCircle, X } from 'lucide-react';
import compraService from '../../../../services/compraService';
import normalizarErrorApi from '../../../../services/erroresApi';
import type { Compra } from '../../../../types/compra';

interface DetalleCompraModalProps {
  idCompra: number;
  onClose: () => void;
}

const formatoFechaHora = new Intl.DateTimeFormat('es-BO', { dateStyle: 'medium', timeStyle: 'short' });

export const DetalleCompraModal: React.FC<DetalleCompraModalProps> = ({ idCompra, onClose }) => {
  const [compra, setCompra] = useState<Compra | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    compraService
      .obtener(idCompra)
      .then((datos) => {
        if (vigente) setCompra(datos);
      })
      .catch((err) => {
        if (vigente) setError(normalizarErrorApi(err).mensaje ?? 'No se pudo cargar la compra.');
      });
    return () => {
      vigente = false;
    };
  }, [idCompra]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-detalle-compra"
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white shadow-xl border border-amber-100"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="titulo-detalle-compra" className="text-base font-bold text-slate-900">
              Compra #{idCompra}
            </h2>
            {compra && (
              <p className="text-xs text-slate-500">
                {compra.proveedor_nombre} · {formatoFechaHora.format(new Date(compra.fecha_hora))} · registrada por{' '}
                {compra.registrado_por}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5">
          {error ? (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          ) : !compra ? (
            <p className="py-8 text-center text-sm text-slate-500">Cargando detalle...</p>
          ) : (
            <>
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Insumo</th>
                    <th className="px-3 py-2 text-right">Cantidad</th>
                    <th className="px-3 py-2 text-right">Precio unit.</th>
                    <th className="px-3 py-2 text-right">Subtotal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {compra.detalles.map((linea) => (
                    <tr key={linea.id_detalle_compra}>
                      <td className="px-3 py-2 font-medium text-slate-800">{linea.nombre_materia_prima}</td>
                      <td className="px-3 py-2 text-right tabular-nums text-slate-600">
                        {linea.cantidad} {linea.unidad_medida}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-slate-600">Bs {linea.precio_unitario}</td>
                      <td className="px-3 py-2 text-right tabular-nums font-semibold text-slate-800">
                        Bs {linea.subtotal}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-4 flex items-center justify-between rounded-xl bg-amber-50 px-4 py-3">
                <span className="text-sm font-semibold text-amber-900">Total</span>
                <span className="text-lg font-bold text-amber-900">Bs {compra.total}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default DetalleCompraModal;
