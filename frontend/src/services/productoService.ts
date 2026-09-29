import api from './api';
import type {
  CategoriaProducto,
  Producto,
  ProductoFiltros,
  ProductoPayload,
} from '../types/producto';

export const productoService = {
  /** GET /api/categorias-producto/ */
  async listarCategorias(): Promise<CategoriaProducto[]> {
    const response = await api.get<CategoriaProducto[]>('/categorias-producto/');
    return response.data;
  },

  /** GET /api/productos/ con filtros opcionales (CU5) */
  async listar(filtros: ProductoFiltros = {}): Promise<Producto[]> {
    const response = await api.get<Producto[]>('/productos/', { params: filtros });
    return response.data;
  },

  /** POST /api/productos/ */
  async crear(payload: ProductoPayload): Promise<Producto> {
    const response = await api.post<Producto>('/productos/', payload);
    return response.data;
  },

  /** PATCH /api/productos/<id>/ — un cambio de precio de venta queda en el historial */
  async actualizar(id: number, payload: ProductoPayload): Promise<Producto> {
    const response = await api.patch<Producto>(`/productos/${id}/`, payload);
    return response.data;
  },

  /** PATCH /api/productos/<id>/toggle-activo/ */
  async alternarActivo(id: number): Promise<Producto> {
    const response = await api.patch<Producto>(`/productos/${id}/toggle-activo/`);
    return response.data;
  },
};

export default productoService;
