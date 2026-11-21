export type PeriodoEconomico = 'dia' | 'semana' | 'mes' | 'personalizado';

export interface DesgloseCategoriaMonto {
  categoria: string;
  total: number | string;
  cantidad: number;
}

export interface EstadoResultadosFila {
  concepto: string;
  monto: number | string;
  tipo: 'ingreso' | 'costo_directo' | 'subtotal' | 'gasto_operativo' | 'inversion' | 'total_neto';
  porcentaje_ingresos: number | string;
}

export interface IngresosReporteEconomico {
  total: number | string;
  efectivo: number | string;
  tarjeta: number | string;
  cantidad_transacciones: number;
}

export interface CostosReporteEconomico {
  compras_materia_prima: number | string;
  cantidad_compras: number;
  mermas_perdidas: number | string;
  unidades_mermas: number;
  total_costos_directos: number | string;
}

export interface GastosOperativosReporte {
  total: number | string;
  cantidad: number;
  desglose: DesgloseCategoriaMonto[];
}

export interface InversionesReporte {
  total: number | string;
  cantidad: number;
  desglose: DesgloseCategoriaMonto[];
}

export interface ResumenFinanciero {
  total_ingresos: number | string;
  total_egresos_operativos: number | string;
  total_egresos_totales: number | string;
  utilidad_bruta: number | string;
  utilidad_operativa: number | string;
  utilidad_neta: number | string;
  margen_bruto_pct: number | string;
  margen_operativo_pct: number | string;
  margen_neto_pct: number | string;
}

export interface ReporteResultadosEconomicos {
  desde: string;
  hasta: string;
  tiene_movimientos: boolean;
  ingresos: IngresosReporteEconomico;
  costos: CostosReporteEconomico;
  gastos_operativos: GastosOperativosReporte;
  inversiones: InversionesReporte;
  resumen_financiero: ResumenFinanciero;
  estado_resultados: EstadoResultadosFila[];
}
