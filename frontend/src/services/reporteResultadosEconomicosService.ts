import api from './api';
import type { ReporteResultadosEconomicos } from '../types/reporteResultadosEconomicos';

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

export async function consultarReporteResultadosEconomicos(
  desde: string,
  hasta: string,
): Promise<ReporteResultadosEconomicos> {
  const respuesta = await api.get<ReporteResultadosEconomicos>('/reportes/resultados-economicos/', {
    params: { desde, hasta },
  });
  return respuesta.data;
}

export async function descargarReporteResultadosCsv(
  desde: string,
  hasta: string,
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/resultados-economicos/csv/', {
    params: { desde, hasta },
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `resultados-economicos-${desde}-${hasta}.csv`);
}

export async function descargarReporteResultadosPdf(
  desde: string,
  hasta: string,
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/resultados-economicos/pdf/', {
    params: { desde, hasta },
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `resultados-economicos-${desde}-${hasta}.pdf`);
}
