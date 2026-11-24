import api from './api';
import type {
  AnalisisVozReporte,
  CasoUsoReporte,
  ComandoVozInterpretado,
} from '../types/reporteVoz';

export async function analizarConsultaVoz(
  texto: string,
  cuActual?: CasoUsoReporte,
): Promise<AnalisisVozReporte> {
  const respuesta = await api.post<AnalisisVozReporte>('/reportes/voz/analizar/', {
    texto,
    ...(cuActual ? { cu_actual: cuActual } : {}),
  });
  return respuesta.data;
}

/** Compatibilidad con pruebas o flujos legacy; el asistente usa solo `analizar`. */
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

function guardarBlob(contenido: Blob, nombre: string): void {
  const url = URL.createObjectURL(contenido);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  enlace.rel = 'noopener';
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

type PayloadAnalisisExport = {
  consulta: string;
  tema: string;
  desde: string;
  hasta: string;
  analisis: string;
  motor?: string;
};

export async function descargarAnalisisReportePdf(payload: PayloadAnalisisExport): Promise<void> {
  const respuesta = await api.post<Blob>('/reportes/voz/analizar/pdf/', payload, {
    responseType: 'blob',
  });
  const base = `reporte-${payload.tema}-${payload.desde}-${payload.hasta}.pdf`;
  guardarBlob(respuesta.data, base);
}

export async function descargarAnalisisReporteCsv(payload: PayloadAnalisisExport): Promise<void> {
  const respuesta = await api.post<Blob>('/reportes/voz/analizar/csv/', payload, {
    responseType: 'blob',
  });
  const base = `reporte-${payload.tema}-${payload.desde}-${payload.hasta}.csv`;
  guardarBlob(respuesta.data, base);
}

export async function descargarAnalisisReporteExcel(payload: PayloadAnalisisExport): Promise<void> {
  const respuesta = await api.post<Blob>('/reportes/voz/analizar/excel/', payload, {
    responseType: 'blob',
  });
  const base = `reporte-${payload.tema}-${payload.desde}-${payload.hasta}.xlsx`;
  guardarBlob(respuesta.data, base);
}

export function descargarTextoComoArchivo(
  contenido: string,
  nombreArchivo: string,
  tipoMime = 'text/plain;charset=utf-8',
): void {
  const blob = new Blob(['\uFEFF', contenido], { type: tipoMime });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombreArchivo;
  enlace.rel = 'noopener';
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}