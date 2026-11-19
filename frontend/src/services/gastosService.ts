import api from './api';
import type {
  GastoFiltros,
  MovimientoEconomico,
  MovimientoEconomicoInput,
} from '../types/gasto';

/** Descarta los filtros vacíos: `?tipo=&categoria=` también llegaría al backend. */
function parametrosGasto(filtros: GastoFiltros = {}): GastoFiltros {
  const params: GastoFiltros = {};
  if (filtros.tipo) params.tipo = filtros.tipo;
  if (filtros.categoria) params.categoria = filtros.categoria;
  if (filtros.fecha_desde) params.fecha_desde = filtros.fecha_desde;
  if (filtros.fecha_hasta) params.fecha_hasta = filtros.fecha_hasta;
  if (filtros.anulado) params.anulado = filtros.anulado;
  if (filtros.search?.trim()) params.search = filtros.search.trim();
  return params;
}

export const gastosService = {
  /** GET /api/gastos/ — movimientos vigentes por defecto (CU20) */
  async listar(filtros?: GastoFiltros): Promise<MovimientoEconomico[]> {
    const response = await api.get<MovimientoEconomico[]>('/gastos/', {
      params: parametrosGasto(filtros),
    });
    return response.data;
  },

  /** GET /api/gastos/<id>/ — detalle de un movimiento */
  async obtener(id: number): Promise<MovimientoEconomico> {
    const response = await api.get<MovimientoEconomico>(`/gastos/${id}/`);
    return response.data;
  },

  /** POST /api/gastos/ — registra el egreso y deja bitácora */
  async registrar(payload: MovimientoEconomicoInput): Promise<MovimientoEconomico> {
    const response = await api.post<MovimientoEconomico>('/gastos/', payload);
    return response.data;
  },

  /** POST /api/gastos/<id>/anular/ — marca anulado sin borrar el registro */
  async anular(id: number, motivo?: string): Promise<MovimientoEconomico> {
    const payload = motivo?.trim() ? { motivo: motivo.trim() } : {};
    const response = await api.post<MovimientoEconomico>(`/gastos/${id}/anular/`, payload);
    return response.data;
  },
};

export default gastosService;
