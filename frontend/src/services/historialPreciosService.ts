import api from './api';
import type { HistorialPrecioFiltros, HistorialPrecioPagina } from '../types/historialPrecio';

export const historialPreciosService = {
  /** Consulta de solo lectura; Axios comparte los interceptores JWT del proyecto. */
  async listar(
    filtros: HistorialPrecioFiltros = {},
    pagina = 1,
    signal?: AbortSignal,
  ): Promise<HistorialPrecioPagina> {
    const response = await api.get<HistorialPrecioPagina>('/productos/historial-precios/', {
      params: { ...filtros, page: pagina },
      signal,
    });
    return response.data;
  },
};

export default historialPreciosService;
