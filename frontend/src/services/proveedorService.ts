import api from './api';
import type { Proveedor, ProveedorFiltros, ProveedorPayload } from '../types/proveedor';

export const proveedorService = {
  /** GET /api/proveedores/ con filtros opcionales (CU6) */
  async listar(filtros: ProveedorFiltros = {}): Promise<Proveedor[]> {
    const response = await api.get<Proveedor[]>('/proveedores/', { params: filtros });
    return response.data;
  },

  /** POST /api/proveedores/ */
  async crear(payload: ProveedorPayload): Promise<Proveedor> {
    const response = await api.post<Proveedor>('/proveedores/', payload);
    return response.data;
  },

  /** PATCH /api/proveedores/<id>/ */
  async actualizar(id: number, payload: ProveedorPayload): Promise<Proveedor> {
    const response = await api.patch<Proveedor>(`/proveedores/${id}/`, payload);
    return response.data;
  },

  /** PATCH /api/proveedores/<id>/toggle-activo/ */
  async alternarActivo(id: number): Promise<Proveedor> {
    const response = await api.patch<Proveedor>(`/proveedores/${id}/toggle-activo/`);
    return response.data;
  },
};

export default proveedorService;
