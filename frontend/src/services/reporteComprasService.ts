import api from './api';
import {
  type PeriodoReporte,
  fechaHoy,
  mesActual,
  rangoDelPeriodo,
  semanaActual,
} from './reporteVentasService';

export type { PeriodoReporte };
export { fechaHoy, mesActual, rangoDelPeriodo, semanaActual };

export interface InsumoComprado {
  id_materia_prima?: number;
  nombre: string;
  unidad_medida: string;
  cantidad: string;
  subtotal: string;
}

export interface ProveedorCompras {
  id_proveedor: number;
  nombre: string;
  cantidad_compras: number;
  total: string;
}

export interface ReporteCompras {
  desde: string;
  hasta: string;
  cantidad: number;
  total: string;
  proveedores: ProveedorCompras[];
  insumos: InsumoComprado[];
}

export interface CierreReporteCompras {
  id_cierre: number;
  desde: string;
  hasta: string;
  periodo: PeriodoReporte;
  proveedor: string | null;
  cantidad: number;
  total: string;
  fecha_generacion: string;
  generado_por: string;
  insumos: InsumoComprado[];
}

export async function consultarReporteCompras(
  desde: string,
  hasta: string,
  idProveedor?: number | '',
  idMateriaPrima?: number | '',
): Promise<ReporteCompras> {
  const respuesta = await api.get<ReporteCompras>('/reportes/compras/', {
    params: {
      desde,
      hasta,
      ...(idProveedor ? { id_proveedor: idProveedor } : {}),
      ...(idMateriaPrima ? { id_materia_prima: idMateriaPrima } : {}),
    },
  });
  return respuesta.data;
}

export async function guardarCierreCompras(cierre: {
  desde: string;
  hasta: string;
  periodo: PeriodoReporte;
  id_proveedor?: number | '';
}): Promise<CierreReporteCompras> {
  const respuesta = await api.post<CierreReporteCompras>('/reportes/compras/cierres/', {
    desde: cierre.desde,
    hasta: cierre.hasta,
    periodo: cierre.periodo,
    ...(cierre.id_proveedor ? { id_proveedor: cierre.id_proveedor } : {}),
  });
  return respuesta.data;
}

export async function listarCierresCompras(): Promise<CierreReporteCompras[]> {
  const respuesta = await api.get<CierreReporteCompras[]>('/reportes/compras/cierres/');
  return respuesta.data;
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

function paramsCompras(
  desde: string,
  hasta: string,
  idProveedor?: number | '',
  idMateriaPrima?: number | '',
) {
  return {
    desde,
    hasta,
    ...(idProveedor ? { id_proveedor: idProveedor } : {}),
    ...(idMateriaPrima ? { id_materia_prima: idMateriaPrima } : {}),
  };
}

export async function descargarReporteComprasCsv(
  desde: string,
  hasta: string,
  idProveedor?: number | '',
  idMateriaPrima?: number | '',
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/compras/csv/', {
    params: paramsCompras(desde, hasta, idProveedor, idMateriaPrima),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `reporte-compras-${desde}-${hasta}.csv`);
}

export async function descargarReporteComprasPdf(
  desde: string,
  hasta: string,
  idProveedor?: number | '',
  idMateriaPrima?: number | '',
): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/compras/pdf/', {
    params: paramsCompras(desde, hasta, idProveedor, idMateriaPrima),
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `reporte-compras-${desde}-${hasta}.pdf`);
}

export async function descargarCierreComprasPdf(idCierre: number): Promise<void> {
  const respuesta = await api.get<Blob>(`/reportes/compras/cierres/${idCierre}/pdf/`, {
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `cierre-compras-${idCierre}.pdf`);
}
