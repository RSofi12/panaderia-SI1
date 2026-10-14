import api from '../../../../services/api';
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
};

