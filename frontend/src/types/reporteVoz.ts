export type CasoUsoReporte = 'CU21' | 'CU22' | 'CU23' | 'CU24' | 'CU25';
export type FormatoReporteVoz = 'pdf' | 'csv' | 'excel' | 'pantalla';
export type AccionReporteVoz = 'consultar' | 'descargar';
export type PeriodoReporteVoz = 'dia' | 'semana' | 'mes' | null;

export interface FiltrosComandoVoz {
  periodo?: PeriodoReporteVoz;
  desde?: string | null;
  hasta?: string | null;
  metodo_pago?: string;
  jornada?: string;
  columnas?: string[] | null;
}

export interface ComandoVozInterpretado {
  caso_uso: CasoUsoReporte;
  formato: FormatoReporteVoz;
  accion: AccionReporteVoz;
  requiere_seleccion_formato: boolean;
  filtros: FiltrosComandoVoz;
  respuesta_voz: string;
  modulo_disponible: boolean;
  motor: 'gemini' | 'local' | string;
}

export interface AnalisisVozReporte {
  consulta: string;
  tema: string;
  caso_uso: CasoUsoReporte;
  desde: string;
  hasta: string;
  analisis: string;
  motor: 'gemini' | 'local' | string;
  exportar_ventas: boolean;
  exportar_produccion: boolean;
  respuesta_voz: string;
  comando: ComandoVozInterpretado;
}

export interface ContextoDescargaAsistente {
  consulta: string;
  desde: string;
  hasta: string;
  metodo: string;
  jornada?: string;
  columnas: string[];
  exportarVentas: boolean;
  exportarProduccion: boolean;
  analisis: string;
  tema: string;
}