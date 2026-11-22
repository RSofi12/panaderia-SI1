export type EstadoPedido = 'pendiente' | 'en_preparacion' | 'listo' | 'entregado' | 'cancelado';

export interface DetallePedido {
  id_detalle_pedido: number;
  id_producto: number;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: string;
  subtotal: string;
}

export interface Pedido {
  id_pedido: number;
  cliente: string;
  fecha_registro: string;
  fecha_entrega: string | null;
  estado: EstadoPedido;
  metodo_pago: string | null;
  total: string;
  registrado_por: string;
  detalles: DetallePedido[];
}
