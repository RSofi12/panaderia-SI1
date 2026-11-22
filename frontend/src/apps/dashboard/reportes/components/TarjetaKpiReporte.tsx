import React from 'react';

interface TarjetaKpiReporteProps {
  etiqueta: string;
  valor: React.ReactNode;
  detalle?: React.ReactNode;
}

/**
 * KPI de reportes CU21–CU25: misma caja, misma tipografía y franja ámbar.
 * Sin iconos, rellenos ni bordes de color distintos entre tarjetas.
 */
export const TarjetaKpiReporte: React.FC<TarjetaKpiReporteProps> = ({
  etiqueta,
  valor,
  detalle,
}) => {
  return (
    <article className="flex h-full min-h-[7.25rem] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="h-1.5 bg-amber-600" aria-hidden="true" />
      <div className="flex flex-1 flex-col p-4">
        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">{etiqueta}</p>
        <p className="mt-1.5 text-2xl font-black tabular-nums tracking-tight text-slate-900">{valor}</p>
        {detalle ? (
          <p className="mt-auto pt-1 text-xs font-medium text-slate-500">{detalle}</p>
        ) : null}
      </div>
    </article>
  );
};
