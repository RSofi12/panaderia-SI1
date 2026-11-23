import React from 'react';
import { Loader2 } from 'lucide-react';

type FormatoExportacion = 'csv' | 'excel' | 'pdf';

interface BotonesExportacionTablaProps {
  onCsv?: () => void;
  onExcel?: () => void;
  onPdf?: () => void;
  descargando?: FormatoExportacion | '';
  deshabilitado?: boolean;
}

const claseBoton =
  'inline-flex min-h-11 cursor-pointer items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-2xs transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';

export const BotonesExportacionTabla: React.FC<BotonesExportacionTablaProps> = ({
  onCsv,
  onExcel,
  onPdf,
  descargando = '',
  deshabilitado = false,
}) => {
  const botones: { id: FormatoExportacion; etiqueta: string; onClick?: () => void }[] = [
    { id: 'csv', etiqueta: 'CSV', onClick: onCsv },
    { id: 'excel', etiqueta: 'Excel', onClick: onExcel },
    { id: 'pdf', etiqueta: 'PDF', onClick: onPdf },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2">
      {botones.map((boton) =>
        boton.onClick ? (
          <button
            key={boton.id}
            type="button"
            disabled={deshabilitado || Boolean(descargando)}
            onClick={boton.onClick}
            className={claseBoton}
          >
            {descargando === boton.id ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            ) : null}
            {boton.etiqueta}
          </button>
        ) : null,
      )}
    </div>
  );
};
