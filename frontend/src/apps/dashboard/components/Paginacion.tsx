interface PaginacionProps {
  pagina: number;
  totalPaginas: number;
  onCambiar: (pagina: number) => void;
  deshabilitado?: boolean;
  etiqueta?: string;
}

const claseBoton =
  'inline-flex min-h-11 min-w-[6.75rem] items-center justify-center rounded-lg border border-slate-200 bg-white px-4 text-sm font-medium text-slate-800 transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-600 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:text-slate-400 disabled:hover:bg-white cursor-pointer';

/**
 * Control de página: [ Anterior ]  Página n de m  [ Siguiente ].
 * Se muestra también cuando solo hay una página, con ambos botones inactivos.
 */
export function Paginacion({
  pagina,
  totalPaginas,
  onCambiar,
  deshabilitado = false,
  etiqueta = 'Paginación del listado',
}: PaginacionProps) {
  const total = Math.max(1, totalPaginas);
  const actual = Math.min(Math.max(1, pagina), total);

  return (
    <nav aria-label={etiqueta} className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 px-4 py-3">
      <button
        type="button"
        onClick={() => onCambiar(actual - 1)}
        disabled={deshabilitado || actual <= 1}
        className={claseBoton}
      >
        Anterior
      </button>
      <p className="min-w-[8.5rem] text-center text-sm font-semibold text-slate-900">
        Página {actual} de {total}
      </p>
      <button
        type="button"
        onClick={() => onCambiar(actual + 1)}
        disabled={deshabilitado || actual >= total}
        className={claseBoton}
      >
        Siguiente
      </button>
    </nav>
  );
}
