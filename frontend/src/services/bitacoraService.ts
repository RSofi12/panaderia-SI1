import api from './api';
import type { FiltrosBitacora, OpcionesBitacora, RegistroBitacora } from '../types/bitacora';
import type { Paginado } from '../types/usuarios';

export const bitacoraService = {
  /** GET /api/bitacora/ — paginado, del registro más reciente al más antiguo (CU26). */
  async listar(filtros: FiltrosBitacora = {}): Promise<Paginado<RegistroBitacora>> {
    const response = await api.get<Paginado<RegistroBitacora>>('/bitacora/', { params: filtros });
    return response.data;
  },

  /** GET /api/bitacora/opciones/ — acciones, módulos y usuarios para los filtros. */
  async opciones(): Promise<OpcionesBitacora> {
    const response = await api.get<OpcionesBitacora>('/bitacora/opciones/');
    return response.data;
  },
};

export default bitacoraService;
