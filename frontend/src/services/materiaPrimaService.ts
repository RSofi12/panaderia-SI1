import api from './api';
import type { AlertaBajoStock } from '../types/materiaPrima';

export const materiaPrimaService = {
  async listarAlertas(signal?: AbortSignal): Promise<AlertaBajoStock[]> {
    const response = await api.get<AlertaBajoStock[]>('/materias-primas/alertas-bajo-stock/', { signal });
    return response.data;
  },
};
