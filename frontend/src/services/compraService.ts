import api from './api';
import type {
  Compra,
  CompraFiltros,
  CompraPayload,
  CompraResumen,
  MateriaPrima,
} from '../types/compra';

export interface MateriaPrimaFiltros {
  nombre?: string;
  activo?: 'true' | 'false';
}

export const compraService = {
  /** GET /api/compras/ — listado de compras registradas (CU7) */
  async listar(filtros?: CompraFiltros): Promise<CompraResumen[]> {
    const response = await api.get<CompraResumen[]>('/compras/', { params: filtros });
    return response.data;
  },

  /** GET /api/compras/<id>/ — cabecera con sus líneas */
  async obtener(id: number): Promise<Compra> {
    const response = await api.get<Compra>(`/compras/${id}/`);
    return response.data;
  },

  /** POST /api/compras/ — registra la compra, suma stock y deja bitácora */
  async registrar(payload: CompraPayload): Promise<Compra> {
    const response = await api.post<Compra>('/compras/', payload);
    return response.data;
  },

  /** GET /api/materias-primas/ — catálogo de insumos para el formulario */
  async listarMateriasPrimas(filtros: MateriaPrimaFiltros = {}): Promise<MateriaPrima[]> {
    const response = await api.get<MateriaPrima[]>('/materias-primas/', { params: filtros });
    return response.data;
  },
};

export default compraService;
