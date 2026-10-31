import api from '../../../../services/api';
import type { ComprobanteVenta } from '../../../../types/comprobante';
import type {
  DetalleVentaEntrada,
  IntencionStripe,
  RegistrarVentaPayload,
  VentaRegistrada,
  VentaResumen,
} from '../../../../types/venta';

export const ventaService = {
  async registrar(payload: RegistrarVentaPayload): Promise<VentaRegistrada> {
    const respuesta = await api.post<VentaRegistrada>('/ventas/', payload);
    return respuesta.data;
  },

  async crearIntencion(detalles: DetalleVentaEntrada[]): Promise<IntencionStripe> {
    const respuesta = await api.post<IntencionStripe>('/ventas/stripe/intencion/', { detalles });
    return respuesta.data;
  },

  async listarHoy(): Promise<VentaResumen[]> {
    const respuesta = await api.get<VentaResumen[]>('/ventas/');
    return respuesta.data;
  },

  async obtenerConfigStripe(): Promise<{ publishable_key: string }> {
    try {
      const respuesta = await api.get<{ publishable_key: string }>('/ventas/stripe/config/');
      return respuesta.data;
    } catch {
      return { publishable_key: '' };
    }
  },

  async obtenerComprobante(idVenta: number): Promise<ComprobanteVenta> {
    const respuesta = await api.get<ComprobanteVenta>(`/ventas/${idVenta}/comprobante/`);
    return respuesta.data;
  },

  async descargarPdfComprobante(idVenta: number, numeroComprobante: number): Promise<void> {
    const respuesta = await api.get(`/ventas/${idVenta}/comprobante/pdf/`, {
      responseType: 'blob',
    });
    const blob = new Blob([respuesta.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `comprobante_${numeroComprobante}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
