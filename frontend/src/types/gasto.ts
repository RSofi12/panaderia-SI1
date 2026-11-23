// Los DecimalField de DRF llegan como string ("350.00") para no perder precisión.

// ---------- Salida: lo que devuelve Django ----------

export type TipoMovimiento = 'gasto' | 'inversion';
export type CategoriaMovimiento = 'alquiler' | 'servicios' | 'mantenimiento' | 'equipos' | 'otros';

export interface MovimientoEconomico {
  id_movimiento: number;
  tipo: TipoMovimiento;
  tipo_display: string;
  categoria: CategoriaMovimiento;
  categoria_display: string;
  concepto: string;
  descripcion: string | null;
  monto: string;
  fecha_hora: string;
  anulado: boolean;
  id_usuario: number;
  registrado_por: string;
}

// ---------- Entrada: lo que el formulario manda en el POST ----------

export interface MovimientoEconomicoInput {
  tipo: TipoMovimiento;
  categoria?: CategoriaMovimiento;
  concepto: string;
  monto: string;
  descripcion?: string;
  /** Fecha local del pago (AAAA-MM-DDTHH:mm). El backend rechaza fechas futuras. */
  fecha_hora?: string;
}

// ---------- Filtros del listado ----------

export interface GastoFiltros {
  tipo?: TipoMovimiento | '';
  categoria?: CategoriaMovimiento | '';
  fecha_desde?: string;
  fecha_hasta?: string;
  /** Solo se envía cuando se quieren ver también los anulados. */
  anulado?: 'todos';
  search?: string;
}

// ---------- Catálogos para los <select> ----------

export interface OpcionTipo {
  valor: TipoMovimiento;
  etiqueta: string;
  descripcion: string;
}

export const TIPOS_MOVIMIENTO: readonly OpcionTipo[] = [
  { valor: 'gasto', etiqueta: 'Gasto operativo', descripcion: 'Alquiler, servicios, mantenimiento' },
  { valor: 'inversion', etiqueta: 'Inversión', descripcion: 'Equipos y mejoras del negocio' },
];

export const CATEGORIAS_MOVIMIENTO: readonly { valor: CategoriaMovimiento; etiqueta: string }[] = [
  { valor: 'alquiler', etiqueta: 'Alquiler' },
  { valor: 'servicios', etiqueta: 'Servicios básicos' },
  { valor: 'mantenimiento', etiqueta: 'Mantenimiento' },
  { valor: 'equipos', etiqueta: 'Equipos y herramientas' },
  { valor: 'otros', etiqueta: 'Otros' },
];
