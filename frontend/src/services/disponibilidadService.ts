import api from './api';
import type { ProductoDisponible } from '../types/disponibilidad';

export const disponibilidadService = {
  async listar(filtros: { q?: string; categoria?: string } = {}) {
    const response = await api.get<ProductoDisponible[]>('/disponibilidad/', { params: filtros });
    return response.data;
  },
};
