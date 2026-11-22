import api from './api';

export type PeriodoReporte = 'dia' | 'semana' | 'mes';

export interface ProductoVendido {
  nombre: string;
  cantidad: number;
  subtotal: string;
}

export interface ReporteVentas {
  desde: string;
  hasta: string;
  cantidad: number;
  total: string;
  efectivo: string;
  tarjeta: string;
  productos: ProductoVendido[];
}

export interface CierreReporteVentas extends ReporteVentas {
  id_cierre: number;
  periodo: PeriodoReporte;
  metodo_pago: string | null;
  fecha_generacion: string;
  generado_por: string;
}

function isoFecha(fecha: Date): string {
  const mes = String(fecha.getMonth() + 1).padStart(2, '0');
  const dia = String(fecha.getDate()).padStart(2, '0');
  return `${fecha.getFullYear()}-${mes}-${dia}`;
}

export function fechaHoy(): string {
  return isoFecha(new Date());
}

export function semanaActual(): string {
  const ahora = new Date();
  const jueves = new Date(ahora);
  jueves.setDate(ahora.getDate() + 3 - ((ahora.getDay() + 6) % 7));
  const anio = jueves.getFullYear();
  const inicio = new Date(anio, 0, 4);
  inicio.setDate(inicio.getDate() - ((inicio.getDay() + 6) % 7));
  const semana = 1 + Math.round((jueves.getTime() - inicio.getTime()) / 604800000);
  return `${anio}-W${String(semana).padStart(2, '0')}`;
}

export function mesActual(): string {
  const ahora = new Date();
  return `${ahora.getFullYear()}-${String(ahora.getMonth() + 1).padStart(2, '0')}`;
}

export function rangoDelDia(fecha: string): { desde: string; hasta: string } {
  return { desde: fecha, hasta: fecha };
}

export function rangoDeLaSemana(semanaIso: string): { desde: string; hasta: string } {
  const [anioTexto, semanaTexto] = semanaIso.split('-W');
  const anio = Number(anioTexto);
  const semana = Number(semanaTexto);
  const enero4 = new Date(anio, 0, 4);
  const lunesSemana1 = new Date(enero4);
  lunesSemana1.setDate(enero4.getDate() - ((enero4.getDay() + 6) % 7));
  const lunes = new Date(lunesSemana1);
  lunes.setDate(lunesSemana1.getDate() + (semana - 1) * 7);
  const domingo = new Date(lunes);
  domingo.setDate(lunes.getDate() + 6);
  return { desde: isoFecha(lunes), hasta: isoFecha(domingo) };
}

export function rangoDelMes(mes: string): { desde: string; hasta: string } {
  const [anioTexto, mesTexto] = mes.split('-');
  const ultimo = new Date(Number(anioTexto), Number(mesTexto), 0).getDate();
  const mm = mesTexto.padStart(2, '0');
  const dd = String(ultimo).padStart(2, '0');
  return { desde: `${anioTexto}-${mm}-01`, hasta: `${anioTexto}-${mm}-${dd}` };
}

export function rangoDelPeriodo(
  periodo: PeriodoReporte,
  valor: string,
): { desde: string; hasta: string } {
  if (periodo === 'dia') return rangoDelDia(valor);
  if (periodo === 'semana') return rangoDeLaSemana(valor);
  return rangoDelMes(valor);
}

export async function consultarReporteVentas(
  desde: string,
  hasta: string,
  metodoPago?: string,
): Promise<ReporteVentas> {
  const respuesta = await api.get<ReporteVentas>('/reportes/ventas/', {
    params: {
      desde,
      hasta,
      ...(metodoPago ? { metodo_pago: metodoPago } : {}),
    },
  });
  return respuesta.data;
}

export async function guardarCierreVentas(cierre: {
  desde: string;
  hasta: string;
  periodo: PeriodoReporte;
  metodoPago?: string;
}): Promise<CierreReporteVentas> {
  const respuesta = await api.post<CierreReporteVentas>('/reportes/ventas/cierres/', {
    desde: cierre.desde,
    hasta: cierre.hasta,
    periodo: cierre.periodo,
    ...(cierre.metodoPago ? { metodo_pago: cierre.metodoPago } : {}),
  });
  return respuesta.data;
}

export async function listarCierresVentas(): Promise<CierreReporteVentas[]> {
  const respuesta = await api.get<CierreReporteVentas[]>('/reportes/ventas/cierres/');
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

export async function descargarReporteCsv(desde: string, hasta: string, metodoPago?: string): Promise<void> {
  const respuesta = await api.get<Blob>('/reportes/ventas/csv/', {
    params: {
      desde,
      hasta,
      ...(metodoPago ? { metodo_pago: metodoPago } : {}),
    },
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `reporte-ventas-${desde}-${hasta}.csv`);
}

export async function descargarCierrePdf(idCierre: number): Promise<void> {
  const respuesta = await api.get<Blob>(`/reportes/ventas/cierres/${idCierre}/pdf/`, {
    responseType: 'blob',
  });
  guardarBlob(respuesta.data, `cierre-ventas-${idCierre}.pdf`);
}
