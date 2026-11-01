import React from 'react';
import type { ComprobanteVenta } from '../../../../types/comprobante';

interface ComprobanteTicketViewProps {
  comprobante: ComprobanteVenta;
  imprimibleId?: string;
}

export const ComprobanteTicketView: React.FC<ComprobanteTicketViewProps> = ({
  comprobante,
  imprimibleId = 'ticket-imprimible-area',
}) => {
  const { empresa, detalles } = comprobante;

  const fechaFormateada = new Date(comprobante.fecha_hora).toLocaleString('es-BO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const metodoPagoNombre = comprobante.metodo_pago === 'stripe' ? 'TARJETA (STRIPE)' : 'EFECTIVO';

  return (
    <div
      id={imprimibleId}
      className="ticket-cu16-container mx-auto w-full max-w-[340px] bg-white p-5 font-mono text-xs text-slate-800 shadow-sm border border-slate-200 rounded-lg print:border-none print:shadow-none print:p-0 print:max-w-none print:w-full print:m-0"
    >
      {/* Encabezado */}
      <div className="text-center space-y-0.5 pb-3 border-b border-dashed border-slate-300">
        <h1 className="text-base font-black uppercase tracking-tight text-slate-900">
          {empresa.nombre}
        </h1>
        <p className="text-[11px] text-slate-600 font-semibold">{empresa.propietario}</p>
        <p className="text-[10px] text-slate-500">{empresa.direccion}</p>
        <p className="text-[10px] text-slate-500">Telf: {empresa.telefono}</p>
      </div>

      {/* Metadatos del Comprobante */}
      <div className="py-2.5 text-[11px] space-y-1 border-b border-dashed border-slate-300">
        <div className="flex justify-between font-bold text-slate-900">
          <span>COMPROBANTE DE VENTA</span>
          <span>#{comprobante.numero_comprobante}</span>
        </div>
        <div className="flex justify-between text-slate-600">
          <span>Fecha y hora:</span>
          <span>{fechaFormateada}</span>
        </div>
        <div className="flex justify-between text-slate-600">
          <span>Atendido por:</span>
          <span className="font-semibold text-slate-800">{comprobante.cajero}</span>
        </div>
        <div className="flex justify-between text-slate-600">
          <span>Forma de pago:</span>
          <span className="font-bold text-slate-800">{metodoPagoNombre}</span>
        </div>
        {comprobante.id_transaccion_stripe ? (
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>Ref. Stripe:</span>
            <span className="truncate max-w-[170px]">{comprobante.id_transaccion_stripe}</span>
          </div>
        ) : null}
      </div>

      {/* Tabla de Artículos */}
      <div className="py-2.5 border-b border-dashed border-slate-300">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="border-b border-slate-200 text-left text-[10px] text-slate-500 uppercase">
              <th className="pb-1 w-10 text-center">Cant.</th>
              <th className="pb-1">Detalle</th>
              <th className="pb-1 text-right w-14">P.Unit</th>
              <th className="pb-1 text-right w-14">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {detalles.map((item) => (
              <tr key={item.id_detalle_venta} className="align-top">
                <td className="py-1 text-center font-bold">{item.cantidad}</td>
                <td className="py-1 pr-1 leading-snug">{item.nombre_producto}</td>
                <td className="py-1 text-right text-slate-600">{Number(item.precio_unitario).toFixed(2)}</td>
                <td className="py-1 text-right font-bold text-slate-900">{Number(item.subtotal).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Totales */}
      <div className="py-2.5 space-y-1.5 border-b border-dashed border-slate-300 text-xs">
        <div className="flex justify-between text-slate-600">
          <span>Total artículos:</span>
          <span className="font-semibold">{comprobante.total_articulos} unid.</span>
        </div>
        <div className="flex justify-between text-sm font-black text-slate-900 pt-1 border-t border-slate-200">
          <span>TOTAL A PAGAR:</span>
          <span className="text-base">Bs {Number(comprobante.total).toFixed(2)}</span>
        </div>
      </div>

      {/* Pie del ticket */}
      <div className="pt-3 text-center space-y-1 text-[10px] text-slate-500">
        <p className="font-bold text-slate-700">{empresa.mensaje_pie}</p>
        <p>Panadería tradicional con el mejor sabor de Santa Cruz.</p>
        <p className="text-[9px] text-slate-400 italic">Documento interno de mostrador</p>
      </div>
    </div>
  );
};
