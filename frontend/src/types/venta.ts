export type MetodoPago = 'efectivo' | 'stripe';

export interface DetalleVentaEntrada {
  id_producto: number;
  cantidad: number;
}

export interface DatosTarjetaEntrada {
  numero: string;
  exp_mes: number;
  exp_anio: number;
  cvc: string;
  titular?: string;
}

export interface RegistrarVentaPayload {
  metodo_pago: MetodoPago;
  id_transaccion_stripe?: string | null;
  datos_tarjeta?: DatosTarjetaEntrada | null;
  detalles: DetalleVentaEntrada[];
}

export interface IntencionStripe {
  id_transaccion_stripe: string;
  client_secret: string;
  monto: string;
  moneda: string;
}

export interface DetalleVenta {
  id_detalle_venta: number;
  id_producto: number;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: string;
  subtotal: string;
}

export interface StockResultante {
  id_producto: number;
  nombre: string;
  stock_actual: number;
}

export interface VentaRegistrada {
  id_venta: number;
  numero_comprobante: number;
  fecha_hora: string;
  metodo_pago: MetodoPago;
  id_transaccion_stripe: string | null;
  total: string;
  registrado_por: string;
  detalles: DetalleVenta[];
  stock_resultante: StockResultante[];
}

export interface VentaResumen {
  id_venta: number;
  numero_comprobante: number;
  fecha_hora: string;
  metodo_pago: MetodoPago;
  id_transaccion_stripe: string | null;
  total: string;
  registrado_por: string;
  cantidad_lineas: number;
}
