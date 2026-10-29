import api from '../../../../services/api';

export interface RegistrarPedidoPayload {
  cliente: { nombre: string; telefono?: string; direccion?: string };
  fecha_entrega: string;
  metodo_pago: 'efectivo' | 'stripe';
  detalles: { id_producto: number; cantidad: number }[];
}

export interface PedidoRegistrado {
  id_pedido: number;
  cliente: string;
  estado: string;
  total: string;
  metodo_pago?: string;
  numero_comprobante?: number | null;
}

export interface DatosTarjetaEntrega {
  numero: string;
  exp_mes: number;
  exp_anio: number;
  cvc: string;
  titular?: string;
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
    datosTarjeta?: DatosTarjetaEntrega,
  ): Promise<PedidoRegistrado> {
    const cuerpo: { estado: string; datos_tarjeta?: DatosTarjetaEntrega } = { estado };
    if (datosTarjeta) {
      cuerpo.datos_tarjeta = datosTarjeta;
    }
    const respuesta = await api.patch<PedidoRegistrado>(`/pedidos/${idPedido}/`, cuerpo);
    return respuesta.data;
  },
};
