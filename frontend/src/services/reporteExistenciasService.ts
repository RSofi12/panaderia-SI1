import api from './api';
import type { ReporteExistencias, ReporteExistenciasFiltros } from '../types/reporteExistencias';

function paramsExistencias(filtros: ReporteExistenciasFiltros) {
  return { tipo: filtros.tipo, q: filtros.q.trim(), estado: filtros.estado };
}

function guardarBlob(contenido: Blob, nombre: string) {
  const url = URL.createObjectURL(contenido);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

export async function consultarReporteExistencias(
  filtros: ReporteExistenciasFiltros,
  signal?: AbortSignal,
): Promise<ReporteExistencias> {
  const response = await api.get<ReporteExistencias>('/reportes/existencias/', {
    params: paramsExistencias(filtros),
    signal,
  });
  return response.data;
}

export async function descargarReporteExistenciasCsv(filtros: ReporteExistenciasFiltros): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/existencias/csv/', {
    params: paramsExistencias(filtros),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, 'reporte-existencias.csv');
}

export async function descargarReporteExistenciasPdf(filtros: ReporteExistenciasFiltros): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/existencias/pdf/', {
    params: paramsExistencias(filtros),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, 'reporte-existencias.pdf');
}
