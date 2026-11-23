import React, { useEffect, useState } from 'react';
import { AlertCircle, ShoppingBag } from 'lucide-react';
import compraService from '../../../../services/compraService';
import normalizarErrorApi from '../../../../services/erroresApi';
import type { Compra } from '../../../../types/compra';
import ModalLectura from '../../components/ModalLectura';

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
    <ModalLectura
      titulo={`Compra #${idCompra}`}
      subtitulo={
        compra
          ? `${compra.proveedor_nombre} · ${formatoFechaHora.format(new Date(compra.fecha_hora))} · registrada por ${compra.registrado_por}`
          : 'Consulta de adquisición de insumos (CU7)'
      }
      iconoCabecera={
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
          <ShoppingBag className="h-5 w-5" />
        </div>
      }
      onCerrar={onClose}
      ancho="lg"
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
      {error ? (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      ) : !compra ? (
        <p className="py-8 text-center text-sm text-slate-500">Cargando detalle...</p>
      ) : (
        <div className="space-y-4">
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
          <div className="flex items-center justify-between rounded-xl bg-amber-50 px-4 py-3">
            <span className="text-sm font-semibold text-amber-900">Total</span>
            <span className="text-lg font-bold text-amber-900">Bs {compra.total}</span>
          </div>
        </div>
      )}
    </ModalLectura>
  );
};

export default DetalleCompraModal;
