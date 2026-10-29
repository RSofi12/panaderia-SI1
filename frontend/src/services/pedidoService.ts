import api from './api';
import type { EstadoPedido, Pedido } from '../types/pedido';

export const pedidoService = {
  async listar(filtros: { estado?: EstadoPedido | ''; q?: string; fecha_entrega?: string } = {}) {
    const response = await api.get<Pedido[]>('/pedidos/estado/', { params: filtros });
    return response.data;
  },

  async obtener(idPedido: number) {
    const response = await api.get<Pedido>(`/pedidos/estado/${idPedido}/`);
    return response.data;
  },
};
