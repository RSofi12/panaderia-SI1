import api from './api';
import type {
  MateriaPrimaFiltros,
  MateriaPrimaPayload,
  MateriaPrimaStock,
} from '../types/inventario';

export const inventarioService = {
  /** GET /api/inventario/materias-primas/ — Stock de materia prima (CU8) */
  async listarStock(filtros: MateriaPrimaFiltros = {}): Promise<MateriaPrimaStock[]> {
    const response = await api.get<MateriaPrimaStock[]>('/inventario/materias-primas/', {
      params: filtros,
    });
    return response.data;
  },

  /** POST /api/materias-primas/ — Crea el insumo con stock inicial cero (CU8). */
  async crear(payload: MateriaPrimaPayload): Promise<void> {
    await api.post('/materias-primas/', payload);
  },

  /** PATCH /api/materias-primas/<id>/ — Actualiza el catálogo del insumo (CU8). */
  async actualizar(id: number, payload: MateriaPrimaPayload): Promise<void> {
    await api.patch(`/materias-primas/${id}/`, payload);
  },

  /** PATCH /api/materias-primas/<id>/toggle-activo/ — Baja lógica o reactivación (CU8). */
  async alternarActivo(id: number): Promise<void> {
    await api.patch(`/materias-primas/${id}/toggle-activo/`);
  },
};

export default inventarioService;
