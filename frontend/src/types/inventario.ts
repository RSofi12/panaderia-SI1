export type EstadoStock = 'normal' | 'bajo_minimo' | 'agotado';

export interface MateriaPrimaStock {
  id_materia_prima: number;
  nombre: string;
  unidad_medida: string;
  // El backend envía los decimales como texto (ej. "18.400")
  stock_actual: string;
  stock_minimo: string;
  estado: EstadoStock;
  activo: boolean;
}

export interface MateriaPrimaFiltros {
  nombre?: string;
  bajo_minimo?: boolean;
  activo?: boolean | 'all';
}

export interface MateriaPrimaPayload {
  nombre: string;
  unidad_medida: string;
  stock_minimo: string;
}
