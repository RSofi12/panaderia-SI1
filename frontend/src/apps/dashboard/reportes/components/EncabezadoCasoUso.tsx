import React from 'react';

interface EncabezadoCasoUsoProps {
  cu: string;
  titulo: string;
  descripcion?: string;
}

/** Etiqueta + título unificados para CU21–CU25 y CU27 (misma tipografía). */
export const EncabezadoCasoUso: React.FC<EncabezadoCasoUsoProps> = ({ cu, titulo, descripcion }) => {
  return (
    <div>
      <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider text-amber-900">
        {cu}
      </span>
      <h2 className="mt-1.5 text-xl font-bold tracking-tight text-slate-900">{titulo}</h2>
      {descripcion ? <p className="mt-1 text-sm text-slate-500">{descripcion}</p> : null}
    </div>
  );
};
