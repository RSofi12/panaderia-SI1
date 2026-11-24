import api from './api';
import type { ReporteProduccion } from '../types/reporteProduccion';

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

export async function consultarReporteProduccion(
  desde: string,
  hasta: string,
  jornada?: string,
): Promise<ReporteProduccion> {
  const respuesta = await api.get<ReporteProduccion>('/reportes/produccion/', {
    params: {
      desde,
      hasta,
      ...(jornada ? { jornada } : {}),
    },
  });
  return respuesta.data;
}

export async function descargarReporteProduccionCsv(
  desde: string,
  hasta: string,
  jornada?: string,
  columnas?: string[],
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/produccion/csv/', {
    params: {
      desde,
      hasta,
      ...(jornada ? { jornada } : {}),
      ...(columnas && columnas.length > 0 ? { columnas: columnas.join(',') } : {}),
    },
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `reporte-produccion-${desde}-${hasta}.csv`);
}

export async function descargarReporteProduccionExcel(
  desde: string,
  hasta: string,
  jornada?: string,
  columnas?: string[],
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/produccion/excel/', {
    params: {
      desde,
      hasta,
      ...(jornada ? { jornada } : {}),
      ...(columnas && columnas.length > 0 ? { columnas: columnas.join(',') } : {}),
    },
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `reporte-produccion-${desde}-${hasta}.xlsx`);
}

export async function descargarReporteProduccionPdf(
  desde: string,
  hasta: string,
  jornada?: string,
  columnas?: string[],
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/produccion/pdf/', {
    params: {
      desde,
      hasta,
      ...(jornada ? { jornada } : {}),
      ...(columnas && columnas.length > 0 ? { columnas: columnas.join(',') } : {}),
    },
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `reporte-produccion-${desde}-${hasta}.pdf`);
}
