export type CasoUsoReporte = 'CU21' | 'CU22' | 'CU23' | 'CU24' | 'CU25';
export type FormatoReporteVoz = 'pdf' | 'csv' | 'excel' | 'pantalla';
export type AccionReporteVoz = 'consultar' | 'descargar';
export type PeriodoReporteVoz = 'dia' | 'semana' | 'mes' | null;

export interface FiltrosComandoVoz {
  periodo?: PeriodoReporteVoz;
  desde?: string | null;
  hasta?: string | null;
  metodo_pago?: string;
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

export interface PendienteDescargaVoz {
  desde: string;
  hasta: string;
  metodo: string;
  columnas: string[];
}