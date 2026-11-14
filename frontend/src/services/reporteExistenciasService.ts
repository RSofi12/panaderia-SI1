import api from './api';
import type { ReporteExistencias, ReporteExistenciasFiltros } from '../types/reporteExistencias';

export async function consultarReporteExistencias(
  filtros: ReporteExistenciasFiltros,
  signal?: AbortSignal,
): Promise<ReporteExistencias> {
  const response = await api.get<ReporteExistencias>('/reportes/existencias/', {
    params: { tipo: filtros.tipo, q: filtros.q.trim(), estado: filtros.estado },
    signal,
  });
  return response.data;
}
