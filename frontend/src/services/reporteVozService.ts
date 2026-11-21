import api from './api';
import type { CasoUsoReporte, ComandoVozInterpretado } from '../types/reporteVoz';

export async function interpretarComandoVoz(
  texto: string,
  cuActual?: CasoUsoReporte,
): Promise<ComandoVozInterpretado> {
  const respuesta = await api.post<ComandoVozInterpretado>('/reportes/voz/interpretar/', {
    texto,
    ...(cuActual ? { cu_actual: cuActual } : {}),
  });
  return respuesta.data;
}