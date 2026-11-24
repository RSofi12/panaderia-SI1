import api from './api';
import type { ReporteExistencias, ReporteExistenciasFiltros } from '../types/reporteExistencias';

function paramsExistencias(filtros: ReporteExistenciasFiltros, columnas?: string[]) {
  return {
    tipo: filtros.tipo,
    q: filtros.q.trim(),
    estado: filtros.estado,
    ...(columnas && columnas.length > 0 ? { columnas: columnas.join(',') } : {}),
  };
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

export async function descargarReporteExistenciasCsv(
  filtros: ReporteExistenciasFiltros,
  columnas?: string[],
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/existencias/csv/', {
    params: paramsExistencias(filtros, columnas),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, 'reporte-existencias.csv');
}

export async function descargarReporteExistenciasExcel(
  filtros: ReporteExistenciasFiltros,
  columnas?: string[],
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/existencias/excel/', {
    params: paramsExistencias(filtros, columnas),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, 'reporte-existencias.xlsx');
}

export async function descargarReporteExistenciasPdf(
  filtros: ReporteExistenciasFiltros,
  columnas?: string[],
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/existencias/pdf/', {
    params: paramsExistencias(filtros, columnas),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, 'reporte-existencias.pdf');
}
