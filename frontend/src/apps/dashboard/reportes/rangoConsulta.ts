import { semanaIsoDesdeFecha, type PeriodoReporte } from '../../../services/reporteVentasService';

export interface RangoConsultaReportes {
  desde: string;
  hasta: string;
  version: number;
}

/** Traduce un DESDE/HASTA a los selectores Día / Semana / Mes de cada CU. */
export function inferirSelectoresPeriodo(desde: string, hasta: string): {
  periodo: PeriodoReporte;
  dia: string;
  semana: string;
  mes: string;
} {
  const dia = desde;
  const semana = semanaIsoDesdeFecha(desde);
  const mes = desde.slice(0, 7);
  if (desde === hasta) {
    return { periodo: 'dia', dia, semana, mes };
  }
  if (desde.endsWith('-01') && hasta.slice(0, 7) === desde.slice(0, 7)) {
    return { periodo: 'mes', dia, semana, mes };
  }
  return { periodo: 'semana', dia, semana, mes };
}

export const ANCLAS_REPORTES = [
  { id: 'ventas', etiqueta: 'CU21 Ventas' },
  { id: 'produccion', etiqueta: 'CU22 Producción' },
  { id: 'existencias', etiqueta: 'CU23 Existencias' },
  { id: 'compras', etiqueta: 'CU24 Compras' },
  { id: 'resultados', etiqueta: 'CU25 Resultados' },
] as const;
