import type { MetodoPago } from './venta';

export interface ComprobanteEmpresa {
  nombre: string;
  propietario: string;
  actividad: string;
  direccion: string;
  telefono: string;
  mensaje_pie: string;
}

export interface ComprobanteDetalleItem {
  id_detalle_venta: number;
  id_producto: number;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: string;
  subtotal: string;
}

export interface ComprobanteVenta {
  id_venta: number;
  numero_comprobante: number;
  fecha_hora: string;
  metodo_pago: MetodoPago;
  id_transaccion_stripe: string | null;
  total: string;
  cajero: string;
  total_articulos: number;
  empresa: ComprobanteEmpresa;
  detalles: ComprobanteDetalleItem[];
}

