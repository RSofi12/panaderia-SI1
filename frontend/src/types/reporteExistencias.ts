export type TipoExistencia = 'materia_prima' | 'producto_terminado';
export type EstadoExistencia = 'normal' | 'bajo_stock' | 'sin_inventario';

export interface ReporteExistenciasFiltros {
  tipo: 'todos' | TipoExistencia;
  q: string;
  estado: 'todos' | EstadoExistencia;
}

/** Los decimales conservan las tres posiciones que entrega la API. */
export interface ExistenciaReporte {
  id: number;
  nombre: string;
  tipo: TipoExistencia;
  stock_actual: string | null;
  stock_minimo: string;
  origen_minimo: 'catalogo' | 'referencial_global';
  unidad_medida: string;
  estado: EstadoExistencia;
  activo: boolean;
}

export interface ReporteExistencias {
  umbral_productos_terminados: string;
  resumen: {
    total: number;
    materias_primas: number;
    productos_terminados: number;
    bajo_stock: number;
    sin_inventario: number;
  };
  resultados: ExistenciaReporte[];
}
