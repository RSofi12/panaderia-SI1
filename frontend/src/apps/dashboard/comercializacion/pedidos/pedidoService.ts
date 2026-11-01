import api from '../../../../services/api';
import type { IntencionStripe } from '../../../../types/venta';

export interface RegistrarPedidoPayload {
  cliente: { nombre: string; telefono?: string; direccion?: string };
  fecha_entrega: string;
  metodo_pago: 'efectivo' | 'stripe';
  id_transaccion_stripe?: string;
  detalles: { id_producto: number; cantidad: number }[];
}

export interface PedidoRegistrado {
  id_pedido: number;
  cliente: string;
  estado: string;
  total: string;
  metodo_pago?: string;
  id_transaccion_stripe?: string | null;
  numero_comprobante?: number | null;
}

export const pedidoService = {
  async registrar(payload: RegistrarPedidoPayload): Promise<PedidoRegistrado> {
    const respuesta = await api.post<PedidoRegistrado>('/pedidos/', payload);
    return respuesta.data;
  },

  async listarAbiertos(): Promise<PedidoRegistrado[]> {
    const respuesta = await api.get<PedidoRegistrado[]>('/pedidos/');
    return respuesta.data;
  },

  async cambiarEstado(
    idPedido: number,
    estado: string,
    idTransaccionStripe?: string,
  ): Promise<PedidoRegistrado> {
    const cuerpo: { estado: string; id_transaccion_stripe?: string } = { estado };
    if (idTransaccionStripe) {
      cuerpo.id_transaccion_stripe = idTransaccionStripe;
    }
    const respuesta = await api.patch<PedidoRegistrado>(`/pedidos/${idPedido}/`, cuerpo);
    return respuesta.data;
  },

  async crearIntencion(idPedido: number): Promise<IntencionStripe> {
    const respuesta = await api.post<IntencionStripe>(`/pedidos/${idPedido}/stripe/intencion/`);
    return respuesta.data;
  },

  async crearIntencionDeLineas(
    detalles: { id_producto: number; cantidad: number }[],
  ): Promise<IntencionStripe> {
    const respuesta = await api.post<IntencionStripe>('/pedidos/stripe/intencion/', { detalles });
    return respuesta.data;
  },

  async obtenerClavePublicaStripe(): Promise<string> {
    try {
      const respuesta = await api.get<{ publishable_key: string }>('/pedidos/stripe/config/');
      return respuesta.data.publishable_key || '';
    } catch {
      return '';
    }
  },
};
