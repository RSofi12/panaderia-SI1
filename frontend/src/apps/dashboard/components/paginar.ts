import { useState } from 'react';

/** Igual al `PAGE_SIZE` de DRF en `backend/config/settings.py`. */
export const TAMANO_PAGINA = 10;

export interface PaginaVisible<T> {
  pagina: number;
  totalPaginas: number;
  total: number;
  /** Índice del primer elemento de la página, base 0. */
  inicio: number;
  /** Índice exclusivo del último elemento visible. */
  fin: number;
  items: T[];
}

/**
 * Recorta un listado ya cargado en el navegador.
 * Los endpoints que devuelven el arreglo completo (productos, compras,
 * pedidos…) se parten aquí. Los que ya vienen paginados del servidor
 * (usuarios, bitácora, historial de precios) no usan esta función:
 * solo el control visual.
 */
export function paginar<T>(items: readonly T[], pagina: number, tamano = TAMANO_PAGINA): PaginaVisible<T> {
  const total = items.length;
  const totalPaginas = Math.max(1, Math.ceil(total / tamano));
  const actual = Math.min(Math.max(1, pagina), totalPaginas);
  const inicio = (actual - 1) * tamano;
  const fin = Math.min(inicio + tamano, total);

  return {
    pagina: actual,
    totalPaginas,
    total,
    inicio,
    fin,
    items: items.slice(inicio, fin),
  };
}

/**
 * Página actual que vuelve a 1 cuando cambia la clave de filtros.
 * La página guardada se ignora si la clave ya no coincide, así la tabla
 * no muestra una página vacía después de buscar o filtrar.
 */
export function usePagina(clave: string) {
  const [estado, setEstado] = useState({ clave, pagina: 1 });
  const pagina = estado.clave === clave ? estado.pagina : 1;

  function setPagina(siguiente: number) {
    setEstado({ clave, pagina: Math.max(1, siguiente) });
  }

  return [pagina, setPagina] as const;
}
